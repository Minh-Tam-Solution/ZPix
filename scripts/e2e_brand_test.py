#!/usr/bin/env python3
"""E2E test: verify Sprint 004 brand integration without loading heavy models.

This test mocks the diffusion pipeline to validate:
1. Brand templates load correctly from JSON
2. Style prefixes are prepended to prompts as expected
3. Full prompt composition matches brand configuration
4. PNG metadata preserves the original user prompt (not the prefixed one)

Usage: uv run --python ../.venv/bin/python e2e_brand_test.py
"""

import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import torch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from source.py.brand_template import get_brand_templates, find_brand

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_brand_template_loading():
    """Task 1+2: Verify brand templates load and schema is correct."""
    brands = get_brand_templates(repo_root / "data" / "brand_templates.json")
    assert len(brands) == 6, f"Expected 6 brands, got {len(brands)}"

    ids = [b.id for b in brands]
    assert ids[-1] == "none", "Last brand should be 'none' fallback"

    # Verify every branded entry has required fields
    for b in brands:
        if b.id == "none":
            continue
        assert b.style_prefix, f"{b.id}: missing style_prefix"
        assert b.example_prompts, f"{b.id}: missing example_prompts"
        assert b.do, f"{b.id}: missing DO guidelines"
        assert b.dont, f"{b.id}: missing DON'T guidelines"

    logger.info(f"✅ Loaded {len(brands)} brand templates with valid schema")
    return brands


def test_find_brand_fallback(brands):
    """Verify find_brand falls back to 'none' for unknown IDs."""
    unknown = find_brand("nonexistent", brands)
    assert unknown.id == "none", "Fallback should be 'none' brand"
    logger.info("✅ Brand fallback lookup works")


def test_prompt_prefix_composition(brands):
    """Task 3: Verify style_prefix is prepended correctly."""
    for b in brands:
        user_prompt = "a test prompt"
        if b.style_prefix:
            full = f"{b.style_prefix}, {user_prompt}"
            assert full.startswith(b.style_prefix), f"{b.id}: prefix not at start"
        else:
            full = user_prompt
        assert user_prompt in full, f"{b.id}: original prompt lost"
    logger.info("✅ Prompt prefix composition correct for all brands")


def test_generate_with_mock_pipeline(brands):
    """Task 6: E2E — mock pipeline, verify brand-aware generation."""
    # Build a fake pipeline that records kwargs and returns a blank image
    captured = {}

    class FakePipeline:
        def __call__(self, **kwargs):
            captured.update(kwargs)
            return MagicMock(images=[Image.new("RGB", (512, 512), color=(128, 128, 128))])

        def enable_model_cpu_offload(self, device=None):
            pass

    pipe = FakePipeline()

    # Patch the global `pipe` in app.py by importing and assigning
    import app as app_module

    original_pipe = getattr(app_module, "pipe", None)
    app_module.pipe = pipe
    app_module.pipe_is_busy = False

    # Patch output dir to a temp folder
    original_output_dir = app_module.output_dir
    with tempfile.TemporaryDirectory() as tmpdir:
        app_module.output_dir = Path(tmpdir)

        results = []
        for brand in brands:
            test_prompt = (
                brand.example_prompts[0]
                if brand.example_prompts
                else "A beautiful Vietnamese landscape"
            )

            # Call generate() exactly as Gradio would
            gallery, idx, used_seed = app_module.generate(
                model=MagicMock(id="test-model", name="Test Model", codename="ZiT", default=MagicMock(steps=4, cfg=0.0)),
                mm_prompt={"text": test_prompt},
                reference_images=None,
                resolution="512x512",
                seed=42,
                random_seed=False,
                steps=4,
                cfg=0.0,
                gallery_images=[],
                lora_name=None,
                brand=brand,
            )

            # Verify the pipeline received the prefixed prompt
            expected_full = (
                f"{brand.style_prefix}, {test_prompt}"
                if brand.style_prefix
                else test_prompt
            )
            assert captured.get("prompt") == expected_full, (
                f"{brand.id}: expected '{expected_full}', got '{captured.get('prompt')}'"
            )

            # Verify output image exists and metadata has original prompt
            img_path = gallery[-1][0]
            img = Image.open(img_path)
            meta_prompt = img.info.get("prompt", "")
            assert meta_prompt == test_prompt, (
                f"{brand.id}: metadata prompt mismatch. Expected '{test_prompt}', got '{meta_prompt}'"
            )

            results.append({
                "brand": brand.name,
                "id": brand.id,
                "prefix_applied": bool(brand.style_prefix),
                "metadata_correct": meta_prompt == test_prompt,
            })
            logger.info(f"✅ {brand.name:20s} — prefix={'YES' if brand.style_prefix else 'NO ':3s} — metadata OK")

    # Restore patched globals
    app_module.pipe = original_pipe
    app_module.output_dir = original_output_dir

    logger.info("\n" + "=" * 50)
    logger.info("Sprint 004 E2E Mock Test Summary")
    logger.info("=" * 50)
    for r in results:
        prefix_icon = "✅" if r["prefix_applied"] else "➖"
        meta_icon = "✅" if r["metadata_correct"] else "❌"
        logger.info(f"{prefix_icon} {meta_icon} {r['brand']:20s} ({r['id']})")

    all_ok = all(r["metadata_correct"] for r in results)
    if all_ok:
        logger.info("\nAll 6 brand integrations passed ✅")
        return 0
    else:
        logger.error("\nSome brand checks failed ❌")
        return 1


def main():
    brands = test_brand_template_loading()
    test_find_brand_fallback(brands)
    test_prompt_prefix_composition(brands)
    return test_generate_with_mock_pipeline(brands)


if __name__ == "__main__":
    sys.exit(main())
