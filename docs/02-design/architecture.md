# Architecture — ZPix trong NQH Content Platform

## System context

```
┌─────────────────────────────────────────────────────────────────┐
│                    NQH Content Platform                         │
│                                                                 │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────────┐  │
│  │  Postiz  │◄──►│  OGA Creative    │◄──►│  NQH AI-Platform  │  │
│  │ (publish)│    │  Studio (gen)    │    │  (Ollama/LLM)     │  │
│  └────▲─────┘    └───────▲──────────┘    └───────────────────┘  │
│       │                  │                                      │
│       │    ┌─────────────┘                                      │
│       │    │  findings                                          │
│       │    │                                                    │
│  ┌────┴────▼────┐                                               │
│  │    ZPix      │  Phase 1: research artifact                   │
│  │  (offline)   │  Phase 2: offline .app client                 │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

## ZPix hien tai — 3-layer launcher (khong thay doi)

```
ZPix.exe (C++ / WinMain)          ← Layer 1: native shell
  └─► start.ps1 (PowerShell)     ← Layer 2: env bootstrap
       └─► app.py (Gradio)       ← Layer 3: UI + inference
```

Mac dev mode thay doi:
- Layer 1: **bo qua** (khong co C++ shell, user mo browser tay)
- Layer 2: `start-mac.sh` thay `start.ps1` (dung system `uv`, khong GPU detection)
- Layer 3: `app.py` + `enable_model_cpu_offload(device="mps")` patch

## Phase 1: Research data flow

```
ZPix (Mac dev mode)
  │
  ├─► Benchmark: MPS vs MLX vs sd.cpp
  │     ├─ Z-Image-Turbo (SDNQ uint4, fp16, bf16)
  │     ├─ FLUX.2-klein-4B (SDNQ 4bit, fp16)
  │     └─ 512x512, 768x768, 1024x1024
  │
  ├─► Findings doc: docs/04-build/benchmark-results.md
  │
  └─► Apply to OGA local-server/server.py:
        ├─ torch_dtype recommendation
        ├─ Memory management pattern
        ├─ Quantization compatibility matrix
        └─ Slicing config per RAM tier
```

## Phase 2: Offline client architecture

```
ZPix.app (Tauri / WKWebView)      ← Layer 1: native shell (cross-platform)
  └─► Python sidecar (uv run)     ← Layer 2: inference engine
       ├─► Gradio UI               ← Layer 3: local web UI
       ├─► Model cache              ~/Library/Application Support/ZPix/models/
       ├─► Brand templates          synced from Postiz workspace
       └─► Offline queue            pending uploads → Postiz API khi co mang
```

### Integration points

| Interface | Direction | Protocol | Data |
|-----------|-----------|----------|------|
| ZPix → OGA | One-way (Phase 1) | Git PR / docs | Benchmark results, optimization patterns |
| ZPix → Postiz | Push (Phase 2) | REST API | Generated images → Postiz draft posts |
| Postiz → ZPix | Pull (Phase 2) | REST API | Brand templates, tone guidelines |
| ZPix ← HuggingFace | Pull (first-run) | HTTPS | Model weights (cached locally) |

### Key decisions

| Decision | Rationale | Alternative rejected |
|----------|-----------|---------------------|
| Giu Gradio UI (khong port sang React) | Upstream ZPix compatible; Gradio = Python-native, it overhead | React UI (10+ dev-days, diverge tu upstream) |
| Tauri thay C++ shell | Cross-platform (WKWebView Mac, WebView2 Win), ~3MB binary, Rust safe | Electron (200MB+ bundle), Swift (Mac-only) |
| `cpu_offload(device="mps")` thay `pipe.to("mps")` | Giam peak memory, cho phep chay tren 16GB Mac | `pipe.to("mps")` (OOM tren 24GB voi 1024x1024) |
| fp16 fallback khi SDNQ fail | SDNQ uint4 kernels = CUDA-only; fp16 chay OK tren MPS | Skip model entirely (mat functionality) |
| Offline queue voi last-write-wins | Don gian, NV luon co latest version | CRDT (over-engineering cho use case nay) |

### Security considerations

- Model weights: download tu HuggingFace (HTTPS, checksum verify)
- Brand templates: Postiz API voi auth token (JWT tu Postiz session)
- Offline queue: local SQLite, encrypt at rest neu chua sensitive brand content
- No telemetry: offline client khong gui bat ky data nao ve server khi khong co mang

## Component mapping

| Component | Phase 1 (research) | Phase 2 (offline) |
|-----------|--------------------|--------------------|
| `main.cpp` + `source/cpp/` | Khong dung | Thay bang Tauri `src-tauri/` |
| `start.ps1` + `source/ps/` | Khong dung (Mac) | Giu cho Windows path |
| `start-mac.sh` | Entry point | Wrapped by Tauri sidecar |
| `app.py` | Core — benchmark target | Core — offline UI |
| `source/py/` | Test LoRA, i2i, history | Them brand template loader |
| `requirements-mac.txt` | Dependencies | Dependencies + offline sync lib |
| `data/curated_models.json` | Model registry | Extend voi offline-available flag |

---

*Owner: @architect | Gate: G2 | Date: 2026-05-04*
