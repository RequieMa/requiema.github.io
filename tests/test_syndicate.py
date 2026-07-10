import sys
from pathlib import Path
import tempfile
import textwrap

# Allow importing scripts/syndicate.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from syndicate import Post, parse_post


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
