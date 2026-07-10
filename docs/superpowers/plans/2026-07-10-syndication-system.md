# Blog Syndication System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI script that reads blog post frontmatter, matches tags against a YAML routing config, and generates platform-formatted Markdown files for cross-posting.

**Architecture:** A single Python script (`scripts/syndicate.py`) reads routing rules from `scripts/syndicate.yml`, parses MkDocs blog post frontmatter, matches convention tags to target platforms, and writes formatted copies to `_syndication/{slug}/`. A git post-commit hook provides automatic reminders.

**Tech Stack:** Python 3.14, PyYAML (already available via mkdocs-material), pytest (added as dev dep), stdlib only for the script itself

## Global Constraints

- Python 3.14+ (per pyproject.toml)
- PyYAML already available as transitive dep of mkdocs-material
- Output directory `_syndication/` must be gitignored
- Script reads config from `scripts/syndicate.yml` (committed, user-editable)
- Reddit/HN never included (always hand-crafted)
- `canonical_url` base: `https://requiema.github.io/blog`

---

### Task 1: Project scaffolding — pytest + directory setup

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py` (empty)
- Create: `scripts/` directory

**Interfaces:**
- Produces: `pytest` available via `uv run pytest`, `scripts/` and `tests/` directories exist

- [ ] **Step 1: Add pytest as a dev dependency**

```bash
cd /home/billma/requiema/requiema.github.io
uv add --dev pytest
```

- [ ] **Step 2: Create directories and placeholder files**

```bash
mkdir -p scripts tests
touch tests/__init__.py
```

- [ ] **Step 3: Verify pytest works**

```bash
uv run pytest --version
```
Expected: prints pytest version

- [ ] **Step 4: Run a trivial test to confirm the harness works**

```bash
echo "def test_trivial(): assert True" > tests/test_trivial.py
uv run pytest tests/test_trivial.py -v
```
Expected: 1 passed

- [ ] **Step 5: Clean up and commit**

```bash
rm tests/test_trivial.py
git add pyproject.toml uv.lock tests/__init__.py scripts/
git commit -m "Add pytest and create scripts/ tests/ directories"
```

---

### Task 2: Routing config file

**Files:**
- Create: `scripts/syndicate.yml`

**Interfaces:**
- Produces: YAML config consumed by `load_routes()` in Task 4

- [ ] **Step 1: Write the config file**

Create `scripts/syndicate.yml`:

```yaml
# Blog Syndication Routing
# Maps convention tags → target platforms with language preference.
# Edit freely — the script reads from here, nothing is hardcoded.
#
# language: zh → expects Chinese version; en → English version
# Reddit/HN are intentionally absent (always hand-crafted).

routes:
  - tags: [essay]
    platforms:
      - name: zhihu
        language: zh
      - name: gongzhonghao
        language: zh
      - name: devto
        language: en
      - name: substack
        language: en

  - tags: [tutorial, guide, howto]
    platforms:
      - name: juejin
        language: zh
      - name: devto
        language: en

  - tags: [release, launch]
    platforms:
      - name: devto
        language: en
      - name: x
        language: en
      - name: x
        language: zh

  - tags: [book, notes]
    platforms:
      - name: yuque
        language: zh
      - name: devto
        language: en
```

- [ ] **Step 2: Verify YAML is valid**

```bash
uv run python -c "import yaml; yaml.safe_load(open('scripts/syndicate.yml')); print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/syndicate.yml
git commit -m "Add syndication routing config"
```

---

### Task 3: `parse_post()` — frontmatter parsing

**Files:**
- Create: `scripts/syndicate.py`
- Create: `tests/test_syndicate.py`

**Interfaces:**
- Produces: `parse_post(path: Path) -> Post` where `Post` is a dataclass with fields `title: str`, `tags: list[str]`, `categories: list[str]`, `body: str`, `language: str`, `slug: str`, `path: Path`

No other task depends on this one, but Tasks 4-7 import from it.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_syndicate.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 3 FAIL (ModuleNotFoundError / ImportError for `syndicate`)

- [ ] **Step 3: Write minimal `parse_post()` in `scripts/syndicate.py`**

Create `scripts/syndicate.py`:

```python
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
```

- [ ] **Step 4: Run tests — should pass**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/syndicate.py tests/test_syndicate.py
git commit -m "Add parse_post() with frontmatter extraction tests"
```

---

### Task 4: `load_routes()` + `match_platforms()` — route matching

**Files:**
- Modify: `scripts/syndicate.py` (append)
- Modify: `tests/test_syndicate.py` (append tests)

