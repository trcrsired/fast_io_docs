#!/usr/bin/env python3
"""Helpers for producing the zhcn (Simplified Chinese) mirror of the docs.

Two modes:

  segs  <english.html>
        Print every translatable text span in document order as
        ``<index>\t<tag>\t<inner html>``.  Spans inside <pre>/<code>/<script>/
        <style> are never emitted, so code blocks are copied byte for byte by
        `apply`.

  apply <english.html> <map.txt> <out.html>
        Rebuild the page with the translations from <map.txt> in place, then
        fix it up for the Chinese site: <html lang="zh-CN">, /docs/ links
        rewritten to /zhcn/docs/, and the 中文/English switcher paragraph
        inserted after the first </h1>.

<map.txt> holds one ``index|translation`` per line.  A missing index keeps the
English text, so a page can be translated in several passes.
"""

import html
import os
import re
import sys
from html.parser import HTMLParser

SEGMENTABLE = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "caption",
    "figcaption", "dt", "dd", "summary", "title", "a", "span", "button",
    "label", "option", "div",
}
# tags whose content is never translated
OPAQUE = {"pre", "code", "script", "style", "kbd", "samp", "textarea"}


class Segmenter(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.starts = [0]  # offset of each line, to map (line, col) -> offset
        for line in text.splitlines(keepends=True):
            self.starts.append(self.starts[-1] + len(line))
        self.stack = []  # (tag, inner_start, inner_end, has_nested, has_text)
        self.segs = []   # (start, end, tag)

    def off(self):
        line, col = self.getpos()
        return self.starts[line - 1] + col

    # -- helpers -------------------------------------------------------
    def _open(self, tag, raw):
        start = self.off()
        inner_start = start + len(raw)
        opaque = any(t in OPAQUE for t, *_ in self.stack)
        self.stack.append([tag, inner_start, None, opaque, False])

    def handle_starttag(self, tag, attrs):
        self._open(tag, self.get_starttag_text() or "")

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                break
        else:
            return
        self._close(i)

    def _close(self, i):
        tag, inner_start, _, opaque, has_text = self.stack[i]
        inner_end = self.off()  # position of '</'
        nested = any(SENEST(s[0]) for s in self.stack[i + 1:])
        anchor = any(s[0] in SEGMENTABLE for s in self.stack[:i])
        for j in range(len(self.stack) - 1, i - 1, -1):
            del self.stack[j]
        if opaque or not has_text or nested or anchor:
            return
        if tag not in SEGMENTABLE:
            return
        body = self.text[inner_start:inner_end]
        if not body.strip():
            return
        if not re.search(r"[A-Za-z]{2}", strip_tags(body)):
            return
        self.segs.append((inner_start, inner_end, tag))

    def handle_data(self, data):
        if not data.strip():
            return
        for entry in self.stack:
            entry[4] = True

    def handle_entityref(self, name):
        self.handle_data("&" + name + ";")

    def handle_charref(self, name):
        self.handle_data("&#" + name + ";")


def SENEST(tag):
    return tag in SEGMENTABLE or tag in OPAQUE


def strip_tags(s):
    return re.sub(r"<[^>]*>", "", s)


def segments(text):
    p = Segmenter(text)
    p.feed(text)
    p.close()
    while p.stack:
        p._close(len(p.stack) - 1)
    return sorted(p.segs)


def normalise(inner):
    return " ".join(inner.split())


def cmd_segs(path):
    text = open(path, encoding="utf-8").read()
    for i, (s, e, tag) in enumerate(segments(text), 1):
        print("%d\t%s\t%s" % (i, tag, normalise(text[s:e])))


def cmd_apply(src, mapfile, out):
    text = open(src, encoding="utf-8").read()
    tmap = {}
    cur = None
    for line in open(mapfile, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        m = re.match(r"(\d+)\|", line)
        if m:
            cur = int(m.group(1))
            tmap[cur] = line[m.end():]
        elif cur is not None:            # continuation line
            tmap[cur] += "\n" + line
    # {{pre:N}} / {{seg}} placeholders copy source markup verbatim
    pres = re.findall(r"<pre>.*?</pre>", text, re.S)
    for k in list(tmap):
        body = tmap[k]
        body = re.sub(r"\{\{pre:(\d+)\}\}",
                      lambda m, pres=pres: pres[int(m.group(1)) - 1], body)
        tmap[k] = body

    segs = segments(text)
    out_text = []
    pos = 0
    for i, (s, e, tag) in enumerate(segs, 1):
        out_text.append(text[pos:s])
        seg = text[s:e]
        if i in tmap:
            body = tmap[i]
            if "\n" in seg:
                line_start = text.rfind("\n", 0, s) + 1
                indent = re.match(r"[ \t]*", text[line_start:]).group(0)
                out_text.append("\n%s  %s\n%s" % (indent, body, indent))
            else:
                out_text.append(body)
        else:
            out_text.append(seg)
        pos = e
    out_text.append(text[pos:])
    doc = "".join(out_text)

    # --- Chinese-site fixups -----------------------------------------
    doc = doc.replace('<html lang="en">', '<html lang="zh-CN">', 1)
    doc = re.sub(r'href="/docs/', 'href="/zhcn/docs/', doc)
    doc = re.sub(r'href="/zhcn/zhcn/', 'href="/zhcn/', doc)
    doc = doc.replace('href="/" class="main-button"', 'href="/zhcn/" class="main-button"')

    norm = os.path.abspath(src).replace(os.sep, "/")
    rel = norm.split("/docs/", 1)[1].rsplit("/", 1)[0]
    href = "/docs/" + rel + "/"
    switch = '<p class="lang-switch"><a href="%s">English</a></p>' % href
    doc, n = re.subn(r'<p class="lang-switch">.*?</p>', switch, doc, flags=re.S)
    if n == 0:
        if "</h1>" in doc:
            doc = doc.replace("</h1>", "</h1>\n    " + switch, 1)
        else:
            doc = doc.replace("<main>", "<main>\n    " + switch, 1)

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write(doc)
    missing = [i for i in range(1, len(segs) + 1) if i not in tmap]
    print("%s: %d segments, %d translated, missing %s"
          % (out, len(segs), len(tmap), missing if missing else "-"))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "segs":
        cmd_segs(sys.argv[2])
    elif len(sys.argv) >= 5 and sys.argv[1] == "apply":
        cmd_apply(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
        sys.exit(2)
