# Coder Handoff: ZPix Sprint 004 — Brand Templates

> **Mục đích file này:** Prompt handoff cho @coder session mới trên Kimi CLI.
> Copy toàn bộ nội dung này vào prompt đầu tiên của session mới tại `/Users/dttai/Documents/Research/ZPix/`.

---

## Bạn là ai

Bạn là **Coder** của dự án ZPix — offline AI image generation client cho 149 nhân viên NQH. Sprint 004 thêm **brand templates** — nhân viên chọn brand (BKL Coffee, Thơm F&B, AirDream, Kupid, LHP) và prompt được pre-fill với tone, style, DO/DONT của brand đó.

---

## Trạng thái hiện tại (2026-05-05)

### Repo
- **Path:** `/Users/dttai/Documents/Research/ZPix/`
- **Branch:** `mac-dev-mode` (15 commits ahead of `main`, commit `709ac05`)
- **Remote:** https://github.com/Minh-Tam-Solution/ZPix

### Hoàn thành ✅
- Sprint 001: Mac dev mode (start-mac.sh, MPS patch)
- Sprint 002: Benchmark (9/9 configs PASS, LoRA/i2i/FLUX validated)
- Sprint 003: Tauri `.app` scaffold, Python sidecar, offline detection, model cache
- Gates G0→G3 CONFIRMED

### Sprint 004 scope (bạn làm)
- User story: **US-2.3 (Brand Templates)**
- Acceptance criteria: **AC-2.3a** (brand config loaded from JSON), hiệu chỉnh cho phù hợp thực tế

---

## CTO notes từ Sprint 003 review

2 issues cần fix trong Sprint 004 (hoặc trước khi ship):

1. **Orphan Python process on quit** — `src-tauri/src/main.rs:119-125`: `child.kill()` chỉ kill bash, không kill grandchild Python. Fix: dùng process group kill. Tùy bạn fix trong sprint này hay tách task riêng.

2. **`current_dir()` vs `.app` bundle path** — `main.rs:10`: khi chạy từ `.app` bundle, `current_dir()` có thể không phải repo root. Fix: dùng `std::env::current_exe().unwrap().parent()` hoặc `app.path().resource_dir()`.

---

## Kiến trúc hiện tại

```
ZPix.app (Tauri / WKWebView)
  └─► start-mac.sh (env: PORT, HF_HOME, ZPIX_OFFLINE)
       └─► uv run app.py --port 7860 [--offline] --locale en-US
            └─► Gradio UI @ http://127.0.0.1:7860
```

### File quan trọng cho Sprint 004

| File | Vai trò | Sửa? |
|------|---------|------|
| `data/curated_models.json` | 2 model definitions | Đọc, không sửa |
| `data/example_prompts.json` | Example prompts hiển thị trong Gradio | Tham khảo pattern |
| `source/py/ex_prompts.py` | Load example prompts từ JSON | Tham khảo pattern |
| `app.py:890-898` | `gr.Examples` widget hiện tại | Mở rộng hoặc thêm brand selector |
| `app.py:428-433` | CLI args (`--port`, `--locale`, `--offline`) | Có thể thêm `--brand-dir` |
| `translations/fr-FR.json` | Translation pattern (flat JSON key→value) | Tham khảo i18n |

### Existing data patterns

**`data/example_prompts.json`:**
```json
[
  {"text": "A hyper-realistic close-up portrait...", "source": "https://..."},
  ...
]
```

**`source/py/ex_prompts.py`:**
```python
def get_example_prompts(json_file: Path) -> list[str]:
    prompts = json.loads(json_file.read_text(encoding="utf-8"))
    return [prompt["text"] for prompt in prompts]
```

Gradio loads these as clickable examples. Brand templates follow the same pattern nhưng mở rộng với brand metadata.

---

## 7 tasks Sprint 004

### Task 1: Thiết kế brand template schema (30 min)

**Tạo `data/brand_templates.json`:**

