# Acceptance Criteria — ZPix

## Phase 1: Research (Sprint 002)

| ID | Story | Criterion | Verification |
|----|-------|-----------|-------------|
| AC-1.1a | US-1.1 | Benchmark covers >= 11 configs (3 backends x 2 models x resolutions) | Config count in results table |
| AC-1.1b | US-1.1 | Each config generates 3 valid images without OOM | No crash logs, images saved |
| AC-1.1c | US-1.1 | Results include time/step + peak memory per config | Columns in benchmark-results.md |
| AC-1.1d | US-1.1 | Recommendation for 16GB and 24GB tiers documented | Section in benchmark-results.md |
| AC-1.2a | US-1.2 | FLUX.2-klein-4B loads on MPS without error | Pipeline load log, no exceptions |
| AC-1.2b | US-1.2 | Generation completes (4 steps, 1024x1024) | Image file produced |
| AC-1.3a | US-1.3 | LoRA safetensors loads via Gradio UI | No error in console |
| AC-1.3b | US-1.3 | Trigger word auto-inserted | Prompt field contains trigger word |
| AC-1.3c | US-1.3 | Output visually different with vs without LoRA | Side-by-side screenshot |
| AC-1.4a | US-1.4 | Reference image accepted via drag/upload | Gradio UI shows reference |
| AC-1.4b | US-1.4 | i2i generation completes | Image file produced |
| AC-1.5a | US-1.5 | No "Translation for C not found" warning | Console log clean |

## Phase 2: Offline Client

| ID | Story | Criterion | Verification |
|----|-------|-----------|-------------|
| AC-2.1a | US-2.1 | .app launches on macOS 14.0+ Apple Silicon | Manual test on M4 Pro |
| AC-2.1b | US-2.1 | WebView opens when Gradio ready | URL loads automatically |
| AC-2.2a | US-2.2 | Generation works with Wi-Fi disabled | Airplane mode test |
| AC-2.2b | US-2.2 | Image saved to ~/Pictures/ZPix/ | File exists check |
| AC-2.3a | US-2.3 | Brand config loaded from local JSON | UI shows brand presets |
| AC-2.4a | US-2.4 | Offline images auto-push to Postiz when online | Draft created in Postiz |
| AC-2.4b | US-2.4 | No duplicate uploads on retry | Idempotency check |

---

*Owner: @pm | Gate: G1 | Date: 2026-05-05*
