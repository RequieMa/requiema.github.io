<sub>🌐 <b>English</b> · <a href="README-cn.md">中文</a></sub>

# RequieMa's Personal Website

> *"Thinking in feedback loops — shown through code that teaches."*

<!-- Support badges -->
[![Ko-fi](https://img.shields.io/badge/Support-ko--fi-FF5E5B?style=flat&logo=ko-fi&logoColor=white)](https://ko-fi.com/requiema)
[![Afdian](https://img.shields.io/badge/Support-爱发电-946CE6?style=flat)](https://afdian.com/a/requiema)

[![MkDocs Material](https://img.shields.io/badge/MkDocs_Material-9.7-526CFE?style=flat&logo=materialformkdocs)](https://squidfunk.github.io/mkdocs-material/)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-deployed-222222?style=flat&logo=github)](https://requiema.github.io)

<br>

**Bilingual blog source (EN/中文) built with MkDocs Material, deployed via GitHub Actions.**

Source for [requiema.github.io](https://requiema.github.io) — a personal site about cybernetics, control theory, and complexity science, written in Chinese and English.

[Quick Start](#quick-start) · [What's Here](#whats-here) · [Repository Structure](#repository-structure)

---

## Quick Start

```bash
git clone https://github.com/RequieMa/requiema.github.io
cd requiema.github.io
uv sync
uv run mkdocs serve    # → http://127.0.0.1:8000
```

Push to `Master` → GitHub Actions builds and deploys to GitHub Pages.

---

## What's Here

| Section | Content | Language |
|---------|---------|----------|
| Blog | Essays, tutorials, release notes | EN + ZH |
| Landing | EN/ZH home pages with language switcher | EN + ZH |
| Notes | Reading notes, book summaries | EN + ZH |

### Syndication

Cross-post blog posts to external platforms from the CLI:

```bash
uv run python scripts/syndicate.py docs/blog/posts/en/my-post.md
uv run python scripts/syndicate.py --all
```

Tag a post with `essay`, `tutorial`, `guide`, `howto`, `release`, `launch`, `book`, or `notes` in frontmatter — the script reads [`scripts/syndicate.yml`](scripts/syndicate.yml) and generates platform-formatted Markdown in `_syndication/`. Chinese platforms get the `zh/` sibling, English ones get `en/`.

| Convention tags | Platforms |
|---|---|
| `essay` | zhihu, gongzhonghao, devto, substack |
| `tutorial`, `guide`, `howto` | juejin, devto |
| `release`, `launch` | devto, X |
| `book`, `notes` | yuque, devto |

Install a post-commit hook for automatic reminders:

```bash
bash scripts/install-hook.sh
```

Reddit and Hacker News are intentionally excluded — always hand-craft those.

---

## Repository Structure

```
requiema.github.io/
├── docs/
│   ├── blog/posts/en/       # English posts
│   ├── blog/posts/zh/       # Chinese posts
│   ├── en/                  # EN landing page
│   ├── zh/                  # Chinese landing
│   └── stylesheets/         # Custom CSS
├── scripts/
│   ├── syndicate.py         # Syndication CLI
│   ├── syndicate.yml        # Routing config (editable)
│   ├── post-commit          # Git hook
│   └── install-hook.sh      # Hook installer
├── tests/
│   └── test_syndicate.py    # 19 tests
├── mkdocs.yml               # MkDocs config
├── .github/workflows/       # CI → GitHub Pages
└── README.md
```

---

## Connect

<div align="center">

| | | |
|---|---|---|
| 📧 | Email | [mazengou@gmail.com](mailto:mazengou@gmail.com) |
| 🌐 | Personal Site | [requiema.github.io](https://requiema.github.io) |
| 📝 | dev.to | [dev.to/requiema](https://dev.to/requiema) |
| 𝕏 | X | [x.com/mazengou](https://x.com/mazengou) |
| 👾 | Reddit | [u/Leather_Rip7919](https://www.reddit.com/user/Leather_Rip7919/) |
| 🔖 | 掘金 | [juejin.cn/user/76300220645242](https://juejin.cn/user/76300220645242) |
| 📦 | Gitee | [gitee.com/requiema](https://gitee.com/requiema) |
| 📖 | 知乎 | [zhihu.com/people/consilivm](https://www.zhihu.com/people/consilivm) |
| 🎬 | Bilibili | 镇魂曲麦 |
| 📱 | 公众号 | 镇魂曲麦 |

</div>
