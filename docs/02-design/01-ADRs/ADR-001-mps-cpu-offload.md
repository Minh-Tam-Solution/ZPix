# ADR-001: Use enable_model_cpu_offload(device="mps") for Apple Silicon

## Status: Accepted (2026-05-04)

## Context

ZPix uses Hugging Face `diffusers` pipelines (ZImagePipeline, Flux2KleinPipeline) for inference.
The original code calls `pipe.enable_model_cpu_offload()` which defaults to CUDA accelerator hooks.
On macOS with Apple Silicon (MPS), three approaches were tested:

1. `pipe.to("mps")` — load entire pipeline to GPU
2. `pipe.enable_model_cpu_offload(device="mps")` — offload sub-models on/off MPS as needed
3. `pipe.to("mps")` + `enable_attention_slicing()` + `enable_vae_slicing()`

## Decision

Use option 2: `pipe.enable_model_cpu_offload(device="mps")`.

## Consequences

### Positive
- Only one sub-model (transformer OR text_encoder OR VAE) resides on GPU at a time
- Peak memory ~14-16GB instead of 20-22GB (option 1) on M4 Pro 24GB
- Stable step time: 14-15s/step across multiple images (no degradation from swap)
- No OOM on 1024x1024 resolution with 9 steps

### Negative
- Slightly slower than option 1 on first image (sub-model transfer overhead ~2s)
- Requires diffusers >= 0.25 for MPS device support in cpu_offload

### Evidence
- Option 1 tested 2026-05-04: OOM on second image (swap 28.91GB), step time degraded 16s → 24s
- Option 2 tested 2026-05-04: 3 images generated, 14.2/14.5/15.1 s/step, no OOM
- Option 3 tested 2026-05-04: OOM persisted (slicing reduces peak per-op but full model still on GPU)

## Applies to

- ZPix `app.py:load_model()` — MPS branch
- OGA `local-server/server.py` — recommendation for Diffusers engine
