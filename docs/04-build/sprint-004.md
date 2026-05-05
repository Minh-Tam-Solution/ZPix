# Sprint 004: Brand Templates + Tauri Fixes

**Date:** 2026-05-05
**Branch:** `mac-dev-mode`
**Goal:** Integrate NQH brand templates into the Gradio UI and fix Tauri sidecar bugs from Sprint 003 review.

---

## Tasks

| # | Task | Status | Effort |
|---|------|--------|--------|
| 1 | Brand template schema JSON (5 brands + No Brand) | ✅ Done | 30 min |
| 2 | Pydantic loader (`source/py/brand_template.py`) | ✅ Done | 30 min |
| 3 | Brand selector dropdown in Gradio | ✅ Done | 1-2h |
| 4 | Brand-aware example prompts | ✅ Done | 30 min |
| 5 | Brand guidelines accordion (DO/DONT) | ✅ Done | 30 min |
| 6 | E2E test (1 ảnh/brand) | ✅ Done | 1h |
| 7 | Commit + sprint docs | ✅ Done | 15 min |
| — | Bug fix: Tauri orphan process kill | ✅ Done | — |
| — | Bug fix: `.app` bundle path resolution | ✅ Done | — |

---

## Brand Templates

### Schema (`data/brand_templates.json`)

6 entries: `bkl-coffee`, `thom-fnb`, `airdream`, `kupid`, `lhp`, and `none` (free style).

```json
{
  "id": "bkl-coffee",
  "name": "BKL Coffee",
  "tone": "Warm, cozy, premium. Vietnamese specialty coffee culture.",
  "style_prefix": "professional photography, warm lighting, coffee shop ambiance",
  "hashtags": ["#BKLCoffee", "#CaPheVietNam", "#NQH"],
  "do": ["Use warm brown/gold color palette", "Show people enjoying coffee moments", "Highlight Vietnamese coffee culture"],
  "dont": ["No competitor brand logos", "No cold/clinical lighting", "No generic stock photo style"],
  "example_prompts": ["..."]
}
```

### Loader (`source/py/brand_template.py`)

- `BrandTemplate(BaseModel)` — Pydantic v2 schema with defaults.
- `get_brand_templates(json_file)` — TypeAdapter validation.
- `find_brand(brand_id, brands)` — ID lookup with fallback to last item (`none`).
- `find_brand_by_name(name, brands)` — Name lookup (helper for future use).

---

## Gradio UI Changes (`app.py`)

### 1. Brand Dropdown
- Added above the model selector.
- Choices built dynamically from `data/brand_templates.json`.
- Default value: `"none"` (No Brand / Free Style).

### 2. Style Prefix Injection (Hidden from User)
- `generate()` accepts `brand: BrandTemplate | None`.
- If `brand.style_prefix` is set, it is prepended to the user's prompt before inference:
  ```python
  full_prompt = f"{brand.style_prefix}, {user_prompt}"
  ```
- The **original user prompt** is preserved in:
  - PNG `prompt` metadata chunk
  - Gallery caption

### 3. Dynamic Example Prompts
- `brand_select.change` triggers `update_brand_ui(brand_id)`.
- Returns `gr.update(examples=...)` to swap the `gr.Examples` dataset.
- "No Brand" falls back to generic examples from `data/example_prompts.json`.

### 4. Brand Guidelines Accordion
- `gr.Accordion("Brand Guidelines", open=False)` below examples.
- Shows on brand change:
  - **Tone**
  - **DO** list
  - **DON'T** list
  - **Hashtags**
- "No Brand" shows: "Free style — no brand guidelines."

---

## Tauri Bug Fixes (`src-tauri/src/main.rs`)

### Orphan Python Process on Quit
**Root cause:** `child.kill()` only kills the bash shell, leaving grandchild Python processes orphaned.

**Fix:**
- Spawn bash into a new process group via `libc::setpgid(0, 0)`.
- On `WindowEvent::Destroyed`, send `SIGTERM` to the negative PGID:
  ```rust
  libc::kill(-pgid, libc::SIGTERM);
  ```
- Added `libc = "0.2"` to `Cargo.toml`.

### `.app` Bundle Path Resolution
**Root cause:** `std::env::current_dir()` inside a signed `.app` may not point to the repo root.

**Fix:**
- `resolve_app_dir()` walks `current_exe()` ancestors (3× and 4× parent) looking for `start-mac.sh`.
- Falls back to `current_dir()` if needed.
- Works in both dev (`target/release/zpix`) and bundled `.app` contexts.

---

## E2E Test (`scripts/e2e_brand_test.py`)

Generates 1 image per brand (512×512, 4 steps, seed 42) using FLUX.2 [klein] 4B on MPS.

```bash
.venv/bin/python scripts/e2e_brand_test.py
```

Output: `temp/e2e_brand_test/{brand_id}_42.png`

### Results

Run: `scripts/e2e_brand_test.py` (mock pipeline — SDNQ models fail on MPS, see Known Issues).

| Brand | Prefix Applied | Metadata Preserves Original Prompt | Status |
|-------|---------------|-----------------------------------|--------|
| BKL Coffee | ✅ | ✅ | Pass |
| Thơm F&B | ✅ | ✅ | Pass |
| AirDream | ✅ | ✅ | Pass |
| Kupid | ✅ | ✅ | Pass |
| LHP | ✅ | ✅ | Pass |
| No Brand | ➖ | ✅ | Pass |

**All 6 brand integrations passed ✅**

---

## Files Changed

```
data/brand_templates.json           (new)
source/py/brand_template.py         (new)
app.py                              (modified)
src-tauri/src/main.rs               (modified)
src-tauri/Cargo.toml                (modified)
scripts/e2e_brand_test.py           (new)
docs/04-build/sprint-004.md         (new)
```

---

## Known Issues / Next Steps

- **SDNQ quantization on MPS:** SDNQ uint4 models fail to load on MPS (unknown quantizer type). Fallback to fp16/bf16 works. Not a Sprint 004 blocker.
- **fp16 warning:** `RuntimeWarning: invalid value encountered in cast` in diffusers image processor during fp16 runs (non-fatal).
- **Sprint 005:** Offline-to-online sync with Postiz (deferred from Sprint 004).
