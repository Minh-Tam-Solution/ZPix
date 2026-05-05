# Changelog — ZPix (NQH Fork)

All notable changes to the NQH fork of ZPix are documented here.
Upstream: github.com/SamuelTallet/ZPix (GPL-3.0)

## [2.0.0-mvp] — 2026-05-05

### Added
- **macOS dev mode**: `start-mac.sh` + `requirements-mac.txt` for Apple Silicon (M-series)
- **MPS inference**: `enable_model_cpu_offload(device="mps")` — no OOM on 24GB unified memory
- **Tauri v2 native app**: `.app` bundle (15MB) with WKWebView, Python sidecar, auto-open Gradio
- **Offline mode**: auto-detect connectivity, `--offline` flag, cached models via `HF_HOME`
- **Brand templates**: 5 NQH brands (BKL Coffee, Thom F&B, AirDream, Kupid, LHP) + free style
  - Brand selector dropdown in Gradio UI
  - Auto-prepend `style_prefix` to prompts (hidden from user)
  - Brand-specific example prompts
  - Brand guidelines accordion (Tone / DO / DONT / Hashtags)
  - PNG metadata preserves original user prompt (not prefixed)
- **Benchmark suite**: `scripts/benchmark_mps.py` — 11 configs, MPS/MLX/sd.cpp
- **SDLC docs**: Full G0→G3 gate artifacts, 4 sprint docs, ADR-001, test plan

### Changed
- `app.py`: MPS-aware device selection (CUDA → MPS → CPU fallback)
- `app.py`: `--offline` CLI flag for `local_files_only` model loading
- `start-mac.sh`: locale validation (`$LANG=C` → `en-US` fallback)

### Fixed
- Tauri: orphan Python process on quit (process group kill via `setpgid` + `SIGTERM`)
- Tauri: `.app` bundle path resolution (`resolve_app_dir()` with ancestor walk)

### Not included (deferred)
- Offline-to-online sync with Postiz (Sprint 005 — blocked on Postiz pilot)
- Brand template sync from Postiz workspace API
- Code signing + notarization (requires Apple Developer account)
- MLX / sd.cpp backends (not available for these models at time of release)

### Benchmark highlights (M4 Pro 24GB)
| Config | Time/Step | Peak Memory |
|--------|-----------|-------------|
| Z-Image Turbo bf16 512×512 | 4.3s | 5.1 GB |
| Z-Image Turbo bf16 1024×1024 | 23.3s | 14.0 GB |
| FLUX.2-klein-4B bf16 512×512 | 4.5s | 4.6 GB |
| FLUX.2-klein-4B bf16 1024×1024 | 16.8s | 8.9 GB |

---

*Based on upstream ZPix v1.0.5 by Samuel Tallet*
