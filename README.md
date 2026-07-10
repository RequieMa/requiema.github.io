# RequieMa's Personal Website

Source for [requiema.github.io](https://requiema.github.io) — a bilingual (EN/中文) blog built
with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

## Local development

```bash
uv sync
uv run mkdocs serve    # → http://127.0.0.1:8000
```

## Deploy

Push to `Master` → GitHub Actions builds and deploys to GitHub Pages.

## Syndication

Cross-post blog content to external platforms with a single command:

```bash
# Process one post:
uv run python scripts/syndicate.py docs/blog/posts/en/my-post.md

# Process all posts:
uv run python scripts/syndicate.py --all
```

### How it works

1. **Tag your post** with a convention tag in frontmatter — `essay`, `tutorial`,
   `guide`, `howto`, `release`, `launch`, `book`, or `notes`.
2. **Run the script** — it reads routing rules from
   [`scripts/syndicate.yml`](scripts/syndicate.yml), matches your tags to target
   platforms, and writes formatted Markdown to `_syndication/<slug>/`.
3. **Copy-paste** each output file into
   [MultiPost](https://multipost.app) (browser extension) or the platform
   directly.

### Platform routing

| Convention tags | Platforms |
|---|---|
| `essay` | zhihu, gongzhonghao, devto, substack |
| `tutorial`, `guide`, `howto` | juejin, devto |
| `release`, `launch` | devto, X |
| `book`, `notes` | yuque, devto |

Chinese platforms get the `zh/` version of a post; English platforms get the
`en/` version. If a language version is missing, the script falls back to
whatʼs available.

Edit [`scripts/syndicate.yml`](scripts/syndicate.yml) to change routing rules
— nothing is hardcoded.

### Bilingual posts

For a post to syndicate to both Chinese and English platforms, create sibling
files with the same filename:

```
docs/blog/posts/en/my-post.md   ← English version
docs/blog/posts/zh/my-post.md   ← 中文版本
```

### Git hook

Run once to install a post-commit hook that reminds you about syndication
targets whenever you commit a blog post:

```bash
bash scripts/install-hook.sh
```

Reddit and Hacker News are intentionally excluded — always hand-craft those.

## Structure

```
docs/
├── blog/posts/en/     ← English posts
├── blog/posts/zh/     ← 中文文章
├── en/                ← EN landing page
├── zh/                ← 中文入口
└── stylesheets/       ← custom CSS
```
