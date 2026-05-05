# Benchmark Results — Apple Silicon (M4 Pro 24GB)

## Test Environment

| Property | Value |
|----------|-------|
| Hardware | Apple M4 Pro, 24GB unified memory |
| OS | macOS 15.x |
| Python | 3.13.11 |
| PyTorch | 2.10.0 |
| Diffusers | b757035df6fe080b56a672c4000e458bb442821a |
| SDNQ | 0.1.6 (Triton unavailable — PyTorch Eager fallback) |
| Test Date | 2026-05-05 |

## Methodology

- **Cold start**: `torch.mps.empty_cache()` + `gc.collect()` + `torch.mps.synchronize()` between configs; pipeline deleted and reloaded.
- **Images per config**: 3
- **Reported metric**: median time/step across 3 images
- **Peak memory**: polled via `torch.mps.driver_allocated_memory()` during generation
- **Seed**: fixed per run (1000, 1001, 1002)
- **Prompt**: "a professional photo of a golden retriever in a sunny park"

## Results

| # | Model | Backend | Resolution | Steps | Dtype | Time/Step (median) | Peak Memory | Status |
|---|-------|---------|-----------|-------|-------|-------------------|-------------|--------|
| 1 | Z-Image Turbo SDNQ | MPS (Diffusers) | 512×512 | 8 | bf16 | 5.87s | 5.07 GB | PASS |
| 2 | Z-Image Turbo SDNQ | MPS (Diffusers) | 768×768 | 8 | bf16 | 13.96s | 8.00 GB | PASS |
| 3 | Z-Image Turbo SDNQ | MPS (Diffusers) | 1024×1024 | 8 | bf16 | 25.00s | 13.95 GB | PASS |
| 4 | Z-Image Turbo | MPS (Diffusers) | 512×512 | 8 | fp16 | 4.70s | 5.10 GB | PASS |
| 5 | Z-Image Turbo | MPS (Diffusers) | 1024×1024 | 8 | fp16 | 19.63s | 14.05 GB | PASS |
| 6 | FLUX.2-klein-4B SDNQ | MPS (Diffusers) | 512×512 | 4 | bf16 | 3.85s | 4.60 GB | PASS |
| 7 | FLUX.2-klein-4B SDNQ | MPS (Diffusers) | 1024×1024 | 4 | bf16 | 14.36s | 8.93 GB | PASS |
| 8 | FLUX.2-klein-4B | MPS (Diffusers) | 512×512 | 4 | fp16 | 4.33s | 4.86 GB | PASS |
| 9 | FLUX.2-klein-4B | MPS (Diffusers) | 1024×1024 | 4 | fp16 | 15.75s | 8.93 GB | PASS |
| 10 | Z-Image Turbo | MLX | 1024×1024 | 8 | bf16 | N/A | N/A | BACKEND_NOT_AVAILABLE |
| 11 | Z-Image Turbo | sd.cpp (Metal) | 1024×1024 | 8 | q4_0 | N/A | N/A | BACKEND_NOT_AVAILABLE |

### Feature Validation

| Feature | Model | Resolution | Result | Notes |
|---------|-------|-----------|--------|-------|
| FLUX.2-klein-4B load + generate | FLUX.2-klein-4B SDNQ | 1024×1024 | **PASS** | step_time=17.26s, peak=8.93GB |
| LoRA hot-swap | FLUX.2-klein-4B + Disney LoRA | 512×512 | **PASS** | Trigger word not present in LoRA metadata; load + generate OK |
| Image-to-image | FLUX.2-klein-4B | 512×512 | **PASS** | step_time=6.59s, peak=5.40GB |

## Analysis

### Memory Management
- **Pattern used**: `enable_model_cpu_offload(device="mps")` per ADR-001
- **Observation**: Peak memory scales roughly quadratically with resolution:
  - 512×512: ~4.6–5.1 GB
  - 768×768: ~8.0 GB
  - 1024×1024: ~8.9–14.1 GB
- **No OOM observed** on 24GB unified memory across all tested configs

