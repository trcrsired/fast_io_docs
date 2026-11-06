#!/usr/bin/env python3
"""Insert `noexcept` / `throws` into every function definition in a doc page.

The tutorial's own rule (Ch6.16) is that no function may be left without an
error contract.  This tool finds every function definition / declaration in
the C++ code blocks of a page, decides between `noexcept` and `throws` (a
function that performs I/O, allocates, or constructs a string/vector is
`throws`; everything else is `noexcept`), and inserts the specifier in the
escape-safe position of the raw HTML.

A bare declaration copies the contract of the definition with the same name
anywhere on the same page, because the specification is part of the function
type and the compiler requires both to agree.

Usage:
    python3 tools/markspec.py docs/06.function/01.whatisfunction/index.html
    python3 tools/markspec.py --write --all
"""
import re, sys, glob, html

BLOCK_RE = re.compile(r'(<pre><code class="language-cpp">)(.*?)(</code></pre>)', re.S)

KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'return', 'sizeof', 'static_assert',
            'alignas', 'decltype', 'throw', 'operator', 'main', 'do', 'try', 'template',
            'else', 'case', 'new', 'delete', 'co_return', 'co_await', 'co_yield', 'defined'}
RET_TYPES = {'void', 'int', 'auto', 'bool', 'char', 'double', 'float', 'long', 'short',
             'unsigned', 'signed', 'size_t', 'constexpr', 'consteval', 'static', 'inline',
             'explicit', 'const', 'template', 'constinit', 'export', 'decltype', 'typename'}

# An operation that can fail: printing, scanning, allocation, device I/O.
THROWS_RE = re.compile(
    r'\b(?:print|println|scan|perr|perrln|print_freestanding|concat_fast_io'
    r'|push_back|emplace_back|resize|reserve|to<'
    r'|obuf_file|ibuf_file|iobuf_file|native_file|win32_file|nt_file|wine_file'
    r'|c_file|c_io_observer|win32_io_observer|nt_io_observer|wine_io_observer'
    r'|native_io_observer|io_observer|ibuf_white_hole|native_white_hole'
    r'|string|vector|deque|list|map|set|open_mode|transmit|read_all|write_all'
    r'|f?print[fs]?|fopen|fclose|fflush|fread|fwrite|fgetc|fputc|fputs|fgets|puts|printf'
    r'|std::cout|std::cin|std::cerr|std::clog)\b')


def decode_with_map(raw):
    """Decode raw HTML to text, returning (text, raw_index_of_each_char)."""
    out, idx, i = [], [], 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == '<':
            j = raw.find('>', i)
            if j < 0:
                out.append(c); idx.append(i); i += 1; continue
            i = j + 1
            continue
        if c == '&':
            j = raw.find(';', i)
            if 0 < j - i <= 10:
                ent = html.unescape(raw[i:j + 1])
                if len(ent) == 1:
                    out.append(ent); idx.append(i); i = j + 1; continue
        out.append(c); idx.append(i); i += 1
    return ''.join(out), idx


