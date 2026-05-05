# Coder Handoff: ZPix Sprint 002 — MPS Benchmark + Feature Validation

> **Mục đích file này:** Prompt handoff cho @coder session mới trên Kimi CLI.
> Copy toàn bộ nội dung này vào prompt đầu tiên của session mới tại `/Users/dttai/Documents/Research/ZPix/`.

---

## Bạn là ai

Bạn là **Coder** của dự án ZPix — một Windows desktop app cho AI image generation đang được port sang macOS để phục vụ 2 mục đích:
1. **Research artifact**: benchmark Apple Silicon inference → feed kết quả cho NQH Creative Studio (OGA)
2. **Offline client (tương lai)**: native `.app` cho 149 nhân viên NQH tạo content không cần mạng

Bạn tiếp nhận từ CTO sau khi **Sprint 001 (Mac Dev Mode)** hoàn thành và **SDLC gates G0→G2 đã CONFIRMED**.

---

## Trạng thái hiện tại (2026-05-05)

### Repo
- **Path:** `/Users/dttai/Documents/Research/ZPix/`
- **Branch:** `mac-dev-mode` (3 commits ahead of `main`, commit `31820a2`)
- **Upstream:** github.com/SamuelTallet/ZPix (GPL-3.0, Windows-only)

### Đã hoàn thành ✅ (Sprint 001)
- [x] `requirements-mac.txt` — Python deps cho macOS (bỏ triton-windows, flash-attn, cu130 torch)
- [x] `start-mac.sh` — Bash launcher tương đương start.ps1 (dùng system `uv`, venv Python 3.13)
- [x] `app.py` patch — `enable_model_cpu_offload(device="mps")` thay vì `pipe.to("mps")` (chống OOM)
- [x] Smoke test: Z-Image-Turbo, 9 steps, 1024×1024, M4 Pro 24GB → 14-15s/step, không OOM, 3 ảnh OK
- [x] SDLC docs đầy đủ (problem-statement, business-case, requirements, user-stories, acceptance-criteria, architecture, ADR-001, sprint-001, test-plan, deploy, collaborate)
- [x] EndiorBot compliance 100%, gates G0→G2 CONFIRMED

### Chưa hoàn thành ⬜ (Sprint 002 — nhiệm vụ của bạn)
- [ ] Fix locale fallback (`$LANG=C` → `en-US`)
- [ ] Test FLUX.2-klein-4B trên MPS
- [ ] Test LoRA hot-swap trên MPS
- [ ] Test image-to-image workflow trên MPS
- [ ] Viết + chạy benchmark script (11 configs)
- [ ] Viết benchmark-results.md
- [ ] Report findings cho OGA

---

## Kiến trúc cần biết

### 3-layer launcher (Windows)
```
ZPix.exe (C++ / WinMain / WebView2)    ← bạn KHÔNG đụng layer này
  └─► start.ps1 (PowerShell)           ← bạn KHÔNG đụng layer này
       └─► app.py (Gradio + diffusers)  ← bạn làm việc ở đây
```

### Mac dev mode (thay thế layer 1+2)
```
start-mac.sh (Bash)                     ← launcher
  └─► uv run app.py --port 7860        ← Gradio UI + inference
       └─► http://127.0.0.1:7860       ← mở browser tay
```

### File quan trọng

| File | Vai trò | Bạn cần sửa? |
|------|---------|---------------|
| `app.py` (1027 dòng) | Gradio UI + pipeline load + inference | Có thể (nếu MPS cần thêm config) |
| `start-mac.sh` | Mac launcher | Có (fix locale) |
| `requirements-mac.txt` | Python deps macOS | Có thể (nếu cần thêm dep cho benchmark) |
| `source/py/image_models.py` | Model download + fallback | Đọc, không sửa |
| `source/py/lora_model.py` | LoRA hot-swap | Đọc, test |
| `source/py/prompt_extract.py` | Read prompt from PNG metadata | Đọc |
| `data/curated_models.json` | 2 models: Z-Image-Turbo SDNQ, FLUX.2-klein-4B SDNQ | Đọc |
| `docs/05-test/test-plans/tp-001-mps-benchmark.md` | 11 benchmark configs | Tham khảo |
| `docs/01-planning/acceptance-criteria.md` | 17 acceptance criteria | Checklist của bạn |

### Key code patterns

