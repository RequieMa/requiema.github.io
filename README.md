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

## Structure

```
docs/
├── blog/posts/en/     ← English posts
├── blog/posts/zh/     ← 中文文章
├── en/                ← EN landing page
├── zh/                ← 中文入口
└── stylesheets/       ← custom CSS
```
