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
