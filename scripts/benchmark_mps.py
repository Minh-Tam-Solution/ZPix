#!/usr/bin/env python3
"""Benchmark MPS inference for ZPix Sprint 002.

Replicates app.py pipeline load and generation logic for headless
benchmarking on Apple Silicon (MPS). Measures time/step and peak
memory via torch.mps.driver_allocated_size().

Outputs:
    results/benchmark_mps.csv
    Console summary + task verdicts
"""

import csv
import gc
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

import torch
from sdnq import SDNQConfig  # noqa: F401
from diffusers import Flux2KleinPipeline, ZImagePipeline
from PIL import Image

# Ensure we can import source.py modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from source.py.image_model import ImageModel
from source.py.resolutions import parse_resolution

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).parent.parent
MODELS_JSON = APP_DIR / "data" / "curated_models.json"
RESULTS_DIR = APP_DIR / "results"
RESULTS_CSV = RESULTS_DIR / "benchmark_mps.csv"

PROMPT = "a professional photo of a golden retriever in a sunny park"

# Test matrix from tp-001-mps-benchmark.md (configs 1-9)
CONFIGS = [
    {"model_name": "Z-Image Turbo", "res": "512x512", "steps": 8, "dtype_str": "bf16"},
    {"model_name": "Z-Image Turbo", "res": "768x768", "steps": 8, "dtype_str": "bf16"},
    {"model_name": "Z-Image Turbo", "res": "1024x1024", "steps": 8, "dtype_str": "bf16"},
    {"model_name": "Z-Image Turbo", "res": "512x512", "steps": 8, "dtype_str": "fp16"},
    {"model_name": "Z-Image Turbo", "res": "1024x1024", "steps": 8, "dtype_str": "fp16"},
    {"model_name": "FLUX.2 [klein] 4B", "res": "512x512", "steps": 4, "dtype_str": "bf16"},
    {"model_name": "FLUX.2 [klein] 4B", "res": "1024x1024", "steps": 4, "dtype_str": "bf16"},
    {"model_name": "FLUX.2 [klein] 4B", "res": "512x512", "steps": 4, "dtype_str": "fp16"},
    {"model_name": "FLUX.2 [klein] 4B", "res": "1024x1024", "steps": 4, "dtype_str": "fp16"},
]

# Non-diffusers backends (N/A on this system until explicitly enabled)
BACKENDS = [
    {"model_name": "Z-Image Turbo", "backend": "MLX", "res": "1024x1024", "steps": 8, "dtype_str": "bf16", "status": "BACKEND_NOT_AVAILABLE"},
    {"model_name": "Z-Image Turbo", "backend": "sd.cpp (Metal)", "res": "1024x1024", "steps": 8, "dtype_str": "q4_0", "status": "BACKEND_NOT_AVAILABLE"},
]


def get_dtype(dtype_str: str):
    if dtype_str == "bf16":
        return torch.bfloat16
    if dtype_str == "fp16":
        return torch.float16
    raise ValueError(f"Unknown dtype: {dtype_str}")


def load_models() -> list[ImageModel]:
    with open(MODELS_JSON) as f:
        raw = json.load(f)
    return [ImageModel.model_validate(m) for m in raw]


def find_model_by_name(models: list[ImageModel], name: str) -> ImageModel:
    for m in models:
        if m.name == name:
            return m
    raise ValueError(f"Model {name} not found")


def load_pipeline(model: ImageModel, dtype_str: str):
    """Replicate app.py load_model logic."""
    match model.pipeline:
        case "ZImagePipeline":
            pipe_class = ZImagePipeline
        case "Flux2KleinPipeline":
            pipe_class = Flux2KleinPipeline
        case _:
            raise ValueError(f"Unsupported pipeline: {model.pipeline}")

    dtype = get_dtype(dtype_str)
    try:
        pipe = pipe_class.from_pretrained(model.id, torch_dtype=dtype)
    except Exception:
        logger.warning(f"Can't load {model.id}, falling back to {model.backup_id}.")
        if model.backup_id:
            pipe = pipe_class.from_pretrained(model.backup_id, torch_dtype=dtype)
        else:
            raise

    # SDNQ guards are CUDA/XPU only; skip on MPS.
    pipe.vae.to(memory_format=torch.channels_last)

    if torch.backends.mps.is_available():
        pipe.enable_model_cpu_offload(device="mps")
    else:
        pipe.enable_model_cpu_offload()

    return pipe


