#!/usr/bin/env python3
"""Generate and validate the service-worker pre-cache list.

The service worker ships one request per page, so the list has to match the
tree exactly: a stale path makes the install log warnings, and a missing page
is unreachable offline. Run this after moving or adding pages.

    python3 tools/gen_sw.py           # rewrite the block in sw.js
    python3 tools/gen_sw.py --check   # fail if sw.js is out of date
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW = os.path.join(ROOT, "sw.js")
BEGIN = "/* BEGIN GENERATED PRECACHE */"
END = "/* END GENERATED PRECACHE */"

SHELL = [
    "/",
    "/zhcn/",
    "/style.css",
    "/script.js",
    "/sw-register.js",
    "/manifest.json",
    "/icons/logo.webp",
    "/icons/logo.png",
]

IMAGE_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg", ".svg", ".ico")


def page_urls() -> list[str]:
    urls = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        if "index.html" not in filenames:
            continue
        rel = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if rel == ".":
            urls.append("/")
        else:
            urls.append("/" + rel + "/")
    return urls


def image_urls() -> list[str]:
    urls = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [name for name in dirnames if name != ".git"]
        for name in filenames:
            if name.lower().endswith(IMAGE_SUFFIXES):
                rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
                urls.append("/" + rel.replace(os.sep, "/"))
    return urls


def build() -> list[str]:
    entries = list(SHELL)
    entries.extend(page_urls())
    entries.extend(image_urls())
    seen = set()
    result = []
    for url in entries:
        if url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def block(entries: list[str]) -> str:
    lines = [BEGIN, "const PRECACHE = ["]
    lines.extend(f'  "{url}",' for url in entries)
    lines.append("];")
    lines.append(END)
    return "\n".join(lines)


def current_entries(source: str) -> list[str]:
    start = source.index(BEGIN) + len(BEGIN)
    end = source.index(END)
    body = source[start:end]
    import re

    return re.findall(r'"([^"]+)"', body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    with open(SW, encoding="utf-8") as handle:
        source = handle.read()

    expected = build()
    actual = current_entries(source)

    if args.check:
        missing = [url for url in expected if url not in set(actual)]
        stale = [url for url in actual if url not in set(expected)]
        if missing or stale:
            print(f"sw.js pre-cache is out of date ({len(actual)} entries)")
            for url in missing:
                print("  missing:", url)
            for url in stale:
                print("  stale:  ", url)
            print("run: python3 tools/gen_sw.py")
            return 1
        print(f"sw.js pre-cache matches the tree ({len(actual)} entries)")
        return 0

    start = source.index(BEGIN)
    end = source.index(END) + len(END)
    updated = source[:start] + block(expected) + source[end:]
    with open(SW, "w", encoding="utf-8") as handle:
        handle.write(updated)
    print(f"wrote {len(expected)} pre-cache entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
