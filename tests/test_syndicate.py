import sys
from pathlib import Path
import tempfile
import textwrap

# Allow importing scripts/syndicate.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from syndicate import Post, parse_post, Platform, Route, load_routes, match_platforms


def make_post_file(content: str, dir_name: str = "en") -> Path:
    """Helper: write content to a temp Markdown file, return its path."""
    tmpdir = Path(tempfile.mkdtemp())
    lang_dir = tmpdir / dir_name
    lang_dir.mkdir()
    post_file = lang_dir / "test-post.md"
    post_file.write_text(textwrap.dedent(content), encoding="utf-8")
    return post_file


def test_parse_post_extracts_frontmatter():
    post_file = make_post_file("""\
    ---
    tags:
      - essay
      - control-theory
    categories:
      - en
      - cybernetics
    ---

    # My Test Post

    This is the body content.

    ## Section

    More text here.
    """)

    post = parse_post(post_file)

    assert post.title == "My Test Post"
    assert post.tags == ["essay", "control-theory"]
    assert post.categories == ["en", "cybernetics"]
    assert post.language == "en"
    assert post.slug == "test-post"
    assert "## Section" in post.body
    assert "---" not in post.body  # frontmatter stripped


def test_parse_post_handles_date_created():
    post_file = make_post_file("""\
    ---
    date:
      created: 2026-07-10
    tags:
      - tutorial
    categories:
      - zh
      - python
    ---

    # 中文标题

    正文内容。
    """, dir_name="zh")

    post = parse_post(post_file)

    assert post.language == "zh"
    assert post.tags == ["tutorial"]
    assert "正文内容" in post.body


def test_parse_post_no_frontmatter_raises():
    post_file = make_post_file("""\
    # No frontmatter here

    Just a body.
    """)

    try:
        parse_post(post_file)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "frontmatter" in str(e).lower()


def test_load_routes_parses_config():
    """load_routes reads syndicate.yml and returns Route objects."""
    routes = load_routes()

    assert len(routes) == 4
    assert routes[0].tags == ["essay"]
    assert routes[0].platforms[0].name == "zhihu"
    assert routes[0].platforms[0].language == "zh"


def test_match_platforms_single_tag():
    """A post with one convention tag matches its route group."""
    post = Post(
        title="Test", tags=["essay"], categories=["en"],
        body="", language="en", slug="test", path=Path("dummy")
    )
    routes = load_routes()

    platforms = match_platforms(post, routes)
    names = {(p.name, p.language) for p in platforms}

    assert ("zhihu", "zh") in names
    assert ("gongzhonghao", "zh") in names
    assert ("devto", "en") in names
    assert ("substack", "en") in names


def test_match_platforms_multiple_tags_union():
    """Tags spanning multiple route groups → union of both platform sets."""
    post = Post(
        title="Test", tags=["essay", "tutorial"], categories=["en"],
        body="", language="en", slug="test", path=Path("dummy")
    )
    routes = load_routes()

    platforms = match_platforms(post, routes)
    names = {(p.name, p.language) for p in platforms}

    # essay group: zhihu(zh), gongzhonghao(zh), devto(en), substack(en)
    # tutorial group: juejin(zh), devto(en)
    # Union dedup: devto(en) appears once
    assert ("zhihu", "zh") in names
    assert ("juejin", "zh") in names
    assert ("devto", "en") in names
    # devto(en) should NOT appear twice
    devto_count = sum(1 for p in platforms if p.name == "devto" and p.language == "en")
    assert devto_count == 1


def test_match_platforms_no_match():
    """A post with no convention tags returns empty list."""
    post = Post(
        title="Test", tags=["python", "random-thoughts"], categories=["en"],
        body="", language="en", slug="test", path=Path("dummy")
    )
    routes = load_routes()

    platforms = match_platforms(post, routes)
    assert platforms == []


def test_match_platforms_tag_in_middle_group():
    """Tags in the tutorial group match correctly."""
    post = Post(
        title="Test", tags=["tutorial"], categories=["en"],
        body="", language="en", slug="test", path=Path("dummy")
    )
    routes = load_routes()

    platforms = match_platforms(post, routes)
    names = {(p.name, p.language) for p in platforms}

    assert ("juejin", "zh") in names
    assert ("devto", "en") in names
    assert len(platforms) == 2


from syndicate import find_post_for_language


def test_find_post_for_language_same_language():
    """If post is already in the target language, return it unchanged."""
    post_file = make_post_file("""\
    ---
    tags: [essay]
    ---

    # English Post

    Content.
    """, dir_name="en")
    post = parse_post(post_file)

    result = find_post_for_language(post, "en")
    assert result is not None
    assert result.language == "en"
    assert result.slug == post.slug