class MPSMemoryMonitor:
    """Poll torch.mps.driver_allocated_size() in a background thread."""

    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.peak = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self):
        while not self._stop.is_set():
            try:
                if torch.backends.mps.is_available():
                    current = torch.mps.driver_allocated_memory()
                    if current > self.peak:
                        self.peak = current
            except Exception:
                pass
            time.sleep(self.interval)

    def start(self):
        self.peak = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        return self.peak


def generate_image(
    pipe,
    model: ImageModel,
    prompt: str,
    resolution: str,
    steps: int,
    cfg: float,
    seed: int,
    reference_image: Image.Image | None = None,
):
    """Generate one image and return (image, step_time_seconds, total_time_seconds)."""
    width, height = parse_resolution(resolution)
    real_steps = steps + (1 if model.codename == "ZiT" else 0)

    pipe_kwargs = {
        "prompt": prompt,
        "height": height,
        "width": width,
        "num_inference_steps": real_steps,
        "guidance_scale": float(cfg),
        "generator": torch.manual_seed(seed),
    }

    if reference_image is not None:
        if "image-to-image" in model.features:
            pipe_kwargs["image"] = reference_image
        else:
            logger.warning("Model does not support image-to-image; ignoring reference.")

    start = time.perf_counter()
    result = pipe(**pipe_kwargs)
    total_time = time.perf_counter() - start

    image = result.images[0]
    step_time = total_time / max(real_steps, 1)
    return image, step_time, total_time


def cold_start():
    """Clear caches to emulate cold start."""
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.synchronize()
        torch.mps.empty_cache()
    time.sleep(2)