```json
[
  {
    "id": "bkl-coffee",
    "name": "BKL Coffee",
    "tone": "Warm, cozy, premium. Vietnamese specialty coffee culture.",
    "style_prefix": "professional photography, warm lighting, coffee shop ambiance",
    "hashtags": ["#BKLCoffee", "#CaPheVietNam", "#NQH"],
    "do": [
      "Use warm brown/gold color palette",
      "Show people enjoying coffee moments",
      "Highlight Vietnamese coffee culture"
    ],
    "dont": [
      "No competitor brand logos",
      "No cold/clinical lighting",
      "No generic stock photo style"
    ],
    "example_prompts": [
      "A barista pouring Vietnamese egg coffee in a cozy BKL Coffee shop, warm golden light, professional food photography",
      "Close-up of a traditional phin filter dripping dark coffee into a glass of condensed milk, rustic wooden table, warm tones"
    ]
  },
  {
    "id": "thom-fnb",
    "name": "Thơm F&B",
    "tone": "Fresh, vibrant, youthful. Modern Vietnamese cuisine.",
    "style_prefix": "bright natural lighting, food photography, fresh ingredients",
    "hashtags": ["#ThomFnB", "#AmThucViet", "#NQH"],
    "do": [
      "Bright, appetizing food styling",
      "Show fresh ingredients and preparation",
      "Vietnamese fusion modern aesthetic"
    ],
    "dont": [
      "No dark/moody food photography",
      "No messy plating",
      "No fast food appearance"
    ],
    "example_prompts": [
      "A beautifully plated Vietnamese pho bowl with fresh herbs, lime, and chili, bright natural window light, overhead shot",
      "Chef hands preparing banh mi with colorful fresh vegetables, bright kitchen, action shot, professional food photography"
    ]
  },
  {
    "id": "airdream",
    "name": "AirDream",
    "tone": "Luxurious, aspirational, serene. Premium hospitality and travel.",
    "style_prefix": "luxury lifestyle photography, soft elegant lighting, aspirational",
    "hashtags": ["#AirDream", "#LuxuryTravel", "#NQH"],
    "do": [
      "Luxury resort/hotel imagery",
      "Serene, aspirational landscapes",
      "Premium material textures (silk, marble, wood)"
    ],
    "dont": [
      "No budget/backpacker aesthetic",
      "No crowded tourist scenes",
      "No harsh lighting"
    ],
    "example_prompts": [
      "A serene infinity pool overlooking misty Vietnamese mountains at sunrise, luxury resort, drone view, golden hour",
      "Elegant hotel room interior with silk curtains, tropical flowers, and ocean view balcony, soft natural light"
    ]
  },
  {
    "id": "kupid",
    "name": "Kupid",
    "tone": "Playful, romantic, trendy. Modern dating and social lifestyle.",
    "style_prefix": "trendy lifestyle photography, vibrant colors, social media aesthetic",
    "hashtags": ["#Kupid", "#DatingVN", "#NQH"],
    "do": [
      "Vibrant, Instagram-worthy aesthetic",
      "Young couples and social scenes",
      "Trendy urban Vietnamese settings"
    ],
    "dont": [
      "No overly formal/corporate imagery",
      "No explicit or suggestive content",
      "No lonely/isolated scenes"
    ],
    "example_prompts": [
      "A young Vietnamese couple sharing boba tea at a trendy Saigon cafe, colorful neon signs, candid shot, warm evening light",
      "Group of friends laughing at a rooftop bar with city skyline at sunset, lifestyle photography, vibrant colors"
    ]
  },
  {
    "id": "lhp",
    "name": "LHP",
    "tone": "Professional, trustworthy, innovative. Corporate and technology.",
    "style_prefix": "corporate professional photography, clean modern aesthetic",
    "hashtags": ["#LHP", "#Innovation", "#NQH"],
    "do": [
      "Clean, modern corporate imagery",
      "Technology and innovation themes",
      "Professional team collaboration"
    ],
    "dont": [
      "No casual/informal settings",
      "No outdated technology",
      "No cluttered backgrounds"
    ],
    "example_prompts": [
      "Modern open office with Vietnamese professionals collaborating around a digital whiteboard, natural light, clean aesthetic",
      "Close-up of hands typing on a sleek laptop with data visualizations on screen, shallow depth of field, blue accent lighting"
    ]
  },
  {
    "id": "none",
    "name": "No Brand (Free Style)",
    "tone": "",
    "style_prefix": "",
    "hashtags": [],
    "do": [],
    "dont": [],
    "example_prompts": []
  }
]
```

**Lưu ý:** Schema này là đề xuất — bạn có thể điều chỉnh fields. Core requirement: `id`, `name`, `style_prefix`, `example_prompts`.

### Task 2: Tạo brand template loader (30 min)

**Tạo `source/py/brand_template.py`:**

```python
"""Brand template management."""
from pathlib import Path
from pydantic import BaseModel

class BrandTemplate(BaseModel):
    id: str
    name: str
    tone: str = ""
    style_prefix: str = ""
    hashtags: list[str] = []
    do: list[str] = []
    dont: list[str] = []
    example_prompts: list[str] = []

def get_brand_templates(json_file: Path) -> list[BrandTemplate]:
    """Load brand templates from JSON file."""
    from pydantic import TypeAdapter
    adapter = TypeAdapter(list[BrandTemplate])
    return adapter.validate_json(json_file.read_text(encoding="utf-8"))

def find_brand(brand_id: str, brands: list[BrandTemplate]) -> BrandTemplate:
    """Find brand by ID. Returns 'none' brand if not found."""
    return next((b for b in brands if b.id == brand_id), brands[-1])
```

Pattern giống `image_models.py` — Pydantic TypeAdapter + JSON file.

### Task 3: Thêm brand selector vào Gradio UI (1-2h)

**Sửa `app.py`** — thêm dropdown brand selector. Vị trí: trước hoặc sau model selector.

