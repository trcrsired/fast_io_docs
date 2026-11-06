#!/usr/bin/env python3
"""Replace <pre> blocks written inline in a translation map with {{pre:N}}
placeholders that copy the corresponding source block byte for byte."""
import re, sys, pathlib

def norm(s):
    s = re.sub(r'<[^>]*>', ' ', s)
    return ' '.join(s.split())

src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
pres = re.findall(r'<pre>.*?</pre>', src, re.S)
keys = [norm(p) for p in pres]
mp = pathlib.Path(sys.argv[2])
out_lines = []
fixed = 0
for line in mp.read_text(encoding='utf-8').split('\n'):
    if '{{pre:' in line or '<pre>' not in line:
        out_lines.append(line)
        continue
    def repl(m):
        global fixed
        body = norm(m.group(0))
        for i, k in enumerate(keys):
            if k == body:
                fixed += 1
                return '{{pre:%d}}' % (i + 1)
        best, bi = -1, None
        for i, k in enumerate(keys):
            common = len(set(k.split()) & set(body.split()))
            if common > best:
                best, bi = common, i + 1
        fixed += 1
        return '{{pre:%d}}' % bi
    line = re.sub(r'<pre>.*?</pre>', repl, line, flags=re.S)
    out_lines.append(line)
mp.write_text('\n'.join(out_lines), encoding='utf-8')
print('replaced %d inline <pre> blocks' % fixed)
