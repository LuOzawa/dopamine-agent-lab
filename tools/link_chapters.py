#!/usr/bin/env python3
"""重建「章级前后篇」并同步 app.js 的 STAGE_TOTAL。

- 扫描 stage-1..8.html 中的 <article class="lesson" id="sN-M">
- 按阶段 + 文档顺序串成一条链路
- 删除旧的 <nav class="chapter-nav"> 后重新插入（可重复运行）
- 第一节的前篇指向学习地图，最后一节的后篇指向审计台账

用法：python3 tools/link_chapters.py
"""
import re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGES = 8

def clean_title(fragment):
    return html.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()

# 1) 移除旧导航
for n in range(1, STAGES + 1):
    path = ROOT / f'stage-{n}.html'
    src = path.read_text(encoding='utf-8')
    src = re.sub(r'\s*<nav class="chapter-nav".*?</nav>\s*', '\n', src, flags=re.S)
    path.write_text(src, encoding='utf-8')

# 2) 收集章节
order = []
for n in range(1, STAGES + 1):
    path = ROOT / f'stage-{n}.html'
    src = path.read_text(encoding='utf-8')
    for m in re.finditer(r'<article class="lesson" id="(s\d-\d+)">(.*?)</article>', src, re.S):
        sid, art = m.group(1), m.group(2)
        badge = re.search(r'<span class="lesson-badge">([^<]+)</span>', art).group(1).strip()
        title = clean_title(re.search(r'<div class="lesson-head">.*?<h2>(.*?)</h2>', art, re.S).group(1))
        order.append({'id': sid, 'stage': n, 'file': path.name, 'badge': badge, 'title': title})

# 3) 生成并插入
for i, item in enumerate(order):
    prev = order[i - 1] if i > 0 else None
    nxt = order[i + 1] if i < len(order) - 1 else None
    prev_html = (
        f'<a class="prev" href="{prev["file"]}#{prev["id"]}"><span class="dir">← 上一节</span>'
        f'<span class="t">{html.escape(prev["badge"] + " " + prev["title"])}</span></a>'
        if prev else
        '<a class="prev" href="index.html"><span class="dir">← 起点</span><span class="t">学习地图</span></a>'
    )
    next_html = (
        f'<a class="next" href="{nxt["file"]}#{nxt["id"]}"><span class="dir">下一节 →</span>'
        f'<span class="t">{html.escape(nxt["badge"] + " " + nxt["title"])}</span></a>'
        if nxt else
        '<a class="next" href="audit.html"><span class="dir">完成 →</span><span class="t">内容审计台账</span></a>'
    )
    nav = f'''        <nav class="chapter-nav" aria-label="章节翻页">
          {prev_html}
          {next_html}
        </nav>
'''
    path = ROOT / item['file']
    src = path.read_text(encoding='utf-8')
    start = src.index(f'<article class="lesson" id="{item["id"]}">')
    end = src.index('</article>', start)
    art = src[start:end].rstrip()
    src = src[:start] + art + '\n' + nav + src[end:]
    path.write_text(src, encoding='utf-8')

# 4) 同步 STAGE_TOTAL
counts = {}
for item in order:
    counts[item['stage']] = counts.get(item['stage'], 0) + 1
pos = ', '.join(f'{n}:{counts.get(n, 0)}' for n in range(1, STAGES + 1))
js_path = ROOT / 'assets/app.js'
js = js_path.read_text(encoding='utf-8')
js = re.sub(r'var STAGE_TOTAL = \{[^}]*\};', f'var STAGE_TOTAL = {{{pos}}};', js, count=1)
js_path.write_text(js, encoding='utf-8')

print(f'chapters={len(order)} STAGE_TOTAL={{{pos}}}')