def match_brace(text, start):
    """Return the index just past the `}` matching the `{` at `start`."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def match_close(text, start):
    """Return the index just past the `)` matching the `(` at `start`."""
    depth = 0
    while start < len(text):
        if text[start] == '(':
            depth += 1
        elif text[start] == ')':
            depth -= 1
            if depth == 0:
                return start + 1
        start += 1
    return -1


_ident = re.compile(r'[A-Za-z_]\w*')
SPEC_WORDS = {'const', 'volatile', 'noexcept', 'throws', 'override', 'final', '&', '&&'}
_spec_ident = re.compile(r'[A-Za-z_]\w*|&&|&')


def scan_spec(code, pos):
    """Consume the specifier sequence that follows a parameter list.

    Returns (spec_text, terminator_index, terminator_char).  Parentheses are
    balanced, so `noexcept(noexcept(f(x)))` is consumed as one specifier.
    """
    start = pos
    n = len(code)
    while pos < n:
        while pos < n and code[pos] in ' \t\r\n':
            pos += 1
        if pos >= n:
            break
        if code[pos] in '{;:':
            return code[start:pos].strip(), pos, code[pos]
        m = _spec_ident.match(code, pos)
        if not m or m.group(0) not in SPEC_WORDS:
            return code[start:pos].strip(), pos, None
        pos = m.end()
        while pos < n and code[pos] in ' \t\r\n':
            pos += 1
        if pos < n and code[pos] == '(':
            close = match_close(code, pos)
            if close < 0:
                return code[start:pos].strip(), pos, None
            pos = close
    return code[start:pos].strip(), pos, None


def scan_block(code):
    """Yield one dict per function definition / declaration found in `code`.

    A candidate starts a line (or follows `;`, `{`, `}`); its head runs to the
    first `(` outside template arguments, and the parameter list is matched by
    balancing parentheses, so parameters such as `int (*op)(int, int)` work.
    """
    n = len(code)
    i = 0
    while i < n:
        if i and code[i - 1] not in '\n;{}':
            i += 1
            continue
        while i < n and code[i] in ' \t':
            i += 1
        m = _ident.match(code, i)
        if not m:
            i += 1
            continue
        depth_angle = 0
        j = i
        open_paren = -1
        while j < n:
            c = code[j]
            if c == '<':
                depth_angle += 1
            elif c == '>':
                depth_angle -= 1
            elif c == '(' and depth_angle <= 0:
                open_paren = j
                break
            elif c in ';{}=)':
                break
            j += 1
        if open_paren < 0:
            i += 1
            continue
        head = code[i:open_paren]
        names = list(_ident.finditer(head))
        if not names:
            i += 1
            continue
        # a call expression is not a declaration: `return n * factorial(n - 1)`
        if names[0].group(0) in KEYWORDS or names[0].group(0) == 'return':
            i += 1
            continue
        name = names[-1].group(0)
        ret = head[:names[-1].start()].strip()
        close = match_close(code, open_paren)
        if close < 0:
            i += 1
            continue
        params = code[open_paren + 1:close - 1]
        spec, term_pos, term = scan_spec(code, close)
        if term is not None:
            body = code[term_pos:match_brace(code, term_pos)] if term == '{' else ''
            yield dict(ret=ret, name=name, params=params.strip(), spec=spec, term=term,
                       term_pos=term_pos, body=body,
                       has_spec=bool(re.search(r'\b(?:noexcept|throws)\b', spec)))
        i += 1


def plausible(ret):
    if not ret:
        return False
    words = ret.split()
    if words[0] in RET_TYPES:
        return True
    return ret.endswith(('>', '*', '&'))


def classify(fn, page_specs):
    """Decide the error contract for one function (None = leave untouched)."""
    if fn['has_spec']:
        return None
    if fn['term'] != '{':
        return page_specs.get(fn['name'], 'noexcept')
    return 'throws' if THROWS_RE.search(fn['body']) else 'noexcept'


# `dup`/`dup2` are libc functions whose declaration already exists in
# <unistd.h>; repeating them with a different spec would not compile.
SKIP = {'dup', 'dup2', 'malloc', 'free', 'write', 'read', 'open', 'close'}


def process(path, write=False, verbose=True):
    src = open(path, encoding='utf-8').read()
    # pass 1: a definition anywhere on the page fixes the contract that a bare
    # declaration of the same function must repeat
    page_specs = {}
    for bm in BLOCK_RE.finditer(src):
        code, _ = decode_with_map(bm.group(2))
        for fn in scan_block(code):
            if fn['term'] == '{' and not fn['has_spec'] and plausible(fn['ret']):
                page_specs[fn['name']] = classify(fn, {})

    pieces, last, report = [], 0, []
    for bm in BLOCK_RE.finditer(src):
        raw = bm.group(2)
        code, idx = decode_with_map(raw)
        inserts, seen = [], set()
        for fn in scan_block(code):
            if fn['name'] in KEYWORDS or fn['name'] in SKIP or not plausible(fn['ret']):
                continue
            if fn['term_pos'] in seen:      # `template <...>` line + signature line
                continue
            seen.add(fn['term_pos'])
            spec = classify(fn, page_specs)
            if spec is None:
                continue
            inserts.append((idx[fn['term_pos']], spec, fn))
        inserts.sort(key=lambda t: t[0], reverse=True)
        new_raw = raw
        for raw_pos, spec, fn in inserts:
            pos = raw_pos
            while pos > 0 and new_raw[pos - 1] in ' \t\r\n':
                pos -= 1
            new_raw = new_raw[:pos] + ' ' + spec + new_raw[pos:]
            report.append((fn['ret'].replace('\n', ' ') + ' ' + fn['name'] + '()', spec))
        pieces.append(src[last:bm.start(2)])
        pieces.append(new_raw)
        last = bm.end(2)
    pieces.append(src[last:])
    out = ''.join(pieces)
    if write and out != src:
        open(path, 'w', encoding='utf-8').write(out)
    if verbose:
        for sig, spec in report:
            print('  %-58s %s' % (sig, spec))
    return len(report)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    write = '--write' in sys.argv
    if '--all' in sys.argv:
        args = sorted(glob.glob('docs/**/index.html', recursive=True))
    total = 0
    for p in args:
        n = process(p, write=write)
        if n:
            print('%s: %d specifier(s)%s' % (p, n, '' if write else ' (dry run)'))
        total += n
    print('TOTAL:', total)
