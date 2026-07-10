# Blog Syndication System — Design Spec

**Date:** 2026-07-10
**Status:** approved

## Overview

A semi-automated syndication pipeline for the RequieMa blog (MkDocs Material). Write a post once
in the blog repo, run one command, get platform-formatted copies ready for bulk publishing via
MultiPost browser extension. A Git hook provides automatic reminders on commit.

## Goals

1. **One command** generates platform-adapted Markdown files for all target platforms
2. **Tag-based routing** — convention tags (`essay`, `tutorial`, `release`, etc.) decide which
   platforms a post should go to
3. **Language-aware** — English platforms get the English version, Chinese platforms get the
   Chinese version, auto-matched
4. **Git hook reminder** — `post-commit` hook detects new/modified posts and prints sync
   instructions
5. **Never committed** — generated files live in `_syndication/`, gitignored

## Components

### 1. Project Layout

```
scripts/
├── syndicate.py          ← CLI script (~150 lines)
└── syndicate.yml         ← routing config (committed, user-editable)
```

### 2. `scripts/syndicate.yml` — Routing Config

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

**Resolution rules:**
- First matching route group wins (top-to-bottom)
- Post with no matching convention tag → no sync targets, script prints info message
- Multiple matching tags across groups (e.g., `essay` + `tutorial`) → union of both platform sets, deduplicated by `name+language`

### 3. `scripts/syndicate.py` — CLI Script

**Dependencies:** Python stdlib + `pyyaml` (already in project)

**Interface:**
```bash
python scripts/syndicate.py docs/blog/posts/en/my-post.md    # single post
python scripts/syndicate.py --all                              # all posts
```

**Logic flow:**
1. Parse post path → read YAML frontmatter → extract title, tags, content
2. Load `scripts/syndicate.yml` → match post tags against route groups
3. For each matched platform, find the right language version (zh → Chinese post, en → English post)
4. Call platform-specific formatter → write to `_syndication/{slug}/{platform}-{lang}.md`
5. Print summary to terminal

### 4. Platform Formatters

| Platform | Format | Special handling |
|---|---|---|
| dev.to | Markdown | Frontmatter includes `canonical_url: https://requiema.github.io/blog/{slug}/` |
| Juejin | Markdown | Passthrough |
| Zhihu | Markdown | Passthrough |
| 公众号 | Markdown | Comment at top: `<!-- 公众号只支持富文本，请用 https://markdown.com.cn 转成富文本后粘贴 -->` |
| Substack | Markdown | Same as dev.to |
| X/Twitter | Plain text | `{title}\n\n{first-paragraph-summary}... 🔗 {canonical_url}` ≤ 280 chars |

### 5. Language Matching

- Script receives one post path (e.g., `en/my-post.md`)
- Automatically checks for sibling at `zh/my-post.md` (same filename, other language dir)
- English platforms → English version; Chinese platforms → Chinese version
- If only one language version exists, all platforms use that version

### 6. Output Structure

```
_syndication/                      ← gitignored
└── {slug}/
    ├── devto-en.md
    ├── zhihu-zh.md
    ├── gongzhonghao-zh.md
    ├── juejin-zh.md
    ├── substack-en.md
    └── x-en.md
```

### 7. Git Hook (`post-commit`)

- Detects new/modified files under `docs/blog/posts/`
- Runs `python scripts/syndicate.py <path>` for each
- Prints reminder with platform list and file paths
- Non-blocking — commit always succeeds regardless of syndication status

## What This System Does NOT Do

- Publish to platforms directly (use MultiPost for that)
- Handle Reddit/HN (always hand-crafted)
- Provide a unified inbox for replies/comments across platforms
- Track which posts have already been syndicated (manual tracking for now)

## Edge Cases

- **No convention tags:** script prints "No sync targets for this post" and exits cleanly
- **Post in one language only:** all platforms get that single version; no error
- **Missing zh/ counterpart:** Chinese platforms get the English version with a warning
- **Multiple convention tags (e.g., `essay` + `tutorial`):** union of both platform sets
- **X/Twitter > 280 chars:** truncate at last complete sentence before limit, append `... 🔗`
