---
date:
  created: 2026-07-10
categories:
  - Meta
tags:
  - chinese
  - meta
  - mkdocs
  - blog
authors:
  - requiema
---

# 这个博客是怎么搭建的

第一篇博客写博客本身 —— 记录搭建这个站点的每一个决策和步骤。如果你也想用 [MkDocs Material][1]
建一个轻量级开发者博客，希望这篇能帮你省几个小时。

## 为什么选 MkDocs Material？

我要的三件事：

1. **用 Markdown 写文章** —— 不要 CMS、不要数据库、不要 WordPress。
2. **`git push` 即部署** —— GitHub Actions 自动构建，GitHub Pages 自动上线。
3. **原生支持双语** —— 英文和中文，搜索能同时索引两种语言。

静态站点生成器是自然的选择，横向对比：

| 工具 | 写作 | 国际化 | 主题生态 |
|------|------|--------|----------|
| Hugo | 好 | 内置 | 多但碎片化 |
| Jekyll | 好 | 靠插件 | GitHub Pages 原生 |
| MkDocs Material | 好（Markdown） | 内置搜索多语言 | 一个精品主题 |

MkDocs Material 赢在第三列 —— 一个主题把事做全、做一致，不需要拼接五个维护参差的模板。
[`blog` 插件][2] 是一等公民，不是事后补丁。

## 搭建步骤

### 1. 脚手架

```bash
pip install mkdocs-material
mkdocs new .
```

得到 `mkdocs.yml` 和 `docs/index.md`。把 `index.md` 换成自己的首页。

### 2. 核心配置

`mkdocs.yml` 是唯一的配置来源。关键部分：

```yaml
# Blog 插件 —— 文章、归档、分类、分页
plugins:
  - blog:
      blog_dir: blog
      post_dir: "{blog}/posts"
      archive: true
      categories: true
      pagination: true
      pagination_per_page: 10
      authors_file: "{blog}/.authors.yml"

  # Tags —— 自动生成标签索引页
  - tags

  # 搜索 —— 中英文分词
  - search:
      lang: [en, zh]

  # RSS 订阅
  - rss:
      match_path: blog/posts/.*
```

### 3. 双语方案

没有拆分站点、没有用 `mkdocs-static-i18n` 插件。就是目录约定：

```
docs/blog/posts/
├── en/    ← 英文文章，tag `english`
└── zh/    ← 中文文章，tag `chinese`
```

搜索同时索引两种语言 —— 上面那段 `lang: [en, zh]` 告诉内置分词器要处理 CJK 字符。
读者通过标签系统按语言筛选文章。

### 4. GitHub Actions CI

一个 workflow 文件（`.github/workflows/ci.yml`）做三件事：

1. Checkout 仓库（full depth，`git-revision-date-localized` 插件需要）
2. `pip install` 依赖 → `mkdocs build`
3. `actions/deploy-pages` 发布

仓库 **Settings → Pages → Source → GitHub Actions** 设置好就全自动了。

### 5. 统计与评论

**Google Analytics 4** —— `mkdocs.yml` 里加一个块：

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

**giscus** —— 免费无广告的评论系统，基于 GitHub Discussions。仓库开启 Discussions、安装
[giscus App][3]，把 repo/category ID 填入 `mkdocs.yml` 即可。

### 6. 主题细节

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

Material 的 feature flag 文档很全 —— 需要什么开什么，其余的关掉。

## 如何写文章

每篇文章是一个 Markdown 文件，加上 frontmatter：

```markdown
---
date:
  created: 2026-07-10
categories:
  - CategoryName
tags:
  - chinese    # 或 english
  - topic-tag
authors:
  - requiema
---

# 标题

正文内容。
```

放入 `docs/blog/posts/zh/` 或 `docs/blog/posts/en/`，commit，push —— CI 自动处理剩下的。

## 故意没做的事情

- **社交卡片** —— 插件能用，但 CairoSVG 在 WSL 上渲染慢。在 CI 环境取消注释 `social.cards: true` 即可。
- **giscus 以外的评论系统** —— Disqus 有广告，utterances 需要单独的 bot。giscus 直接用仓库自己的 Discussions。
- **邮件订阅** —— 暂时不需要。

## 总结

| 维度 | 选择 |
|------|------|
| 静态站点生成器 | MkDocs Material 9.7 |
| 托管 | GitHub Pages（Actions CI） |
| 语言 | `en` / `zh`，目录约定 + 标签 |
| 搜索 | 内置，`lang: [en, zh]` |
| 统计 | Google Analytics 4 |
| 评论 | giscus（GitHub Discussions） |
| RSS | `mkdocs-rss-plugin` |
| 写作 | Markdown + YAML frontmatter |

完整配置在 [仓库源码][4] 里。去写点什么吧。

[1]: https://squidfunk.github.io/mkdocs-material/
[2]: https://squidfunk.github.io/mkdocs-material/setup/setting-up-a-blog/
[3]: https://github.com/apps/giscus
[4]: https://github.com/RequieMa/requiema.github.io