def run_benchmark(models: list[ImageModel]) -> list[dict]:
    results: list[dict] = []

    for cfg in CONFIGS:
        model = find_model_by_name(models, cfg["model_name"])
        logger.info(
            f"Benchmark config: {model.name} {cfg['res']} dtype={cfg['dtype_str']} steps={cfg['steps']}"
        )

        cold_start()

        try:
            pipe = load_pipeline(model, cfg["dtype_str"])
        except Exception as e:
            logger.error(f"Pipeline load failed: {e}")
            results.append({
                "model": model.name,
                "backend": "MPS (Diffusers)",
                "resolution": cfg["res"],
                "steps": cfg["steps"],
                "dtype": cfg["dtype_str"],
                "time_per_step": "FAIL",
                "peak_memory_gb": "FAIL",
                "status": f"LOAD_FAIL: {e}",
            })
            write_csv(results)
            continue

        step_times = []
        peak_memories = []
        status = "PASS"

        for i in range(3):
            seed = 1000 + i
            monitor = MPSMemoryMonitor()
            monitor.start()
            try:
                _, step_time, _ = generate_image(
                    pipe, model, PROMPT, cfg["res"], cfg["steps"], model.default.cfg, seed
                )
                step_times.append(step_time)
            except Exception as e:
                logger.error(f"Generation {i + 1} failed: {e}")
                status = f"GEN_FAIL: {e}"
                break
            finally:
                peak = monitor.stop()
                peak_memories.append(peak)

        if step_times:
            median_step = sorted(step_times)[len(step_times) // 2]
            median_peak = sorted(peak_memories)[len(peak_memories) // 2] if peak_memories else 0
        else:
            median_step = "FAIL"
            median_peak = "FAIL"

        results.append({
            "model": model.name,
            "backend": "MPS (Diffusers)",
            "resolution": cfg["res"],
            "steps": cfg["steps"],
            "dtype": cfg["dtype_str"],
            "time_per_step": median_step,
            "peak_memory_gb": round(median_peak / (1024 ** 3), 2) if isinstance(median_peak, (int, float)) else median_peak,
            "status": status,
        })

        # Incremental save so crash doesn't lose everything
        write_csv(results)

        del pipe
        cold_start()

    # Append N/A backends
    for cfg in BACKENDS:
        results.append({
            "model": cfg["model_name"],
            "backend": cfg["backend"],
            "resolution": cfg["res"],
            "steps": cfg["steps"],
            "dtype": cfg["dtype_str"],
            "time_per_step": "N/A",
            "peak_memory_gb": "N/A",
            "status": cfg["status"],
        })

    return results


def test_flux_klein(models: list[ImageModel]) -> tuple[bool, float | str, float]:
    """Task 2: Validate FLUX.2-klein-4B loads and generates at 1024x1024."""
    logger.info("=== Task 2: FLUX.2-klein-4B smoke test ===")
    model = find_model_by_name(models, "FLUX.2 [klein] 4B")
    cold_start()
    pipe = load_pipeline(model, "bf16")
    prompt = "a cyberpunk cityscape at night, neon lights, high detail"
    monitor = MPSMemoryMonitor()
    monitor.start()
    try:
        _, step_time, total_time = generate_image(pipe, model, prompt, "1024x1024", 4, 1.0, 42)
        peak = monitor.stop()
        logger.info(
            f"FLUX.2-klein-4B 1024x1024: step_time={step_time:.2f}s, total={total_time:.2f}s, peak={peak / (1024 ** 3):.2f}GB"
        )
        return True, step_time, peak
    except Exception as e:
        monitor.stop()
        logger.error(f"FLUX.2-klein-4B failed: {e}")
        return False, str(e), 0.0
    finally:
        del pipe
        cold_start()


def test_lora(models: list[ImageModel]) -> tuple[bool, float | str, float]:
    """Task 3: Test LoRA hot-swap on MPS."""
    logger.info("=== Task 3: LoRA hot-swap test ===")
    model = find_model_by_name(models, "FLUX.2 [klein] 4B")
    cold_start()
    pipe = load_pipeline(model, "bf16")

    lora_dir = APP_DIR / "temp" / "loras"
    lora_dir.mkdir(parents=True, exist_ok=True)
    lora_path = lora_dir / "disney_lora.safetensors"

    if not lora_path.exists():
        logger.info("Downloading Disney LoRA for testing...")
        try:
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id="XLabs-AI/flux-lora-collection",
                filename="disney_lora.safetensors",
                local_dir=str(lora_dir),
                local_dir_use_symlinks=False,
            )
            lora_path = Path(downloaded)
        except Exception as e:
            logger.error(f"LoRA download failed: {e}")
            del pipe
            cold_start()
            return False, f"DOWNLOAD_FAIL: {e}", 0.0

    try:
        from source.py.lora_model import LoraModel

        lora = LoraModel(str(lora_path))
        bfloat16_lora = lora.to_bf16()

        # FLUX .alpha key workaround (app.py line 262-265)
        if isinstance(pipe, Flux2KleinPipeline):
            bfloat16_lora = {k: v for k, v in bfloat16_lora.items() if not k.endswith(".alpha")}

        pipe.unload_lora_weights()
        pipe.load_lora_weights(bfloat16_lora, adapter_name="lora_1")
        trigger = lora.trigger_word()
        logger.info(f"LoRA loaded: {lora_path.name}, trigger word={trigger}")
    except Exception as e:
        logger.error(f"LoRA load failed: {e}")
        del pipe
        cold_start()
        return False, f"LORA_LOAD_FAIL: {e}", 0.0

    prompt = f"{trigger or ''}, a portrait of a woman".strip(", ")
    monitor = MPSMemoryMonitor()
    monitor.start()
    try:
        _, step_time, total_time = generate_image(pipe, model, prompt, "512x512", 4, 1.0, 123)
        peak = monitor.stop()
        logger.info(
            f"LoRA generation: step_time={step_time:.2f}s, total={total_time:.2f}s, peak={peak / (1024 ** 3):.2f}GB"
        )
    except Exception as e:
        monitor.stop()
        logger.error(f"LoRA generation failed: {e}")
        del pipe
        cold_start()
        return False, f"LORA_GEN_FAIL: {e}", 0.0

    del pipe
    cold_start()
    return True, step_time, peak


def test_image_to_image(models: list[ImageModel]) -> tuple[bool, float | str, float]:
    """Task 4: Test image-to-image workflow."""
    logger.info("=== Task 4: Image-to-image test ===")
    model = find_model_by_name(models, "FLUX.2 [klein] 4B")
    cold_start()
    pipe = load_pipeline(model, "bf16")

    ref_prompt = "a serene mountain lake at sunrise"
    try:
        ref_image, _, _ = generate_image(pipe, model, ref_prompt, "512x512", 4, 1.0, 999)
    except Exception as e:
        logger.error(f"Reference image generation failed: {e}")
        del pipe
        cold_start()
        return False, f"REF_GEN_FAIL: {e}", 0.0

    i2i_prompt = "a serene mountain lake at sunrise, oil painting style"
    monitor = MPSMemoryMonitor()
    monitor.start()
    try:
        _, step_time, total_time = generate_image(
            pipe, model, i2i_prompt, "512x512", 4, 1.0, 888, reference_image=ref_image
        )
        peak = monitor.stop()
        logger.info(
            f"i2i generation: step_time={step_time:.2f}s, total={total_time:.2f}s, peak={peak / (1024 ** 3):.2f}GB"
        )
    except Exception as e:
        monitor.stop()
        logger.error(f"i2i generation failed: {e}")
        del pipe
        cold_start()
        return False, f"I2I_FAIL: {e}", 0.0

    del pipe
    cold_start()
    return True, step_time, peak


def write_csv(results: list[dict]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model", "backend", "resolution", "steps", "dtype",
        "time_per_step", "peak_memory_gb", "status",
    ]
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    logger.info(f"Results saved to {RESULTS_CSV}")


def write_console_summary(results: list[dict]):
    print("\n" + "=" * 120)
    print("BENCHMARK SUMMARY — ZPix Sprint 002 (MPS)")
    print("=" * 120)
    header = f"{'#':<3} {'Model':<28} {'Backend':<20} {'Resolution':<10} {'Steps':<6} {'Dtype':<6} {'Time/Step':<12} {'Peak GB':<10} {'Status'}"
    print(header)
    print("-" * 120)
    for i, r in enumerate(results, 1):
        tps = f"{r['time_per_step']:.2f}s" if isinstance(r["time_per_step"], (int, float)) else r["time_per_step"]
        print(
            f"{i:<3} {r['model']:<28} {r['backend']:<20} {r['resolution']:<10} "
            f"{r['steps']:<6} {r['dtype']:<6} {tps:<12} {r['peak_memory_gb']:<10} {r['status']}"
        )
    print("=" * 120)


def main():
    if not torch.backends.mps.is_available():
        logger.error("MPS is not available on this system.")
        sys.exit(1)

    models = load_models()

    # Task 5+6: benchmark suite
    results = run_benchmark(models)

    # Task 2: FLUX.2-klein-4B smoke test
    flux_ok, flux_data, flux_peak = test_flux_klein(models)
    if not flux_ok:
        results.append({
            "model": "FLUX.2 [klein] 4B",
            "backend": "MPS (Diffusers)",
            "resolution": "1024x1024",
            "steps": 4,
            "dtype": "bf16",
            "time_per_step": "FAIL",
            "peak_memory_gb": "FAIL",
            "status": f"FLUX_SMOKE_FAIL: {flux_data}",
        })

    # Task 3: LoRA hot-swap
    lora_ok, lora_data, lora_peak = test_lora(models)
    if not lora_ok:
        results.append({
            "model": "FLUX.2 [klein] 4B + LoRA",
            "backend": "MPS (Diffusers)",
            "resolution": "512x512",
            "steps": 4,
            "dtype": "bf16",
            "time_per_step": "FAIL",
            "peak_memory_gb": "FAIL",
            "status": f"LORA_FAIL: {lora_data}",
        })

    # Task 4: image-to-image
    i2i_ok, i2i_data, i2i_peak = test_image_to_image(models)
    if not i2i_ok:
        results.append({
            "model": "FLUX.2 [klein] 4B i2i",
            "backend": "MPS (Diffusers)",
            "resolution": "512x512",
            "steps": 4,
            "dtype": "bf16",
            "time_per_step": "FAIL",
            "peak_memory_gb": "FAIL",
            "status": f"I2I_FAIL: {i2i_data}",
        })

    write_csv(results)
    write_console_summary(results)

    print("\nTASK VERDICTS:")
    print(f"  Task 1 (Locale fallback): Already committed")
    print(f"  Task 2 (FLUX.2-klein-4B): {'PASS' if flux_ok else 'FAIL'}")
    print(f"  Task 3 (LoRA hot-swap):   {'PASS' if lora_ok else 'FAIL'}")
    print(f"  Task 4 (Image-to-image):  {'PASS' if i2i_ok else 'FAIL'}")
    print(f"\nFull CSV: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
