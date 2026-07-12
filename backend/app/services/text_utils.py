"""Small text helpers shared by exercise and template services."""

import re


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "exercise"