Khi user chọn brand:
1. `style_prefix` prepend vào prompt (ẩn, tự động)
2. `example_prompts` thay thế `gr.Examples` widget
3. Brand DO/DONT hiển thị dưới dạng info box (collapsible)

**Pseudo-code integration:**
```python
# Trong app.py, sau khi load models:
brands = get_brand_templates(app_dir / "data" / "brand_templates.json")
brand_names = [b.name for b in brands]

# Gradio UI:
brand_select = gr.Dropdown(choices=brand_names, value="No Brand (Free Style)", label=t("Brand"))

# Khi generate, prepend style_prefix:
def generate_with_brand(prompt, brand_name, ...):
    brand = find_brand_by_name(brand_name, brands)
    full_prompt = f"{brand.style_prefix}, {prompt}" if brand.style_prefix else prompt
    # ... rest of generation logic
```

**Quan trọng:**
- `style_prefix` prepend vào prompt trước khi gửi cho pipeline, KHÔNG sửa prompt visible cho user
- User vẫn có thể type bất kỳ prompt nào — brand chỉ là prefix tự động
- "No Brand (Free Style)" = không prepend gì, giữ behavior gốc 100%

### Task 4: Brand-aware example prompts (30 min)

Khi user đổi brand → `gr.Examples` widget update hiển thị example prompts của brand đó.

Nếu brand = "No Brand" → hiển thị example prompts gốc từ `data/example_prompts.json` (giữ behavior cũ).

### Task 5: Brand guidelines info box (30 min)

Thêm `gr.Accordion` (collapsible) hiển thị:
- **Tone:** `brand.tone`
- **DO:** bulleted list
- **DONT:** bulleted list

Chỉ hiển thị khi brand != "No Brand". Collapsed by default (không chiếm space).

### Task 6: Test brand selector end-to-end (1h)

Test scenarios:
1. Chọn "BKL Coffee" → prompt prefixed → ảnh ra style warm/coffee
2. Chọn "No Brand" → prompt không prefixed → ảnh style tự do
3. Đổi brand giữa chừng → example prompts update
4. Brand DO/DONT hiển thị đúng
5. Generate ảnh với mỗi brand ít nhất 1 lần

### Task 7: Commit + update sprint docs (15 min)

Sprint doc: `docs/04-build/sprints/sprint-004-brand-templates.md`
Commit convention: `feat(brand): <description>`

---

## Cách chạy

```bash
cd /Users/dttai/Documents/Research/ZPix

# Dev mode (không cần Tauri)
./start-mac.sh

# Tauri dev (native app)
npm run dev

# Tauri build (.app bundle)
npm run build
```

## Quy ước commit

```
feat(brand): add brand template schema + loader
feat(brand): add brand selector to Gradio UI
feat(brand): brand-aware example prompts
docs(sdlc): Sprint 004 brand templates complete
```

## Quy tắc

1. **KHÔNG sửa Windows path** — `start.ps1`, `source/ps/`, `source/cpp/`, `main.cpp` đừng đụng.
2. **KHÔNG sửa model loading logic** — `load_model()` trong app.py đã stable (ADR-001). Brand prefix chỉ sửa prompt, KHÔNG sửa pipeline.
3. **Giữ "No Brand" as default** — behavior gốc 100% unchanged khi không chọn brand.
4. **Pydantic cho schema validation** — follow pattern của `image_model.py` / `image_models.py`.
5. **Commit thường xuyên** — mỗi task xong thì commit.

## Acceptance Criteria

| AC | Criterion | Verify |
|----|-----------|--------|
| AC-2.3a | Brand config loaded from local JSON | `data/brand_templates.json` parsed, dropdown shows 6 brands |
| AC-2.3a+ | Prompt pre-filled with brand style_prefix | Generate → check prompt sent to pipeline includes prefix |
| AC-2.3a++ | Brand DO/DONT displayed | Accordion shows correct guidelines per brand |
| AC-2.3b-defer | Templates sync from Postiz workspace when online | **DEFERRED to Sprint 005** — Postiz API chưa sẵn sàng |

## Definition of Done

- [ ] `data/brand_templates.json` với 5 brands + "No Brand"
- [ ] `source/py/brand_template.py` loader (Pydantic)
- [ ] Brand dropdown trong Gradio UI
- [ ] style_prefix auto-prepend khi generate
- [ ] Brand example prompts thay thế khi đổi brand
- [ ] Brand guidelines accordion (collapsible)
- [ ] Test: generate 1 ảnh/brand, ảnh phản ánh brand tone

## Khi xong

```bash
git push origin mac-dev-mode
endiorbot compliance check
endiorbot gate status
```

Báo CTO review.

---

*Handoff từ: CTO review Sprint 003 (2026-05-05)*
*Branch: mac-dev-mode @ 709ac05*
*User story: US-2.3 (Brand Templates)*
*AC: AC-2.3a (partial — sync deferred to Sprint 005)*
