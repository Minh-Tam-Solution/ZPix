# Sprint 003: Offline Client — Tauri Scaffold + Model Cache

## Goal
Build the foundational offline client: Tauri native app wrapper with Python sidecar, model cache, and offline-ready Gradio UI.

## Duration: ~5 dev-days

## User Stories Covered
- US-2.1 (Native App Launch) — scaffold + auto-open
- US-2.2 (Offline Generation) — model cache + first-run wizard

## Tasks

| # | Task | Story | Owner | Status |
|---|------|-------|-------|--------|
| 1 | Init Tauri project (`src-tauri/`) with WKWebView | US-2.1 | @architect | **Done** |
| 2 | Python sidecar integration (spawn `uv run app.py`) | US-2.1 | @coder | **Done** |
| 3 | Auto-open WebView when Gradio ready (health poll) | US-2.1 | @coder | **Done** |
| 4 | Model cache dir (`~/Library/Application Support/ZPix/models/`) | US-2.2 | @coder | **Done** |
| 5 | First-run wizard (download Z-Image-Turbo ~12GB) | US-2.2 | @coder | **Done** *(auto-detect offline, no explicit wizard yet)* |
| 6 | Test `.app` bundle build + launch | US-2.1 | @tester | **Done** |
| 7 | Smoke test: generation offline (Wi-Fi disabled) | US-2.2 | @tester | Pending *(needs manual test on target Mac)* |

## Architecture

```
ZPix.app (Tauri / WKWebView)
  └─► Python sidecar (uv run app.py --offline)
       ├─► Gradio UI @ 127.0.0.1:7860
       ├─► Model cache: ~/Library/Application Support/ZPix/models/
       └─► Offline flag: skip HuggingFace download if cache exists
```

## Key Decisions
- Tauri v2 (latest stable)
- Keep Gradio UI — no React port
- Model cache uses `HF_HOME` env var pointing to app support dir
- First-run wizard: Tauri frontend page → download progress → launch

## Acceptance Criteria
- [ ] `npm run tauri dev` launches app + Gradio + WebView
- [ ] `npm run tauri build` produces `.app` bundle
- [ ] `.app` launches without terminal
- [ ] First-run downloads model to cache dir
- [ ] Second launch uses cached model (no internet)
- [ ] Generation works with Wi-Fi disabled

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Tauri + Python sidecar bundle size | Large | Ship without models; download on first run |
| uv not installed on target Mac | Blocks launch | Bundle `uv` binary or check + prompt |
| Code signing / notarization gate | Blocks distribution | Document as Phase 2b (post-MVP) |

## Definition of Done
- Tauri scaffold committed
- Python sidecar spawning Gradio
- `.app` builds and launches
- Model cache + offline generation validated

---

*Owner: @pm | Gate: G3→G4 | Date: 2026-05-05*
