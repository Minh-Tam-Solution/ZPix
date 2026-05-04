# Business Case — ZPix Research & Offline Client

## Context

NQH dang build "NQH Content Platform" gom 3 thanh phan:

| Component | Vai tro | Repo |
|-----------|---------|------|
| **Postiz** (NQH Brand Ambassador) | Content management + publishing 30+ MXH | postiz-app |
| **OGA** (NQH Creative Studio) | AI generation engine (200+ models, local + cloud) | Open-Generative-AI |
| **ZPix** (repo nay) | Research artifact → offline client | ZPix |

## Dual-phase justification

### Phase 1: Research artifact (now → 2-3 tuan)

**Chi phi:** 0 dong them (su dung ZPix repo co san, dev time ~5 dev-days)

**Gia tri:**
- Benchmark data cho OGA local-server tuning (MPS vs MLX vs sd.cpp, quantization options)
- Validated `enable_model_cpu_offload(device="mps")` pattern — da chung minh giam OOM tren M4 Pro 24GB (test 2026-05-04: 3 images, ~14s/step stable, khong OOM)
- Findings apply truc tiep cho OGA Sprint 5 (Diffusers migration)

**ROI:** Tiet kiem ~3-5 dev-days OGA team khong phai tu trial-and-error MPS optimization.

### Phase 2: Offline client (sau Phase 1, ~2-4 tuan)

**Chi phi:** ~10-15 dev-days (Tauri/Swift wrapper, model bundling, offline sync)

**Gia tri:**
- 149 NV co the tao content bat ky dau, bat ky luc nao — khong phu thuoc mang
- Giam API cost: moi image gen offline = tiet kiem 1 cloud API call ($0.02-0.05/image)
- Brand consistency: offline client pre-load brand guidelines + tone templates

**ROI khi scale:**
- 149 NV x 5 images/tuan x $0.03/image = ~$1,160/thang tiet kiem API cost
- Khong tinh gia tri brand presence khi NV co the tao content tai su kien/remote

## Risk

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Apple Silicon models chat luong kem hon cloud | Medium | Benchmark truoc, chi deploy neu >= 80% cloud quality |
| SDNQ quantization khong ho tro MPS | High (da xac nhan) | Fallback fp16 model goc — da test OK |
| Offline client maintenance burden | Medium | Dung Tauri (1 codebase Win+Mac), auto-update via Sparkle |
| ZPix upstream license conflict | Low | GPL-3.0 — fork OK, chi can giu license notice |

## Decision

**CEO approved:** ZPix = Phase 1 research (benchmark + optimize) → Phase 2 offline `.app` (neu Phase 1 chung minh Apple Silicon viable).

**Kill signal Phase 2:** Neu benchmark cho thay M4 Pro < 50% chat luong cloud models → khong build offline client, chi giu research findings.

---

*Owner: @pm | Gate: G0 | Date: 2026-05-04*
