#!/usr/bin/env python3
"""Restore byte-identical <pre> blocks in translated pages.

For every page where the Chinese copy's <pre> blocks differ from the English
source only in whitespace, replace them with the English ones verbatim."""
import re, sys, glob

def norm(s):
    return ' '.join(re.sub(r'<[^>]*>', ' ', s).split())

force = '--force' in sys.argv
fixed = skipped = 0
for f in sorted(glob.glob('zhcn/docs/**/index.html', recursive=True)):
    en_path = f[len('zhcn/'):]
    try:
        en = open(en_path, encoding='utf-8').read()
    except FileNotFoundError:
        continue
    zh = open(f, encoding='utf-8').read()
    pa = re.findall(r'<pre>.*?</pre>', en, re.S)
    pb = re.findall(r'<pre>.*?</pre>', zh, re.S)
    if pa == pb or not pb:
        continue
    if len(pa) != len(pb) or (not force and [norm(x) for x in pa] != [norm(x) for x in pb]):
        print('SKIP (content differs):', f)
        skipped += 1
        continue
    it = iter(pa)
    zh_new = re.sub(r'<pre>.*?</pre>', lambda m: next(it), zh, flags=re.S)
    open(f, 'w', encoding='utf-8').write(zh_new)
    fixed += 1
print('restored code blocks in %d pages, skipped %d' % (fixed, skipped))