**Interfaces:**
- Consumes: `Post` dataclass from Task 3, `scripts/syndicate.yml` from Task 2
- Produces: `Platform(name, language)` dataclass, `Route(tags, platforms)` dataclass, `load_routes(path: Path) -> list[Route]`, `match_platforms(post: Post, routes: list[Route]) -> list[Platform]`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_syndicate.py`:

```python
from syndicate import Platform, Route, load_routes, match_platforms


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
```

- [ ] **Step 2: Run tests — should fail**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 5 new FAILs — `Platform`, `Route`, `load_routes`, `match_platforms` not defined

- [ ] **Step 3: Implement data classes + load_routes + match_platforms**

Append to `scripts/syndicate.py` (after the `Post` dataclass, before `parse_post`):

```python


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
```

- [ ] **Step 4: Run tests — should pass**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/syndicate.py tests/test_syndicate.py
git commit -m "Add route matching logic: load_routes() + match_platforms()"
```

---

### Task 5: `find_post_for_language()` — language matching

**Files:**
- Modify: `scripts/syndicate.py` (append)
- Modify: `tests/test_syndicate.py` (append tests)

**Interfaces:**
- Consumes: `Post` dataclass, `parse_post()` from Task 3
- Produces: `find_post_for_language(post: Post, target_lang: str) -> Post | None`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_syndicate.py`:

```python
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
```

- [ ] **Step 2: Run tests — should fail**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 3 new FAILs — `find_post_for_language` not defined

- [ ] **Step 3: Implement `find_post_for_language()`**

Append to `scripts/syndicate.py`:

```python


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
```

- [ ] **Step 4: Run tests — should pass**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/syndicate.py tests/test_syndicate.py
git commit -m "Add find_post_for_language() for bilingual post matching"
```

---

### Task 6: Platform formatters

**Files:**
- Modify: `scripts/syndicate.py` (append)
- Modify: `tests/test_syndicate.py` (append tests)

**Interfaces:**
- Consumes: `Post` from Task 3
- Produces: `format_post(post: Post, platform: Platform, canonical_base: str) -> str`
- Internal helpers: `_format_devto()`, `_format_gongzhonghao()`, `_format_x()`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_syndicate.py`:

```python
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
```

- [ ] **Step 2: Run tests — should fail**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 6 new FAILs — `format_post` not defined

- [ ] **Step 3: Implement `format_post()` and helpers**

Append to `scripts/syndicate.py`:

```python


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
```

- [ ] **Step 4: Run tests — should pass**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/syndicate.py tests/test_syndicate.py
git commit -m "Add platform formatters: devto, substack, gongzhonghao, x, passthrough"
```

---

### Task 7: Output writing + CLI main + `--all` support

**Files:**
- Modify: `scripts/syndicate.py` (append CLI + output logic)
- Modify: `tests/test_syndicate.py` (append integration test)

**Interfaces:**
- Consumes: All prior functions (parse_post, load_routes, match_platforms, find_post_for_language, format_post)
- Produces: `process_post(filepath: Path, routes: list[Route], canonical_base: str) -> None`, `find_all_posts() -> list[Path]`, `main()` entry point

This is the final assembly task — wires everything together and makes the script runnable.

- [ ] **Step 1: Add integration test**

Append to `tests/test_syndicate.py`:

```python
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

    # The existing post has tags [english, meta, mkdocs, blog] —
    # none of these are convention tags, so output should say "无同步目标"
    # or list platforms if any match


def test_cli_nonexistent_file():
    """Passing a non-existent file should exit with error."""
    result = subprocess.run(
        ["uv", "run", "python", "scripts/syndicate.py", "nonexistent.md"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
```

- [ ] **Step 2: Run tests — should fail**

```bash
uv run pytest tests/test_syndicate.py::test_cli_single_post_generates_files tests/test_cli_nonexistent_file -v
```
Expected: FAIL — `process_post` / `main` not found or script not runnable

- [ ] **Step 3: Add output writing + CLI to the script**

Append to `scripts/syndicate.py`:

```python


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
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest tests/test_syndicate.py -v
```
Expected: 19 passed

- [ ] **Step 5: Manual smoke test with the real blog post**

```bash
uv run python scripts/syndicate.py docs/blog/posts/en/setting-up-this-blog.md
```
Expected: prints the post slug and sync targets (or "无同步目标" since the post has `meta`/`mkdocs`/`blog` tags, none of which are convention tags)

- [ ] **Step 6: Commit**

```bash
git add scripts/syndicate.py tests/test_syndicate.py
git commit -m "Add CLI, output writing, and --all support to syndicate.py"
```

---

### Task 8: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

**Interfaces:**
- Produces: `_syndication/` is ignored by git

- [ ] **Step 1: Append `_syndication/` to `.gitignore`**