**Pipeline load (app.py:158-215):**
```python
pipe = pipe_class.from_pretrained(model.id, torch_dtype=torch.bfloat16)

# SDNQ quantization — CUDA/XPU only, skipped trên MPS (guard ở line 189):
if triton_is_available and (torch.cuda.is_available() or torch.xpu.is_available()):
    pipe.transformer = apply_sdnq_options_to_model(...)

# MPS path (line 204-207):
if torch.backends.mps.is_available():
    pipe.enable_model_cpu_offload(device="mps")
else:
    pipe.enable_model_cpu_offload()
```

**Model registry (data/curated_models.json):**
```json
[
  {"id": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32", "pipeline": "ZImagePipeline", "default": {"steps": 8}},
  {"id": "Disty0/FLUX.2-klein-4B-SDNQ-4bit-dynamic", "pipeline": "Flux2KleinPipeline", "default": {"steps": 4}}
]
```

**ADR-001 (đã quyết định, KHÔNG thay đổi):**
- Dùng `enable_model_cpu_offload(device="mps")` — offload từng sub-model
- KHÔNG dùng `pipe.to("mps")` — OOM trên 24GB
- KHÔNG dùng `pipe.to("mps") + slicing` — vẫn OOM

---

## 8 tasks Sprint 002 — theo thứ tự

### Task 1: Fix locale fallback (5 min)

**Vấn đề:** Khi `$LANG=C` hoặc unset trên macOS, `start-mac.sh` truyền locale không hợp lệ → warning "Translation for C not found".

**Sửa trong `start-mac.sh`:** Sau khi tính `LOCALE`, thêm validation:
```bash
# Validate locale format (xx-XX). If invalid, fallback to en-US.
if [[ ! "$LOCALE" =~ ^[a-z]{2}-[A-Z]{2}$ ]]; then
    LOCALE="en-US"
fi
```

**Verify:** `LANG=C ./start-mac.sh` → không còn warning "Translation for C not found" trong log.

**AC:** AC-1.5a

### Task 2: Test FLUX.2-klein-4B trên MPS (1-2h, download ~8GB lần đầu)

**Bước:**
1. Chạy `./start-mac.sh`, mở http://127.0.0.1:7860
2. Trong Gradio UI, đổi model sang "FLUX.2 [klein] 4B"
3. Đợi model download (HuggingFace, ~8GB)
4. Generate ảnh: prompt bất kỳ, 4 steps (default), 1024×1024
5. Ghi nhận: thời gian/step, có OOM không, chất lượng ảnh

**Nếu OOM:**
- Thử `enable_sequential_cpu_offload(device="mps")` thay vì `enable_model_cpu_offload(device="mps")` — chậm hơn nhưng ít memory hơn
- Hoặc giảm resolution: 768×768, 512×512
- Ghi nhận resolution tối đa chạy được

**AC:** AC-1.2a, AC-1.2b

### Task 3: Test LoRA hot-swap trên MPS (30 min)

**Bước:**
1. Download 1 public LoRA file (bất kỳ LoRA compatible với FLUX hoặc SDXL). Ví dụ:
   - https://huggingface.co/XLabs-AI/flux-lora-collection (pick 1 .safetensors)
2. Trong Gradio UI, load LoRA file
3. Verify: trigger word auto-inserted? (check `source/py/lora_model.py:129` — cast bfloat16)
4. Generate ảnh with LoRA vs without LoRA → so sánh visual

**Nếu fail:** Ghi nhận error message, check xem `lora_model.py` có `.to(device)` call nào miss MPS không.

**AC:** AC-1.3a, AC-1.3b, AC-1.3c

### Task 4: Test image-to-image (30 min)

**Bước:**
1. Dùng FLUX.2-klein-4B (model duy nhất có feature `image-to-image` trong curated_models.json)
2. Drag hoặc upload 1 reference image vào Gradio UI
3. Nhập prompt, generate
4. Verify: output phản ánh cả prompt lẫn reference image

**AC:** AC-1.4a, AC-1.4b

### Task 5: Viết benchmark script (2-3h)

**Tạo `scripts/benchmark_mps.py`:**
```python
# Pseudo-code — bạn implement chi tiết
import torch, time, psutil

CONFIGS = [
    {"model": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32", "res": (512,512), "steps": 8, "dtype": "bf16"},
    {"model": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32", "res": (768,768), "steps": 8, "dtype": "bf16"},
    {"model": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32", "res": (1024,1024), "steps": 8, "dtype": "bf16"},
    # ... thêm theo tp-001-mps-benchmark.md (11 configs total)
]

for config in CONFIGS:
    # Load pipeline
    # Measure: torch.mps.driver_allocated_size() for peak memory
    # Generate 3 images, record median time/step
    # Save results to CSV
```

**Output:** `results/benchmark_mps.csv` + console summary

