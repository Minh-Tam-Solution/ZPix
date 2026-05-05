# Sprint 002: MPS Benchmark + Feature Validation

## Goal
Benchmark Apple Silicon inference and validate remaining ZPix features on MPS.

## Duration: ~3-5 days

## User Stories Covered
- US-1.1 (MPS Benchmark)
- US-1.2 (FLUX.2-klein-4B on MPS)
- US-1.3 (LoRA Hot-Swap on MPS)
- US-1.4 (Image-to-Image on MPS)
- US-1.5 (Locale Fallback)

## Tasks

| # | Task | Story | Owner | Status |
|---|------|-------|-------|--------|
| 1 | Fix locale fallback in `start-mac.sh` (`C` → `en-US`) | US-1.5 | @coder | Pending |
| 2 | Test FLUX.2-klein-4B load + generate on MPS | US-1.2 | @coder | Pending |
| 3 | Test LoRA hot-swap on MPS | US-1.3 | @coder | Pending |
| 4 | Test image-to-image workflow on MPS | US-1.4 | @coder | Pending |
| 5 | Write benchmark script (automate 11 configs from test plan) | US-1.1 | @architect | Pending |
| 6 | Run benchmark suite, collect results | US-1.1 | @tester | Pending |
| 7 | Write benchmark-results.md with recommendations | US-1.1 | @architect | Pending |
| 8 | PR/report findings to OGA local-server | US-1.1 | @architect | Pending |

## Definition of Done
- [ ] All 11 benchmark configs produce valid images
- [ ] FLUX.2-klein-4B, LoRA, and i2i confirmed working on MPS
- [ ] Locale warning resolved
- [ ] `docs/04-build/benchmark-results.md` complete with recommendation
- [ ] Findings communicated to OGA repo

## Dependencies
- HuggingFace model access (FLUX.2-klein-4B download ~8GB)
- A LoRA safetensors file for testing (any public LoRA compatible with Z-Image or FLUX)
- MLX diffusers support (may not exist yet for these models — document if unavailable)
- sd.cpp Metal binary (check OGA `electron/lib/` for bundled version)

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| FLUX.2-klein-4B OOM on 24GB | Blocks US-1.2 | Try `enable_sequential_cpu_offload` or reduce resolution |
| MLX backend unavailable for Z-Image-Turbo | Reduces benchmark to 2 backends | Document as N/A, benchmark MPS vs sd.cpp only |
| sd.cpp doesn't support SDNQ quantized models | Reduces benchmark scope | Use sd.cpp native q4_0/q8_0 quantization instead |
