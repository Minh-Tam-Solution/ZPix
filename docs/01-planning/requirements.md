# Requirements — ZPix Research & Offline Client

## Phase 1: Research (Sprint hien tai, ~5 dev-days)

### R1.1 — Mac dev mode (DONE)

**Status:** Completed 2026-05-04

- [x] `requirements-mac.txt` — Python deps cho macOS (bo triton-windows, flash-attn, cu130)
- [x] `start-mac.sh` — Bash launcher tuong duong start.ps1
- [x] `app.py` patch — `enable_model_cpu_offload(device="mps")` thay `pipe.to("mps")` (chong OOM)
- [x] Smoke test: Z-Image-Turbo, 9 steps, 1024x1024, M4 Pro 24GB → 14-15s/step, khong OOM

### R1.2 — Benchmark suite

| Test case | Models | Backends | Resolutions | Metrics |
|-----------|--------|----------|-------------|---------|
| Text-to-Image | Z-Image-Turbo, FLUX.2-klein-4B | MPS (Diffusers), MLX, sd.cpp | 512x512, 768x768, 1024x1024 | Time/step, peak memory, image quality (FID neu co ref set) |

**Deliverable:** `docs/04-build/benchmark-results.md` — bang so sanh, recommendation cho OGA local-server config.

### R1.3 — Feed findings to OGA

- PR hoac report cho OGA repo voi:
  - Optimal `torch_dtype` cho Apple Silicon (bf16 vs fp16)
  - Memory management pattern (`cpu_offload(device="mps")` vs `pipe.to("mps")` vs `enable_sequential_cpu_offload`)
  - Quantization compatibility matrix (SDNQ uint4 tren MPS: NO, fp16: YES, bf16: YES)
  - Recommended slicing config (attention_slicing, vae_slicing) theo RAM tier

### R1.4 — Test remaining ZPix features on MPS

- [ ] FLUX.2-klein-4B model load + generate
- [ ] LoRA hot-swap (`source/py/lora_model.py`)
- [ ] Image-to-image workflow
- [ ] Locale fallback (fix "Translation for C not found")

## Phase 2: Offline client (sau Phase 1, ~10-15 dev-days)

### R2.1 — Native app wrapper

- Tauri (WKWebView Mac, WebView2 Win) thay C++ shell hien tai
- Spawn Python process (giu kien truc 3-layer)
- Auto-open browser khi Gradio ready
- macOS: `.app` bundle, code-signed, notarized
- Windows: giu nguyen ZPix.exe path hien tai

### R2.2 — Offline model bundling

- Pre-download Z-Image-Turbo fp16 (~12GB) vao app bundle hoac first-run wizard
- Cache tai `~/Library/Application Support/ZPix/models/` (Mac) hoac `%APPDATA%\ZPix\models\` (Win)
- Khong can internet sau first-run

### R2.3 — Brand template integration

- Load brand guidelines tu JSON config (logo, tone, DO/DONT, hashtag defaults)
- Pre-fill prompt voi brand context
- Sync templates khi co mang (pull tu OGA hoac Postiz workspace)

### R2.4 — Offline → Online sync

- Queue generated images locally
- Khi co mang: auto-push len Postiz draft (API call)
- Conflict resolution: last-write-wins (offline content luon moi hon)

## Non-functional requirements

| NFR | Target |
|-----|--------|
| Generation time (512x512, Z-Image-Turbo, M4 Pro) | < 30s |
| Memory peak (1024x1024) | < 20GB unified |
| App startup (warm, model cached) | < 15s |
| Offline storage per model | < 15GB |
| Supported macOS | 14.0+ (Sonoma, Apple Silicon only) |

## Out of scope

- Video generation (OGA handles via Wan2GP/cloud)
- Lip sync (OGA Cinema Studio)
- Cloud model routing (OGA + Muapi.ai)
- Social media publishing (Postiz)

---

*Owner: @pm | Gate: G0.1, G1 | Date: 2026-05-04*
