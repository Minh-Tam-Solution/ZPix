# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ZPix is a Windows desktop app for local AI image generation (Z-Image-Turbo and FLUX.2-klein-4B via Hugging Face `diffusers`). Author: Samuel Tallet. License: GPL-3.0+.

The repo is **Windows-only** at runtime — `main.cpp` is `wWinMain`, the launcher uses `windows.h`/WebView2/JobObject, and install/launch is driven by PowerShell. macOS/Linux builds are not expected.

## Architecture (3-layer launcher)

The app is one product but three languages cooperating in a specific sequence. Understanding this flow is the prerequisite for almost any change:

1. **`ZPix.exe` — C++ shell (`main.cpp` + `source/cpp/*.cpp`, headers in `include/`)**
   - `wWinMain` → `find_free_port()` picks a localhost port → creates a Win32 window hosting a WebView2 control.
   - `StarterThread` (`source/cpp/starter.cpp`) spawns `powershell.exe -NoProfile -ExecutionPolicy Bypass -File start.ps1 -Port <port>` inside a `JobObject` so the Python child dies with the shell.
   - `WatcherThread` polls the port; when Gradio is up it posts `WM_APP_WEBVIEW_READY` to the main thread, which navigates the WebView to `http://127.0.0.1:<port>` and hides the console (`console.cpp`).
   - When the starter exits, it `PostThreadMessage(WM_QUIT)` to tear down the GUI.
   - Built with CMake + vcpkg; only declared C++ dep is `unofficial-webview2` (vcpkg.json), plus system libs `ws2_32`, `dwmapi`. C++20, 64-bit Windows.

2. **`start.ps1` + `source/ps/*.ps1` — Python environment bootstrap**
   - `gpu_detection.ps1` enumerates GPUs; NVIDIA gets the optimized path (CUDA 13.0 torch 2.10.0+cu130, triton-windows, prebuilt flash-attention wheel). Anything else falls back to default torch with `Backend "auto"`.
   - Uses the **bundled** `tools/astral/uv.exe` (do not assume a global `uv`). Python 3.13.11 venv at `.venv/`. Successful optimized install drops a `.venv\optimized` marker to skip reinstall on next launch; `uv venv --clear` removes it.
   - `app_invoking.ps1` finally runs `uv run app.py --port <port> --locale <Get-WinSystemLocale>`. Locale comes from Windows, not from a flag the user picks.
   - `DEBUG` or `DEBUG.txt` file at repo root flips PowerShell's `$DebugPreference` to `Continue` and keeps the console window visible (otherwise `console.cpp` hides it by title once the WebView is ready).

3. **`app.py` + `source/py/*.py` — Gradio UI and inference**
   - `app.py` is the entrypoint loaded by `uv run`. It builds the Gradio interface, loads `Flux2KleinPipeline` / `ZImagePipeline` from `diffusers`, and applies SDNQ quantization options via `apply_sdnq_options_to_model`.
   - Per-feature modules in `source/py/`: `image_model.py` / `image_models.py` (Hugging Face download w/ backup-id fallback), `lora_model.py` (hot-swap LoRA + trigger word from safetensors metadata), `gen_history.py` (SQLite prompt history), `prompt_extract.py` (read prompt from PNG metadata), `resolutions.py` (11 supported aspect ratios), `disclaimer.py` (TOU gate), `os_abstract.py`, `trigger_word.py`, `ex_prompts.py`.
   - User-data paths: outputs → `<User>\Pictures\ZPix`; prompt DB → `~/.zpix/prompts_history.sqlite`; Triton cache → `~/.triton`; Gradio temp → `<repo>/temp/GradioApp` (cleared on every run).

There is **no `pyproject.toml` / `requirements.txt`** — Python dependencies are pinned imperatively inside `start.ps1` (`Install-Torch`, `Install-Package`, `Install-Archive` from `package_utils.ps1`). Adding/upgrading a Python dep means editing the relevant `Install-*` call there, not a manifest.

## Build / run / clean

All commands are PowerShell on Windows; macOS/Linux cannot run them. Running them from this checkout (a research clone on macOS) will fail by design.

```powershell
# C++ build → produces ZPix.exe + WebView2Loader.dll at repo root
.\build.ps1                   # vswhere → Enter-VsDevShell → vcpkg install → cmake -B build && cmake --build build --config Release

# End-user run path (this is what ZPix.exe spawns; rarely invoked manually)
.\start.ps1 -Port 7860

# Reset caches / venv / build artifacts (interactive prompts)
.\clean.cmd
```

Useful manual invocations when iterating on Python without the C++ shell:

```powershell
.\tools\astral\uv.exe run app.py --port 7860 --locale en-US
```

There is no test suite, no CI, no lint script wired into the repo (Ruff is mentioned in README credits but no config is present). Don't claim "tests pass" — verify by launching the app.

## Conventions worth knowing

- **Metadata files (`metadata/NAME`, `VERSION`, `DESCRIPTION`, `HOME_URL`, `DONATE_URL`)** are plain text read at build time by CMake (`file(READ …)`) and at runtime by both `start.ps1` (`Get-Content`) and the C++ side (`metadata.cpp` via `metadata.hpp`). When bumping versions, edit the file in `metadata/`, not a string literal.
- **Translations** live as flat JSON keyed by English source (`translations/fr-FR.json`). Locale is auto-detected from Windows; there is no in-app picker. Adding a language = drop `<locale>.json` in `translations/`.
- **Models** are declared in `data/curated_models.json`; example prompts in `data/example_prompts.json`. `image_models.py` resolves these via `pydantic.TypeAdapter` and falls back to `model.backup_id` if `snapshot_download` fails.
- **Asset serving**: `app.py` calls `gr.set_static_paths(paths=[assets_dir])` so anything dropped in `assets/` is served directly by Gradio.

## SDLC scaffolding (ignore for code work)

`AGENTS.md`, `IDENTITY.md`, `.sdlc-config.json`, and `docs/00-foundation/` … `docs/08-collaborate/` are EndiorBot SDLC framework scaffolding generated outside the upstream ZPix project. They reference an `./endiorbot.mjs` CLI that **does not exist in this repo** — do not run those commands. `IDENTITY.md` claims the tech stack is "JavaScript / npm", which is wrong; trust this file and the source tree instead. The framework files are gitignored under `.endiorbot/`, `.sdlc-framework`, and `.claude/` per `.gitignore`.
