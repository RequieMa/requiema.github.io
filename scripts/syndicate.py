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
class Platform:
    """A syndication target platform with language preference."""
    name: str       # 'devto', 'zhihu', 'juejin', etc.
    language: str   # 'en' or 'zh'


@dataclass
class Route:
    """A routing rule: tags → list of platforms."""
    tags: list[str]
    platforms: list[Platform]


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


def load_routes(config_path: Path | None = None) -> list[Route]:
    """Load routing configuration from syndicate.yml.

    Args:
        config_path: Path to syndicate.yml. If None, resolves relative to this script.

    Returns:
        List of Route objects in config order.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "syndicate.yml"

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    routes = []
    for entry in data["routes"]:
        platforms = [Platform(name=p["name"], language=p["language"])
                     for p in entry["platforms"]]
        routes.append(Route(tags=entry["tags"], platforms=platforms))
    return routes


def match_platforms(post: Post, routes: list[Route]) -> list[Platform]:
    """Find all platforms this post should be syndicated to.

    Iterates all route groups. Any group whose tags intersect the post's
    tags contributes its platforms. Results are deduplicated by (name, language).

    Args:
        post: The parsed blog post.
        routes: Route definitions from syndicate.yml.

    Returns:
        List of Platform objects (deduplicated, preserving first-match order).
    """
    matched: dict[tuple[str, str], Platform] = {}

    for route in routes:
        if any(tag in post.tags for tag in route.tags):
            for p in route.platforms:
                key = (p.name, p.language)
                if key not in matched:
                    matched[key] = p

    return list(matched.values())


def find_post_for_language(post: Post, target_lang: str) -> Post | None:
    """Find the version of this post in the target language.

    Given a post at en/my-post.md, check if zh/my-post.md exists (and vice versa).

    Args:
        post: A parsed post.
        target_lang: 'en' or 'zh' — the desired language.

    Returns:
        A parsed Post in the target language, or None if no such version exists.
    """
    if post.language == target_lang:
        return post

    other_lang_dir = post.path.parent.parent / target_lang
    other_path = other_lang_dir / post.path.name

    if other_path.exists():
        return parse_post(other_path)

    return None
