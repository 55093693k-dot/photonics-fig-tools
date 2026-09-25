# -*- coding: utf-8 -*-
"""rasterize_pdf.py -- download (optional) + rasterize PDF pages to PNG.

Why: several design numbers must be READ OFF a figure (taper geometry, layer
order).  Guessing them is forbidden, and the numbers are only defensible if the
figure raster is reproducible.  This tool makes that one command.

Usage
-----
    python rasterize_pdf.py --pdf refs/p.pdf --pages 1,6 --dpi 200 --outdir refs/_pages
    python rasterize_pdf.py --url <url> --pdf refs/p.pdf ...      # fetch first

Only ASCII is printed, so the tool is safe to run on a console with a non-UTF-8
code page.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request


def fetch(url: str, dst: str) -> None:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/pdf,*/*",
    })
    with urllib.request.urlopen(req, timeout=90) as r, open(dst, "wb") as fh:
        fh.write(r.read())
    print("fetched %d bytes -> %s" % (os.path.getsize(dst), dst))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--url", default=None, help="download to --pdf before rasterizing")
    ap.add_argument("--pages", default="1", help="1-based, comma separated, or 'all'")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--outdir", default=None, help="default <pdf dir>/_pages")
    a = ap.parse_args()

    if a.url and not os.path.exists(a.pdf):
        fetch(a.url, a.pdf)
    if not os.path.exists(a.pdf):
        print("MISSING %s" % a.pdf)
        return 2

    import fitz  # pymupdf
    doc = fitz.open(a.pdf)
    print("pages=%d" % doc.page_count)
    idx = range(doc.page_count) if a.pages == "all" else \
        [int(p) - 1 for p in a.pages.split(",")]
    outdir = a.outdir or os.path.join(os.path.dirname(os.path.abspath(a.pdf)), "_pages")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.pdf))[0]
    for i in idx:
        pg = doc[i]
        pix = pg.get_pixmap(dpi=a.dpi)
        out = os.path.join(outdir, "%s_p%02d_%ddpi.png" % (base, i + 1, a.dpi))
        pix.save(out)
        print("p%02d %.0f x %.0f pt -> %dx%d px : %s (%d bytes)"
              % (i + 1, pg.rect.width, pg.rect.height, pix.width, pix.height,
                 out, os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
