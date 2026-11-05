# DeepSeek Harness 学习手册

以 [runoob · DeepSeek Harness 教程](https://www.runoob.com/deepseek-harness/deepseek-harness-tutorial.html) 为蓝本的本地学习站：6 章、33 节，正式文档风格。

## 打开

双击 `index.html` 即可。纯静态、无外部字体/CDN、无需服务器；进度保存在本机 `localStorage`。

## 内容

- `index.html` 继续阅读入口与四条阅读路线
- `stage-1.html` ～ `stage-6.html` 33 节，每节含目标 / 前置 / 要点 / 动手 / 自检
- `contents.html` 对照原文 2 组 34 项的全部章节
- `search.html` 全文搜索（33 节，包含实操示例、代码与排错）
- `audit.html` 33 行内容审计
- `about.html` 假设声明、设计令牌、维护与待核实清单
- `tools/build.py` 课程数据与页面/索引生成脚本

## 许可

- 代码 MIT，见 `LICENSE`。
- 原创文字 CC BY-NC-SA 4.0，见 `LICENSE-CONTENT.md` 与 `LICENSE-CC-BY-NC-SA-4.0.txt`。
- 原教程与第三方内容不在本目录授权范围内。

## 维护

修改 `tools/build.py` 中的课程数据后运行：

```bash
python3 tools/build.py
```

会重新生成阶段页、首页、目录、审计、搜索页与搜索索引。

实操示例维护在 `tools/build.py` 的 `EXAMPLES` 中，包含操作步骤、可复制代码、预期结果、排错和官方来源。示例的文档对照日期独立于既有内容审计日期。

首页优先返回上次未完成的小节，已完成时推荐按顺序排在最前的未完成小节。浏览器存储失败时会显示持续提示；复制不可用时可手动复制选中的代码。

交互回归检查（需要本机已有 Playwright 和 Chromium）：

```bash
node tools/check-ui.cjs
```

可用 `PLAYWRIGHT_MODULE` 指定 Playwright 模块路径，`CHROME_PATH` 指定浏览器路径。检查覆盖进度保存、审计入口、移动端目录、搜索边界和直接打开 HTML；使用临时浏览器配置，不读取个人浏览器数据。
