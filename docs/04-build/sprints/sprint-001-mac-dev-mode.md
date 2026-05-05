# Sprint 001: Mac Dev Mode

## Goal
Enable ZPix to run on macOS Apple Silicon for research/benchmarking purposes.

## Duration: 2026-05-04 (1 day)

## Deliverables

| Item | Status | Commit |
|------|--------|--------|
| `requirements-mac.txt` | Done | 75d069b |
| `start-mac.sh` | Done | 75d069b |
| `app.py` MPS patch (pipe.to → cpu_offload) | Done | uncommitted (pending ADR-001 validation) |
| Smoke test Z-Image-Turbo on M4 Pro 24GB | Done | 3 images, 14-15s/step |

## Test Results

| Test | Result |
|------|--------|
| uv venv + pip install | Pass — 36 packages, no conflict |
| SDNQ Triton fallback | Pass — "Falling back to PyTorch Eager mode" |
| HF model download (12 files) | Pass — 13:30s (first run), cached thereafter |
| Pipeline load (5/5 components) | Pass — 7s warm |
| HTTP 200 on port 7860 | Pass — 5-13ms |
| Z-Image-Turbo 1024x1024, 9 steps | Pass — 14.2s/step (image 1), 14.5s/step (image 2), 15.1s/step (image 3) |
| Memory pressure | Acceptable — no OOM with cpu_offload(device="mps") |

## Blocked / Deferred

- FLUX.2-klein-4B test → Sprint 002
- LoRA hot-swap on MPS → Sprint 002
- Image-to-image → Sprint 002
- Locale fallback fix → Sprint 002
