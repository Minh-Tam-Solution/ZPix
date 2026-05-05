# Deploy Plan — ZPix 2.0.0-mvp

## Scope

Phase 2 MVP: offline `.app` with brand templates. Sync deferred.

## Artifacts

| Artifact | Path | Size | Notes |
|----------|------|------|-------|
| ZPix.app (Tauri bundle) | `src-tauri/target/release/bundle/macos/ZPix.app` | ~15MB | Does NOT include model weights |
| Model weights | Downloaded on first run to `~/Library/Application Support/com.nqh.zpix/models/` | ~12-20GB | Z-Image-Turbo + FLUX.2-klein-4B |
| Python venv | Created on first run at `.venv/` | ~2GB | torch + diffusers + gradio |

## Prerequisites on target Mac

- macOS 14.0+ (Sonoma or later)
- Apple Silicon (M1/M2/M3/M4)
- `uv` installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- ~35GB free disk (app + models + venv)
- Internet for first run (model download)

## Install steps

1. Copy ZPix folder to target Mac (entire repo checkout, or bundled archive)
2. Run `./start-mac.sh` (dev mode) or double-click `ZPix.app` (Tauri mode)
3. First run: venv creation (~2 min) + model download (~15 min on fast connection)
4. Subsequent runs: skip install, launch in ~10s

## Distribution (internal)

- **Current**: copy repo folder to target Mac via AirDrop / USB / NAS
- **Future**: internal download portal with versioned zip
- **NOT YET**: code-signed + notarized `.app` (requires Apple Developer account, ~$99/year)

## Rollback

Delete `.venv/` and `~/Library/Application Support/com.nqh.zpix/` to reset to clean state.

## Known limitations

- No auto-update mechanism
- No code signing (macOS Gatekeeper will warn on first launch — right-click → Open to bypass)
- Offline mode requires models cached from a previous online run
- Brand template sync from Postiz not yet implemented

---

*Owner: @coder | Gate: G4 | Date: 2026-05-05*
