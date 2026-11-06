#!/usr/bin/env python3
"""Wrap the body of every `int main` in a doc page in a herbception handler.

The whole point of chapter 11 is that I/O fails constantly: every open, read,
write, flush and scan can report an error.  Every example in the chapter must
therefore show the handler a reader is supposed to write:

    int main()
    {
        try
        {
            ...
        }
        catch throws (::std::error e)
        {
            ::fast_io::perrln(e);
            return 1;
        }
        return 0;
    }

Usage:
    python3 tools/herbwrap.py docs/11.io/01.fileio/index.html
    python3 tools/herbwrap.py --write --ch11
"""
import re, sys, glob

BLOCK_RE = re.compile(r'(<pre><code class="language-cpp">)(.*?)(</code></pre>)', re.S)
MAIN_RE = re.compile(r'\bint\s+main\s*\(')


def match_close(text, start, opener='(', closer=')'):
    depth = 0
    while start < len(text):
        if text[start] == opener:
            depth += 1
        elif text[start] == closer:
            depth -= 1
            if depth == 0:
                return start + 1
        start += 1
    return -1


def indent_unit(body):
    for line in body.split('\n'):
        if line.strip():
            lead = line[:len(line) - len(line.lstrip())]
            return lead or '\t'
    return '\t'


def wrap(code):
    """Return the rewritten code, or None when there is nothing to do."""
    m = MAIN_RE.search(code)
    if not m:
        return None
    paren = code.index('(', m.start())
    close = match_close(code, paren)
    if close < 0:
        return None
    brace = code.index('{', close)
    end = match_close(code, brace, '{', '}')
    if end < 0:
        return None
    body = code[brace + 1:end - 1]
    if 'catch throws' in body:
        return None
    unit = indent_unit(body)
    stripped = body.strip('\n')
    lines = stripped.split('\n')
    # the body keeps its own indentation and moves one level deeper, inside try
    inner = '\n'.join((unit + l) if l.strip() else '' for l in lines)
    tail_returns = lines and lines[-1].strip().startswith('return')
    handler = (
        f'{unit}try\n'
        f'{unit}{{\n'
        f'{inner}\n'
        f'{unit}}}\n'
        f'{unit}catch throws (::std::error e)\n'
        f'{unit}{{\n'
        f'{unit}{unit}::fast_io::perrln(e);\n'
        f'{unit}{unit}return 1;\n'
        f'{unit}}}\n'
    )
    if not tail_returns:
        handler += f'{unit}return 0;\n'
    head = code[:brace]
    # `int main() {` -> `int main()\n{`, matching the rest of the book
    head = head.rstrip()
    if not head.endswith('{'):
        head += '\n{'
    return head + '\n' + handler + code[end - 1:]


def process(path, write=False):
    src = open(path, encoding='utf-8').read()
    pieces, last, n = [], 0, 0
    for bm in BLOCK_RE.finditer(src):
        raw = bm.group(2)
        # the code block is HTML-escaped; the constructs we touch are ASCII
        new = wrap(raw)
        pieces.append(src[last:bm.start(2)])
        if new is None:
            pieces.append(raw)
        else:
            pieces.append(new)
            n += 1
        last = bm.end(2)
    pieces.append(src[last:])
    out = ''.join(pieces)
    if write and out != src:
        open(path, 'w', encoding='utf-8').write(out)
    return n


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    write = '--write' in sys.argv
    if '--ch11' in sys.argv:
        args = sorted(glob.glob('docs/11.io/**/index.html', recursive=True))
    total = 0
    for p in args:
        n = process(p, write=write)
        if n:
            print('%3d  %s' % (n, p))
        total += n
    print('TOTAL blocks wrapped:', total, '(dry run)' if not write else '')
