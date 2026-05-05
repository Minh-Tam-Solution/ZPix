"""Brand template management."""

from pathlib import Path

from pydantic import BaseModel, TypeAdapter


class BrandTemplate(BaseModel):
    """A brand template with style guidelines and example prompts."""

    id: str
    """Brand identifier."""

    name: str
    """Display name."""

    tone: str = ""
    """Brand tone description."""

    style_prefix: str = ""
    """Prefix automatically prepended to prompts."""

    hashtags: list[str] = []
    """Suggested hashtags."""

    do: list[str] = []
    """DO guidelines."""

    dont: list[str] = []
    """DONT guidelines."""

    example_prompts: list[str] = []
    """Example prompts for this brand."""


def get_brand_templates(json_file: Path) -> list[BrandTemplate]:
    """Load brand templates from a JSON file.

    Args:
        json_file: Path to brand_templates.json.

    Returns:
        List of BrandTemplate objects.
    """
    adapter = TypeAdapter(list[BrandTemplate])
    return adapter.validate_json(json_file.read_text(encoding="utf-8"))


def find_brand(brand_id: str, brands: list[BrandTemplate]) -> BrandTemplate:
    """Find a brand by its ID.

    Args:
        brand_id: Brand identifier.
        brands: List of loaded brand templates.

    Returns:
        Matching BrandTemplate or the last brand ("none") if not found.
    """
    return next((b for b in brands if b.id == brand_id), brands[-1])


def find_brand_by_name(name: str, brands: list[BrandTemplate]) -> BrandTemplate:
    """Find a brand by its display name.

    Args:
        name: Display name of the brand.
        brands: List of loaded brand templates.

    Returns:
        Matching BrandTemplate or the last brand ("none") if not found.
    """
    return next((b for b in brands if b.name == name), brands[-1])
