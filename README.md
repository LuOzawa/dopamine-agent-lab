# Dopamine Agent Lab

两个本地学习站，放在同一个仓库里：

- **AI Agent 学习站** — 47 节 / 8 阶段，多巴胺风格，覆盖概念、模型、RAG、框架、多智能体与生产部署。
- **DeepSeek Harness 手册** — 33 节 / 6 章，编辑式手册风格，覆盖安装、模型、插件、服务、沙箱与复盘。

两门课都保留原文链接，每节含「目标 / 前置 / 要点 / 动手 / 自检」，并附带内容审计与全文搜索。
纯静态、离线可用、无需服务器。

![AI Agent 学习站](docs/preview-index.png)

| DeepSeek Harness 手册 | 全文搜索 |
|---|---|
| ![DeepSeek Harness](docs/preview-dsh.png) | ![搜索](docs/preview-search.png) |

---

## 两门课

| 课程 | 入口 | 风格 | 规模 |
|---|---|---|---|
| AI Agent 学习站 | [`ai-agent/index.html`](ai-agent/index.html) | 多巴胺 / 贴纸感 | 47 节 · 8 阶段 |
| DeepSeek Harness 手册 | [`deepseek-harness/index.html`](deepseek-harness/index.html) | 纸白 / 墨蓝 / 黄铜 | 33 节 · 6 章 |

仓库首页 [`index.html`](index.html) 是两门课的落地页。

## 打开

1. 保持目录完整，双击根目录 `index.html`，选择课程。
2. 也可以直接打开 `ai-agent/index.html` 或 `deepseek-harness/index.html`。
3. 进度保存在本机 `localStorage`；换浏览器或清站点数据会重置。

## 目录结构

```text
.
├── index.html                 课程落地页
├── 404.html                   旧链接重定向
├── ai-agent/                  第一门课：47 节
│   ├── index.html / stage-1..8.html / contents / frameworks / search / audit / about
│   ├── assets/                样式、进度、搜索索引、lesson map
│   ├── examples/              第 5、6 阶段可运行实验与下载包
│   ├── tools/                 章节生成、搜索索引、示例构建与校验
│   └── LICENSE*               课程目录内的许可副本
├── deepseek-harness/          第二门课：33 节
│   ├── index.html / stage-1..6.html / contents / search / audit / about
│   ├── assets/                独立样式、进度与搜索索引
│   ├── design/                设计参考与验收截图
│   ├── design-qa.md           设计验收记录
│   ├── tools/                 课程生成、UI 检查、截图脚本
│   └── LICENSE*               课程目录内的许可副本
├── docs/                      仓库级预览图
├── LICENSE                    MIT（代码）
├── LICENSE-CONTENT.md         CC BY-NC-SA 4.0（原创文字）
├── LICENSE-CC-BY-NC-SA-4.0.txt
└── README.md
```

## 旧链接

主站原来的根路径已经移入 `ai-agent/`。访问旧地址时，GitHub Pages 的 `404.html` 会自动跳转：

- `/stage-5.html` → `/ai-agent/stage-5.html`
- `/contents.html` → `/ai-agent/contents.html`
- `/assets/...`、`/examples/...`、`/tools/...` → `/ai-agent/...`

落地页和两门课的入口不受影响。

## 两门课各自有什么

### AI Agent 学习站

- 47 节，8 阶段，约 22 小时
- 原文 3 组 48 项的全部目录对照
- 13 个 Agent 框架 + 8 个工具/平台的选型矩阵
- 全文搜索：47 节 / 1,288 句
- 47 行内容审计 + 12 条更新对照
- 第 5、6 阶段可运行实验：源码、固定依赖、测试、预期输出、下载包

### DeepSeek Harness 手册

- 33 节，6 章，约 15 小时
- 原文 2 组 34 项的全部目录对照
- 5 个「跟着做」实操示例：安装、首条只读任务、自定义模型、第一个插件、加载插件
- 全文搜索：33 节 / 396 句
- 33 行内容审计；模型名、benchmark、发布时间等标「待核实」
- 设计验收记录与截图：`design-qa.md`、`design/`

## 维护

```bash
# 重建第一门课的章节前后篇与 STAGE_TOTAL
python3 ai-agent/tools/link_chapters.py

# 重建第一门课搜索索引与首页 lesson map
python3 ai-agent/tools/build_search_index.py

# 重建第二门课的页面、目录、审计与搜索索引
python3 deepseek-harness/tools/build.py
```

第二门课的可选 UI 回归检查（需要本机 Node 版 Playwright）：

```bash
node deepseek-harness/tools/check-ui.cjs
```

## 内容审计

审计结论分别在两个课程目录里：

- [`ai-agent/audit.html`](ai-agent/audit.html)：47 行，状态、影响范围、严重度、优先级与依据。
- [`deepseek-harness/audit.html`](deepseek-harness/audit.html)：33 行，整体与 0.2.x 预览版一致，具体版本与模型信息需自行核实。

## 许可证

- **代码**（HTML / CSS / JS、示例代码、工具脚本）：MIT，见 [`LICENSE`](LICENSE)。
- **原创文字**（学习路径、要点、任务、审计、说明）：CC BY-NC-SA 4.0，见 [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md) 与 [`LICENSE-CC-BY-NC-SA-4.0.txt`](LICENSE-CC-BY-NC-SA-4.0.txt)。
- 两个课程目录内各有一份许可副本，方便单独取用。
- runoob 原文、图片、商标与第三方内容不在本仓库授权范围内。

## 来源

- [runoob · AI Agent（智能体）教程](https://www.runoob.com/ai-agent/ai-agent-tutorial.html)
- [runoob · DeepSeek Harness 教程](https://www.runoob.com/deepseek-harness/deepseek-harness-tutorial.html)

本站不复制原文全文，只提供学习路径、要点提炼、任务与审计；原文版权归原站点/原作者。
