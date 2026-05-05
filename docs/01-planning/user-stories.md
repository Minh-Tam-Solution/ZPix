# User Stories — ZPix

## Phase 1: Research

### US-1.1: MPS Benchmark
**As** DevOps lead,
**I want** a reproducible benchmark comparing MPS, MLX, and sd.cpp backends on M4 Pro 24GB,
**so that** I can configure OGA local-server with the optimal backend/dtype/slicing settings.

**Acceptance Criteria:**
- [ ] Benchmark script runs all 11 test configs from `tp-001-mps-benchmark.md`
- [ ] Each config generates 3 valid images (no OOM, no NaN artifacts)
- [ ] Results table in `docs/04-build/benchmark-results.md` with time/step, peak memory per config
- [ ] Recommendation section identifying optimal config for 16GB and 24GB tiers

### US-1.2: FLUX.2-klein-4B on MPS
**As** a content creator,
**I want** FLUX.2-klein-4B to work on Mac dev mode,
**so that** I have a second model option for different image styles.

**Acceptance Criteria:**
- [ ] FLUX.2-klein-4B model loads without error on MPS
- [ ] Image generation completes (4 steps, 1024x1024) without OOM
- [ ] Step time documented in sprint results

### US-1.3: LoRA Hot-Swap on MPS
**As** a brand manager,
**I want** to load custom LoRA styles on Mac,
**so that** I can test brand-specific LoRA files before deploying to OGA.

**Acceptance Criteria:**
- [ ] LoRA safetensors file loads via Gradio UI on MPS
- [ ] Trigger word auto-inserted from LoRA metadata
- [ ] Generation with LoRA produces visually different output than without

### US-1.4: Image-to-Image on MPS
**As** a content creator,
**I want** to use reference images for image-to-image generation on Mac,
**so that** I can edit existing images with AI.

**Acceptance Criteria:**
- [ ] Drag/upload reference image works in Gradio UI
- [ ] Image-to-image generation completes without error
- [ ] Output reflects both prompt and reference image

### US-1.5: Locale Fallback
**As** a macOS user,
**I want** the app to handle missing locale gracefully,
**so that** I don't see "Translation for C not found" warnings.

**Acceptance Criteria:**
- [ ] When `$LANG=C` or unset, app defaults to `en-US` without warning
- [ ] `start-mac.sh` passes valid locale to `--locale` flag

## Phase 2: Offline Client

### US-2.1: Native App Launch
**As** an NQH employee,
**I want** to double-click a ZPix.app icon on my Mac,
**so that** the AI image generator opens without terminal commands.

**Acceptance Criteria:**
- [ ] `.app` bundle launches on macOS 14.0+ Apple Silicon
- [ ] Browser/WebView opens automatically when Gradio is ready
- [ ] No Xcode or developer tools required

### US-2.2: Offline Generation
**As** an NQH employee at a remote event,
**I want** to generate images without internet,
**so that** I can create content for social media even offline.

**Acceptance Criteria:**
- [ ] Model weights cached locally after first download
- [ ] Generation works with Wi-Fi disabled
- [ ] Image saved to `~/Pictures/ZPix/` as normal

### US-2.3: Brand Templates
**As** a brand manager,
**I want** pre-loaded brand guidelines in the offline app,
**so that** employees follow brand tone and style even offline.

**Acceptance Criteria:**
- [ ] Brand config (logo, tone, DO/DONT, hashtags) loaded from local JSON
- [ ] Prompt pre-filled with brand context when brand is selected
- [ ] Templates sync from Postiz workspace when online

### US-2.4: Offline-to-Online Sync
**As** an NQH employee,
**I want** my offline-generated images to auto-upload to Postiz when I get back online,
**so that** I don't have to manually re-upload content.

**Acceptance Criteria:**
- [ ] Generated images queued locally when offline
- [ ] Auto-push to Postiz draft when connectivity restored
- [ ] No duplicate uploads on retry

---

*Owner: @pm | Gate: G1 | Date: 2026-05-05*