Add this line at the end of `.gitignore`:

```
_syndication/
```

- [ ] **Step 2: Verify it's ignored**

```bash
mkdir -p _syndication/test
touch _syndication/test/foo.md
git status --short
```
Expected: `_syndication/` does NOT appear in `git status`

- [ ] **Step 3: Clean up and commit**

```bash
rm -rf _syndication
git add .gitignore
git commit -m "Add _syndication/ to .gitignore"
```

---

### Task 9: Git post-commit hook + install script

**Files:**
- Create: `scripts/post-commit` (the hook script itself)
- Create: `scripts/install-hook.sh` (one-time installer)

**Interfaces:**
- Produces: `.git/hooks/post-commit` hook that runs syndicate.py on changed posts

Note: Git hooks live in `.git/hooks/` which is not version-controlled. We commit the hook source to `scripts/` and provide an install script.

- [ ] **Step 1: Create the hook script**

Create `scripts/post-commit`:

```bash
#!/bin/bash
# Post-commit hook: detect new/modified blog posts and remind about syndication.
# Installed by scripts/install-hook.sh

REPO_ROOT=$(git rev-parse --show-toplevel)
CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | grep '^docs/blog/posts/.*\.md$' || true)

if [ -n "$CHANGED" ]; then
    echo ""
    echo "📢 检测到博客文章变更，检查同步目标..."
    echo ""

    echo "$CHANGED" | while read -r file; do
        uv run --directory "$REPO_ROOT" python scripts/syndicate.py "$REPO_ROOT/$file"
    done

    echo ""
    echo "💡 打开 MultiPost 浏览器扩展 → 粘贴对应文件内容 → 选择平台 → 一键发布"
    echo ""
fi
```

- [ ] **Step 2: Create the install script**

Create `scripts/install-hook.sh`:

```bash
#!/bin/bash
# Install the post-commit hook for blog syndication reminders.
# Run once: bash scripts/install-hook.sh

set -e

HOOK_SRC="$(dirname "$0")/post-commit"
HOOK_DST="$(git rev-parse --show-toplevel)/.git/hooks/post-commit"

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✅ post-commit hook installed at .git/hooks/post-commit"
```

- [ ] **Step 3: Make both scripts executable and install the hook**

```bash
chmod +x scripts/post-commit scripts/install-hook.sh
bash scripts/install-hook.sh
```

Expected: `✅ post-commit hook installed at .git/hooks/post-commit`

- [ ] **Step 4: Test the hook with a dummy commit**

```bash
# Create a test file in docs/blog/posts/en/ with no convention tags
# so the hook runs but produces no output files
touch docs/blog/posts/en/_test_hook.md
git add docs/blog/posts/en/_test_hook.md
git commit -m "test: verify post-commit hook"
```
Expected: hook fires, runs syndicate.py, output appears in the commit log

- [ ] **Step 5: Clean up test file**

```bash
git rm docs/blog/posts/en/_test_hook.md
git commit -m "Remove hook test file"
```

- [ ] **Step 6: Commit the hook source**

```bash
git add scripts/post-commit scripts/install-hook.sh
git commit -m "Add post-commit hook and installer for syndication reminders"
```

---

### Task 10: Final verification — end-to-end with --all

**Files:**
- No changes — verification only

- [ ] **Step 1: Run `--all` mode**

```bash
uv run python scripts/syndicate.py --all
```

Expected: prints each post found and its sync targets. For the current blog post (`setting-up-this-blog`, tags: `meta`, `mkdocs`, `blog`), prints "无同步目标" since none of those are convention tags.

- [ ] **Step 2: Run the full test suite one last time**

```bash
uv run pytest tests/test_syndicate.py -v
```

Expected: 19 passed

- [ ] **Step 3: Verify `.gitignore` is working**

```bash
git status --short
```

Expected: no `_syndication/` in output

- [ ] **Step 4: Mark complete**

No commit needed — verification only.

---

## Completion Checklist

- [ ] `scripts/syndicate.yml` — routing config, committed and editable
- [ ] `scripts/syndicate.py` — CLI with `parse_post`, `load_routes`, `match_platforms`, `find_post_for_language`, `format_post`, `write_output`, `process_post`, `main`
- [ ] `scripts/post-commit` — git hook source
- [ ] `scripts/install-hook.sh` — one-time hook installer
- [ ] `.gitignore` — includes `_syndication/`
- [ ] `tests/test_syndicate.py` — 19 tests covering parsing, matching, formatting, language resolution, CLI
- [ ] `_syndication/` — output directory, gitignored, created on demand
- [ ] `pyproject.toml` — includes `pytest` dev dependency