def test_find_post_for_language_sibling_exists():
    """If a sibling in the target language exists, return it."""
    tmpdir = Path(tempfile.mkdtemp())
    en_dir = tmpdir / "en"
    zh_dir = tmpdir / "zh"
    en_dir.mkdir()
    zh_dir.mkdir()

    en_path = en_dir / "my-post.md"
    zh_path = zh_dir / "my-post.md"

    en_path.write_text(textwrap.dedent("""\
    ---
    tags: [essay]
    ---

    # English Post
    Content.
    """), encoding="utf-8")

    zh_path.write_text(textwrap.dedent("""\
    ---
    tags: [essay]
    ---

    # 中文文章
    内容。
    """), encoding="utf-8")

    en_post = parse_post(en_path)
    result = find_post_for_language(en_post, "zh")

    assert result is not None
    assert result.language == "zh"
    assert "中文文章" in result.title


def test_find_post_for_language_no_sibling():
    """If no sibling exists, return None."""
    post_file = make_post_file("""\
    ---
    tags: [essay]
    ---

    # Only English

    No Chinese version.
    """, dir_name="en")
    post = parse_post(post_file)

    result = find_post_for_language(post, "zh")
    assert result is None


from syndicate import format_post


CANONICAL_BASE = "https://requiema.github.io/blog"


def test_format_devto_adds_canonical_url():
    """dev.to output includes canonical_url in frontmatter."""
    post = Post(
        title="My Test Post",
        tags=["essay"], categories=["en"],
        body="# My Test Post\n\nSome content.",
        language="en", slug="my-test-post", path=Path("dummy"),
    )
    platform = Platform(name="devto", language="en")

    output = format_post(post, platform, CANONICAL_BASE)

    assert "canonical_url: https://requiema.github.io/blog/my-test-post/" in output
    assert "Some content." in output


def test_format_substack_same_as_devto():
    """Substack uses the same format as dev.to."""
    post = Post(
        title="Test", tags=["essay"], categories=["en"],
        body="# Test\n\nBody.",
        language="en", slug="test", path=Path("dummy"),
    )
    devto_out = format_post(post, Platform(name="devto", language="en"), CANONICAL_BASE)
    substack_out = format_post(post, Platform(name="substack", language="en"), CANONICAL_BASE)

    assert devto_out == substack_out


def test_format_gongzhonghao_adds_warning():
    """公众号 output includes a reminder about rich-text conversion."""
    post = Post(
        title="Test", tags=["essay"], categories=["zh"],
        body="# 测试\n\n正文内容。",
        language="zh", slug="test", path=Path("dummy"),
    )
    platform = Platform(name="gongzhonghao", language="zh")

    output = format_post(post, platform, CANONICAL_BASE)

    assert "markdown.com.cn" in output
    assert "正文内容" in output


def test_format_x_short_tweet():
    """X/Twitter: title + first paragraph + link."""
    post = Post(
        title="My Post",
        tags=["release"], categories=["en"],
        body="# My Post\n\nA quick announcement.",
        language="en", slug="my-post", path=Path("dummy"),
    )
    platform = Platform(name="x", language="en")

    output = format_post(post, platform, CANONICAL_BASE)

    assert "My Post" in output
    assert "A quick announcement" in output
    assert "🔗 https://requiema.github.io/blog/my-post/" in output


def test_format_x_truncates_long_tweet():
    """X/Twitter: truncates to ≤ 280 characters."""
    post = Post(
        title="A Very Long Post Title",
        tags=["release"], categories=["en"],
        body="# A Very Long Post Title\n\n" + ("Very long sentence. " * 30),
        language="en", slug="long-post", path=Path("dummy"),
    )
    platform = Platform(name="x", language="en")

    output = format_post(post, platform, CANONICAL_BASE)

    assert len(output) <= 280


def test_format_passthrough_platforms():
    """Zhihu, Juejin, Yuque get the raw body as-is."""
    post = Post(
        title="Test", tags=["tutorial"], categories=["zh"],
        body="# 测试\n\n正文。",
        language="zh", slug="test", path=Path("dummy"),
    )

    for name in ("zhihu", "juejin", "yuque"):
        platform = Platform(name=name, language="zh")
        output = format_post(post, platform, CANONICAL_BASE)
        assert output == post.body, f"{name} should be passthrough"


import subprocess


def test_cli_single_post_generates_files():
    """End-to-end: run syndicate.py on the real blog post, verify output."""
    repo_root = Path(__file__).resolve().parent.parent
    post_path = repo_root / "docs/blog/posts/en/setting-up-this-blog.md"

    if not post_path.exists():
        # Skip if the post doesn't exist (shouldn't happen, but be safe)
        return

    # Run the script
    result = subprocess.run(
        ["uv", "run", "python", "scripts/syndicate.py", str(post_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Should exit cleanly
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Should print the post slug
    assert "setting-up-this-blog" in result.stdout


def test_cli_nonexistent_file():
    """Passing a non-existent file should exit with error."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/syndicate.py", "nonexistent.md"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
