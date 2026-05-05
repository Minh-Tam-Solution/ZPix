# Test Plan: MPS Benchmark Suite

## Objective
Benchmark AI image generation on Apple Silicon (M4 Pro 24GB) across backends, models, and resolutions.
Results feed into OGA local-server optimization.

## Hardware
- Apple M4 Pro, 24GB unified memory
- macOS 14.0+ (Sonoma)
- No discrete GPU

## Test Matrix

| # | Model | Backend | Resolution | Steps | Dtype | Metric |
|---|-------|---------|-----------|-------|-------|--------|
| 1 | Z-Image-Turbo SDNQ-uint4 | MPS (Diffusers) | 512x512 | 8 | bf16 | time/step, peak mem |
| 2 | Z-Image-Turbo SDNQ-uint4 | MPS (Diffusers) | 768x768 | 8 | bf16 | time/step, peak mem |
| 3 | Z-Image-Turbo SDNQ-uint4 | MPS (Diffusers) | 1024x1024 | 8 | bf16 | time/step, peak mem |
| 4 | Z-Image-Turbo fp16 | MPS (Diffusers) | 512x512 | 8 | fp16 | time/step, peak mem, quality delta |
| 5 | Z-Image-Turbo fp16 | MPS (Diffusers) | 1024x1024 | 8 | fp16 | time/step, peak mem, quality delta |
| 6 | FLUX.2-klein-4B SDNQ-4bit | MPS (Diffusers) | 512x512 | 4 | bf16 | time/step, peak mem |
| 7 | FLUX.2-klein-4B SDNQ-4bit | MPS (Diffusers) | 1024x1024 | 4 | bf16 | time/step, peak mem |
| 8 | FLUX.2-klein-4B fp16 | MPS (Diffusers) | 512x512 | 4 | fp16 | time/step, peak mem |
| 9 | FLUX.2-klein-4B fp16 | MPS (Diffusers) | 1024x1024 | 4 | fp16 | time/step, peak mem |
| 10 | Z-Image-Turbo | MLX (if available) | 1024x1024 | 8 | bf16 | time/step, peak mem |
| 11 | Z-Image-Turbo | sd.cpp (Metal) | 1024x1024 | 8 | q4_0 | time/step, peak mem |

## Methodology

1. Cold start: kill all Python processes, clear MPS cache
2. Generate 3 images per config, report median
3. Measure: `torch.mps.driver_allocated_size()` for peak memory
4. Record step time from Gradio progress bar (already logged by diffusers)
5. Quality: visual inspection + optional CLIP score against cloud-generated reference

## Pass Criteria

- All configs generate valid images without OOM
- Benchmark report completed with all 11 rows
- At least one config achieves <= 10s/step at 512x512

## Output

Results in `docs/04-build/benchmark-results.md`
Recommendation PR for OGA `local-server/server.py`

## Status: Pending (Sprint 002)