**Lưu ý:**
- MLX backend: check xem `diffusers` có MLX pipeline cho Z-Image-Turbo không. Nếu không → ghi N/A.
- sd.cpp: check `electron/lib/` trong OGA repo (`/Users/dttai/Documents/Research/Open-Generative-AI/electron/lib/`) có binary không. Nếu không → ghi N/A.
- Chỉ benchmark những gì actually available, đừng giả data.

**AC:** AC-1.1a

### Task 6: Chạy benchmark suite (1-2h)

- Chạy `scripts/benchmark_mps.py`
- Cold start mỗi config (kill Python, clear MPS cache: `torch.mps.empty_cache()`)
- 3 images/config, report median
- Ghi nhận mọi OOM hoặc failure

**AC:** AC-1.1b, AC-1.1c

### Task 7: Viết benchmark-results.md (1h)

**Tạo `docs/04-build/benchmark-results.md`:**

```markdown
# Benchmark Results — Apple Silicon (M4 Pro 24GB)

## Test Environment
- Hardware: Apple M4 Pro, 24GB unified memory
- OS: macOS 15.x
- Python: 3.13.11, torch 2.10.0, diffusers (commit b75703...)

## Results

| # | Model | Backend | Resolution | Steps | Dtype | Time/Step (median) | Peak Memory | Status |
|---|-------|---------|-----------|-------|-------|-------------------|-------------|--------|
| 1 | Z-Image-Turbo SDNQ | MPS | 512×512 | 8 | bf16 | ...s | ...GB | ... |
...

## Recommendations

### For 24GB unified memory (M4 Pro, M3 Max, M2 Ultra)
- ...

### For 16GB unified memory (M4, M3 Pro base, M2 Pro)
- ...

### OGA local-server impact
- ...
```

**AC:** AC-1.1d

### Task 8: Report findings cho OGA (30 min)

- Copy key findings vào 1 file: `docs/04-build/oga-recommendations.md`
- Nội dung: optimal torch_dtype, memory management pattern, quantization matrix, slicing config
- Nếu có access OGA repo (`/Users/dttai/Documents/Research/Open-Generative-AI/`): mở PR trực tiếp sửa `local-server/server.py`
- Nếu không: để file report, CTO sẽ chuyển

---

## Cách chạy

```bash
cd /Users/dttai/Documents/Research/ZPix

# Launch app (skip install nếu .venv/mac-ready tồn tại)
./start-mac.sh

# Custom port
PORT=7861 ./start-mac.sh

# Force reinstall (xóa venv cũ)
rm -rf .venv && ./start-mac.sh

# Check git status
git log --oneline -5
git status
```

## Quy ước commit

```
feat(mac): <mô tả feature>     # code mới
fix(mac): <mô tả fix>          # sửa bug
docs(sdlc): <mô tả>            # documentation
test(bench): <mô tả>           # benchmark related
```

## Quy tắc

1. **KHÔNG sửa Windows path** — `start.ps1`, `source/ps/`, `source/cpp/`, `main.cpp` là upstream code, đừng đụng.
2. **KHÔNG thay đổi ADR-001** — `enable_model_cpu_offload(device="mps")` đã quyết định. Nếu phát hiện vấn đề mới → viết ADR-002.
3. **Ghi nhận thật** — nếu 1 config OOM hoặc fail, ghi "FAIL" trong benchmark, đừng bỏ qua.
4. **Commit thường xuyên** — mỗi task xong thì commit, đừng gom hết cuối sprint.
5. **Test trước khi claim done** — mỗi AC cần evidence (screenshot, log output, hoặc file generated).

## Definition of Done (Sprint 002)

- [ ] 11 benchmark configs → valid images, no OOM (hoặc ghi rõ N/A/FAIL nếu không available)
- [ ] FLUX.2-klein-4B, LoRA, i2i confirmed working trên MPS (hoặc documented tại sao fail)
- [ ] Locale warning resolved
- [ ] `docs/04-build/benchmark-results.md` complete với recommendation
- [ ] Findings documented cho OGA

## Khi xong

Chạy:
```bash
endiorbot gate recommend G3
endiorbot compliance check
```

Nếu G3 chưa pass (do thiếu lint/test/coverage — ZPix gốc không có test suite), ghi note và báo CTO để force-confirm.

---

*Handoff từ: CTO review session 2026-05-05*
*Branch: mac-dev-mode @ 31820a2*
*Sprint plan: docs/04-build/sprints/sprint-002-benchmark.md*
*Test plan: docs/05-test/test-plans/tp-001-mps-benchmark.md*
