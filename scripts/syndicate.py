#!/usr/bin/env python3
"""Blog syndication helper — generates platform-formatted copies of posts.

Usage:
    python scripts/syndicate.py docs/blog/posts/en/my-post.md
    python scripts/syndicate.py --all
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Post:
    """A parsed blog post."""
    title: str
    tags: list[str]
    categories: list[str]
    body: str       # Markdown body without frontmatter
    language: str   # 'en' or 'zh', derived from parent directory
    slug: str       # filename stem
    path: Path      # original file path


def parse_post(filepath: Path) -> Post:
    """Parse a Markdown file with YAML frontmatter into a Post.

    Args:
        filepath: Path to a .md file under docs/blog/posts/{en,zh}/

    Returns:
        Post with extracted metadata and body.

    Raises:
        ValueError: If the file has no YAML frontmatter or is malformed.
    """
    text = filepath.read_text(encoding="utf-8")

    if not text.startswith("---"):
        raise ValueError(f"No frontmatter found in {filepath}")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed frontmatter in {filepath}")

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()

    language = filepath.parent.name  # 'en' or 'zh'
    slug = filepath.stem

    # Extract title from first heading in body
    title = slug
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped.lstrip("#").strip()
            break

    return Post(
        title=title,
        tags=frontmatter.get("tags", []),
        categories=frontmatter.get("categories", []),
        body=body,
        language=language,
        slug=slug,
        path=filepath,
    )
