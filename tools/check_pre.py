#!/usr/bin/env python3
"""Reject raw '<' inside <pre> blocks.

A code block must escape every angle bracket that belongs to the code:
`#include <fast_io.h>` renders as `#include ` because the browser eats
`<fast_io.h>` as a bogus tag, and `vector<int>` renders as `vector`. The
text is silently gone, so only a scanner can catch it.

Usage: python3 tools/check_pre.py $(find docs zhcn -name index.html)
"""
import re
import sys

KNOWN = set("""code pre span em strong b i a br div table tr td th ul ol li p h1 h2 h3
h4 h5 h6 sub sup samp kbd var mark small wbr del ins u s abbr cite q time svg path g circle
line rect polyline polygon text tspan use defs stop clippath mask symbol title desc style
script""".split())
TAG = re.compile(r'</?([a-zA-Z0-9]+)[^<>]*>')

bad = 0
for path in sys.argv[1:]:
    try:
        text = open(path, encoding='utf-8').read()
    except OSError:
        continue
    hits = []
    for block in re.findall(r'<pre>.*?</pre>', text, re.S):
        pos = 0
        while pos < len(block):
            if block[pos] != '<':
                pos += 1
                continue
            m = TAG.match(block, pos)
            if m and m.group(1).lower() in KNOWN:
                pos = m.end()
                continue
            line = block.count('\n', 0, pos) + 1
            snippet = ' '.join(block[pos:pos + 40].split())
            hits.append('line %d: %s' % (line, snippet))
            pos += 1
    if hits:
        bad += 1
        print('FAIL', path)
        for h in hits[:5]:
            print('   ', h)
print('checked %d pages, %d with raw markup in <pre>' % (len(sys.argv) - 1, bad))
sys.exit(1 if bad else 0)
