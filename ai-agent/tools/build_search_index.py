#!/usr/bin/env python3
"""从 8 个阶段页生成全文搜索索引。

输出：
  assets/search-index.json   —— 纯 JSON，便于检查与二次使用
  assets/search-index.js     —— window.__SEARCH_INDEX__ = {...};
                                因为 file:// 下 fetch(JSON) 会被 CORS 拦截，
                                页面用 <script src> 加载这份包装。

用法：python3 tools/build_search_index.py
"""
import json, re, html, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent

def clean(fragment: str) -> str:
    fragment = re.sub(r'<script.*?</script>', '', fragment, flags=re.S)
    fragment = re.sub(r'<[^>]+>', '', fragment)
    fragment = html.unescape(fragment)
    fragment = fragment.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', fragment).strip()

def split_sentences(text: str):
    parts = re.split(r'(?<=[。！？!?；;])\s*', text)
    return [p.strip() for p in parts if p.strip()]

lessons = []
lesson_map = []
for n in range(1, 9):
    path = ROOT / f'stage-{n}.html'
    src = path.read_text(encoding='utf-8')
    for m in re.finditer(r'<article class="lesson" id="(s\d-\d+)">(.*?)</article>', src, re.S):
        sid, block = m.group(1), m.group(2)
        title = clean(re.search(r'<div class="lesson-head">.*?<h2>(.*?)</h2>', block, re.S).group(1))
        sentences = []

        def add(kind, text):
            for s in split_sentences(clean(text)):
                if len(s) >= 4:
                    sentences.append({'k': kind, 't': s})

        mgoal = re.search(r'<div class="field goal">.*?<h3>.*?</h3>\s*<p>(.*?)</p>', block, re.S)
        if mgoal:
            add('目标', mgoal.group(1))

        mpre = re.search(r'<h3>.*?前置知识.*?</h3>\s*<p>(.*?)</p>', block, re.S)
        if mpre:
            add('前置', mpre.group(1))

        mbullet = re.search(r'<h3>.*?核心要点.*?</h3>\s*<ul>(.*?)</ul>', block, re.S)
        if mbullet:
            for li in re.findall(r'<li>(.*?)</li>', mbullet.group(1), re.S):
                add('要点', li)

        mtask = re.search(r'<div class="field task[^"]*">.*?<h3>.*?</h3>\s*<p>(.*?)</p>', block, re.S)
        if mtask:
            add('任务', mtask.group(1))

        for q, a in re.findall(r'<details>\s*<summary>(.*?)</summary>\s*<div class="a">(.*?)</div>', block, re.S):
            add('自检', q)
            add('答案', a)

        # 站内「补充」块（表格/列表）也纳入索引
        for m in re.finditer(r'<div class="callout[^"]*"', block):
            tail = block[m.start():].split('<div class="lesson-actions">')[0]
            for tag in ('li', 'p'):
                for frag in re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', tail, re.S):
                    add('补充', frag)
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tail, re.S):
                cells = [clean(x) for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
                cells = [c for c in cells if c]
                if cells:
                    add('补充', ' ｜ '.join(cells))

        # 去重，保留顺序
        # 可运行实验的操作说明、命令和报错可搜索；完整源码不加入索引。
        for example in re.findall(r'<section class="runnable-example".*?</section>', block, re.S):
            example = re.sub(r'<details class="example-source">.*?</details>', '', example, flags=re.S)
            for fragment in re.findall(r'<(?:p|li)>(.*?)</(?:p|li)>', example, re.S):
                add('实验', fragment)
            for command in re.findall(r'<pre class="example-code example-command"[^>]*><code>(.*?)</code></pre>', example, re.S):
                add('运行', command)

        seen = set()
        uniq = []
        for s in sentences:
            key = s['t']
            if key not in seen:
                seen.add(key)
                uniq.append(s)

        lessons.append({
            'id': sid,
            'stage': n,
            'title': title,
            'url': f'stage-{n}.html#{sid}',
            'sentences': uniq,
        })
        duration = re.search(r'<span class="chip accent">(.*?)</span>', block, re.S)
        lesson_map.append({
            'id': sid, 'title': title, 'url': f'stage-{n}.html#{sid}',
            'duration': clean(duration.group(1)) if duration else '按自己的节奏学习',
        })

payload = {
    'generated': datetime.date.today().isoformat(),
    'count': len(lessons),
    'lessons': lessons,
}

out_json = ROOT / 'assets/search-index.json'
out_js = ROOT / 'assets/search-index.js'
out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding='utf-8')
out_js.write_text(
    '/* 由 tools/build_search_index.py 生成，请勿手改；改内容后重新运行脚本。 */\n'
    'window.__SEARCH_INDEX__ = ' + json.dumps(payload, ensure_ascii=False) + ';\n',
    encoding='utf-8')
(ROOT / 'assets/lesson-map.js').write_text(
    '/* 由 tools/build_search_index.py 生成，供首页继续学习使用。 */\n'
    'window.__LESSON_MAP__ = ' + json.dumps(lesson_map, ensure_ascii=False) + ';\n',
    encoding='utf-8')

total = sum(len(l['sentences']) for l in lessons)
print(f'lessons={len(lessons)} sentences={total}')
print(f'json={out_json.stat().st_size/1024:.1f}KB js={out_js.stat().st_size/1024:.1f}KB')
