#!/usr/bin/env python3
"""检查页面嵌入、全站本地链接、章节数与第 6 阶段下载包完整性。"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import zipfile
from build_stage6_examples import ROOT, LAB, LESSONS, code


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids=[]; self.links=[]; self.lessons=[]
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'): self.ids.append(attrs['id'])
        if attrs.get('href'): self.links.append(attrs['href'])
        if tag=='article' and 'lesson' in attrs.get('class','').split(): self.lessons.append(attrs['id'])


def main():
    source=(ROOT/'stage-6.html').read_text()
    for item in LESSONS:
        for name in item['files']:
            assert code((LAB/name).read_text(),'source-code',name) in source, name
        assert code((LAB/'expected'/f's6{item["n"]}.txt').read_text(),'output','离线实跑标准输出') in source
    pages={p:Page(p) for p in ROOT.glob('*.html')}
    assert sum(len(p.lessons) for p in pages.values())==47
    for path,page in pages.items():
        assert all(n==1 for n in Counter(page.ids).values()), f'duplicate id: {path.name}'
        for href in page.links:
            url=urlsplit(href)
            if url.scheme or url.netloc: continue
            target=(path.parent/unquote(url.path)).resolve() if url.path else path
            assert target.exists(), f'missing link: {path.name} → {href}'
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, f'missing anchor: {href}'
    with zipfile.ZipFile(ROOT/'examples/stage6-examples.zip') as archive:
        for name in archive.namelist():
            rel=Path(name).relative_to('stage6')
            assert not any(x in {'.env','.runtime','__pycache__'} or x.startswith('.venv') for x in rel.parts)
            assert archive.read(name)==(LAB/rel).read_bytes(), f'ZIP mismatch: {name}'
        assert len(archive.namelist())==len(set(archive.namelist()))
        print(f'ZIP: {len(archive.namelist())} files match source; no secrets/runtime paths')
    print(f'HTML: 7 embedded lessons match files; {len(pages)} pages / 47 lessons / local links and anchors OK')


if __name__=='__main__': main()
