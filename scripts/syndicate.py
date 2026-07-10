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


# ---------------------------------------------------------------------------
# Platform formatters
# ---------------------------------------------------------------------------

PASSTHROUGH_PLATFORMS = {"zhihu", "juejin", "yuque"}


def format_post(post: Post, platform: Platform, canonical_base: str) -> str:
    """Format a post for a specific platform.

    Args:
        post: The parsed post (in the correct language for the platform).
        platform: The target platform with language preference.
        canonical_base: Base URL for canonical links (e.g. https://requiema.github.io/blog).

    Returns:
        Formatted Markdown string for the platform.
    """
    canonical_url = f"{canonical_base}/{post.slug}/"

    if platform.name in ("devto", "substack"):
        return _format_with_canonical(post, canonical_url)
    elif platform.name == "gongzhonghao":
        return _format_gongzhonghao(post)
    elif platform.name == "x":
        return _format_x(post, canonical_url)
    else:
        # Passthrough: zhihu, juejin, yuque
        return post.body


def _format_with_canonical(post: Post, canonical_url: str) -> str:
    """Format for dev.to / Substack: add canonical_url frontmatter."""
    lines = [
        "---",
        f"title: \"{post.title}\"",
        f"canonical_url: {canonical_url}",
        "---",
        "",
        post.body,
    ]
    return "\n".join(lines)


def _format_gongzhonghao(post: Post) -> str:
    """Format for 公众号: prepend rich-text conversion reminder."""
    lines = [
        "<!-- 公众号只支持富文本，请用 https://markdown.com.cn 转成富文本后粘贴 -->",
        "",
        post.body,
    ]
    return "\n".join(lines)


def _format_x(post: Post, canonical_url: str) -> str:
    """Format for X/Twitter: title + first paragraph + link, ≤ 280 chars."""
    # Extract first non-heading paragraph as summary
    paragraphs = [
        p for p in post.body.split("\n\n")
        if p.strip() and not p.strip().startswith("#")
    ]
    summary = paragraphs[0].strip() if paragraphs else ""

    tweet = f"{post.title}\n\n{summary}\n\n🔗 {canonical_url}"

    if len(tweet) <= 280:
        return tweet

    # Truncate at the last full sentence before the limit
    truncated = tweet[:277] + "..."
    return truncated


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("_syndication")


def write_output(slug: str, platform_name: str, language: str, content: str) -> Path:
    """Write syndicated content to _syndication/{slug}/{platform}-{lang}.md.

    Args:
        slug: Post slug (filename stem).
        platform_name: 'devto', 'zhihu', etc.
        language: 'en' or 'zh'.
        content: The formatted Markdown string.

    Returns:
        Path to the written file.
    """
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{platform_name}-{language}.md"
    out_path = out_dir / filename
    out_path.write_text(content, encoding="utf-8")
    return out_path


def find_all_posts() -> list[Path]:
    """Find all unique blog posts (deduplicated by filename stem).

    Prefers the en/ version when both en/ and zh/ exist.
    """
    posts_dir = Path("docs/blog/posts")
    seen: set[str] = set()
    posts: list[Path] = []

    for md_file in sorted(posts_dir.rglob("*.md")):
        if md_file.stem in seen:
            continue
        seen.add(md_file.stem)
        posts.append(md_file)

    return posts


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

CANONICAL_BASE = "https://requiema.github.io/blog"


def process_post(filepath: Path, routes: list[Route]) -> None:
    """Process a single blog post: match platforms, format, write output.

    Args:
        filepath: Path to the post Markdown file.
        routes: Route definitions from syndicate.yml.
    """
    post = parse_post(filepath)
    platforms = match_platforms(post, routes)

    print(f"📄 {post.slug}")

    if not platforms:
        print("   💡 无同步目标。请在 frontmatter 的 tags 中添加约定标签: "
              "essay / tutorial / guide / howto / release / launch / book / notes")
        return

    for p in platforms:
        # Find the right language version
        target_post = find_post_for_language(post, p.language)
        if target_post is None:
            print(f"   ⚠️  没有 {p.language} 语言版本，使用 {post.language} 版本代替")
            target_post = post

        content = format_post(target_post, p, CANONICAL_BASE)
        out_path = write_output(target_post.slug, p.name, p.language, content)
        print(f"   ✅ {out_path}")


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Blog syndication helper — generate platform-formatted copies of posts."
    )
    parser.add_argument(
        "post_path", nargs="?",
        help="Path to a blog post (e.g., docs/blog/posts/en/my-post.md)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all blog posts"
    )

    args = parser.parse_args()

    if not args.post_path and not args.all:
        parser.print_help()
        return

    routes = load_routes()

    if args.all:
        posts = find_all_posts()
        if not posts:
            print("📭 没有找到任何博客文章。")
            return
        for post_path in posts:
            process_post(post_path, routes)
            print()
    else:
        filepath = Path(args.post_path)
        if not filepath.exists():
            print(f"❌ 文件不存在: {filepath}")
            raise SystemExit(1)
        process_post(filepath, routes)


if __name__ == "__main__":
    main()
