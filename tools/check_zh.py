#!/usr/bin/env python3
"""Verify zhcn pages: <pre> blocks byte-identical to English, links prefixed,
no leftover untranslated banner."""
import re, sys, os
bad = 0
for f in sys.argv[1:]:
    en = open(f, encoding='utf-8').read()
    zh_path = os.path.join('zhcn', f)
    if not os.path.exists(zh_path):
        print('MISSING', zh_path); bad += 1; continue
    zh = open(zh_path, encoding='utf-8').read()
    pa = re.findall(r'<pre>.*?</pre>', en, re.S)
    pb = re.findall(r'<pre>.*?</pre>', zh, re.S)
    problems = []
    if pa != pb:
        problems.append('pre blocks differ (%d vs %d)' % (len(pa), len(pb)))
    body = re.sub(r'<p class="lang-switch">.*?</p>', '', zh, flags=re.S)
    if re.search(r'href="/(?!zhcn/)[^"]*docs/', body):
        problems.append('unprefixed docs link')
    if '本页尚未翻译' in zh:
        problems.append('translation banner still present')
    if 'lang-switch' not in zh:
        problems.append('no language switcher')
    if problems:
        print('FAIL', zh_path, problems); bad += 1
print('checked %d pages, %d problems' % (len(sys.argv) - 1, bad))
