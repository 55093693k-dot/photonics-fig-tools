# -*- coding: utf-8 -*-
"""oa_locate.py -- find openly accessible copies of a paper from its DOI.

Why: publisher sites (IEEE/Optica) answer scripted requests with 418/403, so
"we cannot re-read the figure" would otherwise block a design decision.  The
OpenAlex API is not bot-blocked and lists every OA location (publisher,
repository, arXiv, ...) with a direct pdf_url.

Usage
-----
    python oa_locate.py --doi 10.1109/JPHOT.2019.2926823 --out refs/_oa.json
    python oa_locate.py --doi 10.1364/OE.23.016289 --out refs/_oa2.json
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request

API = "https://api.openalex.org/works/doi:%s?mailto=your-email@example.com"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    req = urllib.request.Request(API % a.doi, headers={"User-Agent": "oa-locate/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)

    def loc(l):
        src = l.get("source") or {}
        return {"pdf_url": l.get("pdf_url"), "landing": l.get("landing_page_url"),
                "host": src.get("host_organization_name"), "name": src.get("display_name"),
                "oa": l.get("is_oa"), "version": l.get("version")}

    out = {
        "doi": a.doi,
        "title": d.get("title"),
        "year": d.get("publication_year"),
        "oa": d.get("open_access"),
        "best_pdf": (d.get("best_oa_location") or {}).get("pdf_url"),
        "locations": [loc(l) for l in (d.get("locations") or [])],
    }
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print("wrote %s : %d location(s), oa=%s" % (a.out, len(out["locations"]), out["oa"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
