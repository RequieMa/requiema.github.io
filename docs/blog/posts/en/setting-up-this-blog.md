---
date:
  created: 2026-07-10
categories:
  - en
  - meta
tags:
  - english
  - meta
  - mkdocs
  - blog
authors:
  - requiema
---

# How This Blog Was Built

The first post is about the blog itself — a write-up of every decision and step that went into
putting this site together. If you are setting up a similar lightweight developer blog with
[MkDocs Material][1], this should save you a couple of hours.

## Why MkDocs Material?

I wanted three things:

1. **Write posts in Markdown** — no CMS, no database, no WordPress.
2. **Deploy on every `git push`** — GitHub Actions builds the site and deploys to GitHub Pages.
3. **Bilingual out of the box** — English and Chinese, with search that handles both.

Static site generators are the obvious choice. Among them:

| Tool | Writing | i18n | Theme ecosystem |
|------|---------|------|-----------------|
| Hugo | Good | Built-in | Large, fragmented |
| Jekyll | Good | Plugins | GitHub Pages native |
| MkDocs Material | Good (Markdown) | Built-in search langs | One excellent theme |

MkDocs Material wins on the third column — one theme that does everything well, consistently,
without me stitching together five half-maintained templates. The [`blog` plugin][2] is
first-class, not an afterthought.

## Step-by-step Setup

### 1. Scaffold

```bash
pip install mkdocs-material
mkdocs new .
```

This gives you `mkdocs.yml` and `docs/index.md`. Replace `index.md` with your landing page.

### 2. Core Configuration

`mkdocs.yml` is the single source of truth. Here is what goes in:

```yaml
# Blog plugin — posts, archive, categories, pagination
plugins:
  - blog:
      blog_dir: blog
      post_dir: "{blog}/posts"
      archive: true
      categories: true
      pagination: true
      pagination_per_page: 10
      authors_file: "{blog}/.authors.yml"

  # Tags — auto-generates tag index pages
  - tags

  # Search with Chinese tokenization
  - search:
      lang: [en, zh]

  # RSS
  - rss:
      match_path: blog/posts/.*
```

### 3. Bilingual Strategy

No separate site builds, no `mkdocs-static-i18n` plugin. Just a directory convention:

```
docs/blog/posts/
├── en/    ← English posts go here, tagged `english`
└── zh/    ← 中文文章放这里，tag `chinese`
```

Search indexes both languages — the `lang: [en, zh]` line above tells the built-in segmenter to
handle CJK characters. Readers filter by language via the tag system.

### 4. GitHub Actions CI

A single workflow file (`.github/workflows/ci.yml`) does three things on every push to `Master`:

1. Checkout the repo (full depth, needed for `git-revision-date-localized`)
2. `pip install` dependencies + `mkdocs build`
3. `actions/deploy-pages` to publish

Set **Settings → Pages → Source → GitHub Actions** in the repo and you are done.

### 5. Analytics & Comments

**Google Analytics 4** — one block in `mkdocs.yml`:

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

**giscus** — free, no-ads comment system powered by GitHub Discussions. Enable Discussions in the
repo settings, install the [giscus app][3], and drop the repo/category IDs into `mkdocs.yml`.

### 6. Theme Polish

```yaml
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.path
    - toc.follow
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.action.edit
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
```

Material's feature flags are well-documented — enable what you need, skip the rest.

## Writing a Post

Every post is a Markdown file with frontmatter:

```markdown
---
date:
  created: 2026-07-10
categories:
  - CategoryName
tags:
  - english     # or chinese
  - topic-tag
authors:
  - requiema
---

# Title

Content goes here.
```

Drop it in `docs/blog/posts/en/` or `docs/blog/posts/zh/`, commit, push — the CI pipeline handles
the rest.

## What is Missing (On Purpose)

- **Social cards** — the plugin works, but CairoSVG rendering is slow on WSL. Uncomment
  `social.cards: true` in CI environments.
- **No comment system other than giscus** — Disqus has ads, utterances requires a separate bot.
  giscus uses the repo's own Discussions.
- **No email newsletter** — not needed at launch.

## Summary

| Dimension | Choice |
|-----------|--------|
| SSG | MkDocs Material 9.7 |
| Hosting | GitHub Pages (Actions CI) |
| Language | `en` / `zh` via directory convention + tags |
| Search | Built-in, `lang: [en, zh]` |
| Analytics | Google Analytics 4 |
| Comments | giscus (GitHub Discussions) |
| RSS | `mkdocs-rss-plugin` |
| Writing | Markdown + YAML frontmatter |

The full config is in the [repo source][4]. Go write something.

[1]: https://squidfunk.github.io/mkdocs-material/
[2]: https://squidfunk.github.io/mkdocs-material/setup/setting-up-a-blog/
[3]: https://github.com/apps/giscus
[4]: https://github.com/RequieMa/requiema.github.io
