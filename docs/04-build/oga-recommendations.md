# OGA Recommendations — Apple Silicon Inference (Sprint 002)

> For: NQH Creative Studio OGA local-server team
> From: ZPix Sprint 002 Benchmark
> Date: 2026-05-05

## Summary

ZPix Sprint 002 benchmarked Apple Silicon MPS inference for two primary models:
- **Z-Image-Turbo** (fast SD-turbo derivative, SDNQ uint4 quantized)
- **FLUX.2-klein-4B** (compact FLUX, SDNQ 4-bit dynamic)

Results feed directly into OGA `local-server/server.py` optimization for macOS endpoints.

## Key Findings

### 1. Optimal torch_dtype
- <!-- FILL: bf16 vs fp16 conclusion -->

### 2. Memory Management Pattern
- **Adopted**: `enable_model_cpu_offload(device="mps")`
- **Rationale**: ADR-001 validated on M4 Pro 24GB. Keeps only one sub-model on GPU at a time.
- **Fallback**: `enable_sequential_cpu_offload(device="mps")` if OOM persists (e.g., 16GB systems at 1024×1024)

### 3. Quantization Matrix

| Model | Windows (CUDA) | macOS (MPS) | Notes |
|-------|---------------|-------------|-------|
| Z-Image-Turbo | SDNQ uint4 (Triton) | SDNQ uint4 (PyTorch Eager fallback) | Same weights, slower matmul |
| FLUX.2-klein-4B | SDNQ 4-bit dynamic | SDNQ 4-bit dynamic (PyTorch Eager) | No Triton = no INT8 matmul |

### 4. Slicing / Tiling Config
- VAE slicing (`enable_vae_slicing`) and attention slicing not required when CPU offload is active
- If using `pipe.to("mps")` directly, slicing is insufficient to prevent OOM on 24GB

### 5. Backend Availability on macOS

| Backend | Status for Z-Image-Turbo | Status for FLUX.2-klein | Recommendation |
|---------|-------------------------|------------------------|----------------|
| Diffusers + MPS | ✅ Working | ✅ Working | Primary |
| MLX | ❌ Not available | ❌ Not available | Monitor `ml-diffusers` project |
| sd.cpp (Metal) | ❌ No binary in OGA repo | ❌ No binary in OGA repo | Bundle `stable-diffusion.cpp` Metal build |

## Recommended server.py Changes

```python
# In OGA local-server/server.py — proposed MPS branch

if torch.backends.mps.is_available():
    pipe.enable_model_cpu_offload(device="mps")
    # Optional: set memory fraction to leave headroom for OS / browser
    torch.mps.set_per_process_memory_fraction(0.85)
else:
    pipe.enable_model_cpu_offload()
```

### Additional Recommendations
1. **Cache models in `~/.cache/huggingface/`** — reuse across ZPix and OGA to avoid double-download
2. **Pre-warm pipeline** on server start — first image is slower due to sub-model transfers
3. **Queue depth = 1 on MPS** — concurrent requests cause memory fragmentation; serialize

## Action Items

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Merge MPS offload pattern into `local-server/server.py` | OGA backend | High |
| 2 | Add `torch.mps.set_per_process_memory_fraction(0.85)` guard | OGA backend | Medium |
| 3 | Document 16GB vs 24GB config presets | OGA docs | Medium |
| 4 | Evaluate sd.cpp Metal backend for 8-16GB Macs | OGA backend | Low |

## Attachments

- [`benchmark-results.md`](./benchmark-results.md) — full data table
- [`results/benchmark_mps.csv`](../../results/benchmark_mps.csv) — raw CSV

---

*Prepared by @coder for CTO review → OGA handoff*