### Performance vs Resolution
- Z-Image Turbo: step time increases ~4–5× from 512×512 → 1024×1024
- FLUX.2-klein-4B: step time increases ~3–4× from 512×512 → 1024×1024
- At 512×512, FLUX.2-klein-4B (3.85s/step bf16) is faster than Z-Image Turbo (5.87s/step bf16) despite larger model, because FLUX runs 4 real steps vs Z-Image's 9 real steps

### Dtype Comparison (bf16 vs fp16)
- **Z-Image Turbo**: fp16 slightly faster than bf16 at 512×512 (4.70s vs 5.87s); comparable at 1024×1024 (19.63s vs 25.00s)
- **FLUX.2-klein-4B**: fp16 comparable to bf16 at 512×512 (4.33s vs 3.85s); slightly slower at 1024×1024 (15.75s vs 14.36s)
- **Warning**: fp16 with Z-Image Turbo produces `RuntimeWarning: invalid value encountered in cast` from diffusers image_processor. Images still generate but may have subtle quality differences.

### Backend Availability
- **MLX**: No `diffusers` MLX backend available for these models at time of testing
- **sd.cpp (Metal)**: No prebuilt binary in OGA repo `electron/lib/`

## Recommendations

### For 24GB unified memory (M4 Pro, M3 Max, M2 Ultra)
- **Primary config**: Z-Image Turbo SDNQ bf16 @ 1024×1024 (25s/step, ~14GB peak)
- **Speed priority**: FLUX.2-klein-4B SDNQ bf16 @ 512×512 (3.85s/step, ~4.6GB peak) — best throughput
- **Quality priority**: FLUX.2-klein-4B SDNQ bf16 @ 1024×1024 (14.36s/step, ~8.9GB peak)

### For 16GB unified memory (M4, M3 Pro base, M2 Pro)
- Safe at 512×512 for both models (~4.6–5.1GB peak)
- 768×768 may be tight for Z-Image Turbo (~8GB peak) but should work if no other heavy apps running
- 1024×1024 risky: Z-Image Turbo peaks at ~14GB; may OOM depending on OS memory pressure
- Recommendation: stick to 512×512 or try `enable_sequential_cpu_offload(device="mps")` for 1024×1024 (slower but safer)

### For 8GB unified memory (MacBook Air base)
- Not recommended for diffusers pipelines at 1024×1024
- 512×512 may work with `enable_sequential_cpu_offload(device="mps")` but will be very slow
- Use quantized backends (sd.cpp, MLX) when available

### OGA local-server impact
- See [`oga-recommendations.md`](./oga-recommendations.md) for `server.py` changes
- Key takeaway: `enable_model_cpu_offload(device="mps")` is required; `pipe.to("mps")` OOMs on 24GB

## Raw Data

Full CSV: [`results/benchmark_mps.csv`](../../results/benchmark_mps.csv)

## Acceptance Criteria Coverage

| AC | Status | Evidence |
|----|--------|----------|
| AC-1.1a | ✅ PASS | 11 configs attempted (9 MPS + 2 N/A) |
| AC-1.1b | ✅ PASS | No crash logs; images generated for all 9 MPS configs |
| AC-1.1c | ✅ PASS | Results table includes time/step + peak memory |
| AC-1.1d | ✅ PASS | Recommendation sections for 16GB and 24GB |
| AC-1.2a | ✅ PASS | FLUX load log shows no exceptions |
| AC-1.2b | ✅ PASS | 1024×1024 image produced (Task 2) |
| AC-1.3a | ✅ PASS | LoRA safetensors loaded via script (`load_lora_weights`) |
| AC-1.3b | ⚠️ PARTIAL | Trigger word not present in test LoRA metadata; code path works |
| AC-1.3c | ✅ PASS | Visual diff observed with LoRA applied |
| AC-1.4a | ✅ PASS | Reference image accepted (Task 4) |
| AC-1.4b | ✅ PASS | i2i image produced (Task 4) |
| AC-1.5a | ✅ PASS | `start-mac.sh` locale fix committed |

---

*Generated by ZPix benchmark suite (Sprint 002)*
