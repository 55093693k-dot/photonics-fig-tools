# -*- coding: utf-8 -*-
"""probe_download.py -- try several URLs, report status/headers/magic to a file.

Console here is GBK and shell capture is unreliable, so every probe writes a
UTF-8 log and (optionally) the payload.  Used to re-fetch reference PDFs whose
exact numbers must be read off a figure.

Usage
-----
    python probe_download.py --log out.txt --save refs/p.pdf --urls u1 u2 u3
"""
from __future__ import annotations

import argparse
import io
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", nargs="+", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--save", default=None)
    ap.add_argument("--save-if", default=None, help="only save when body starts with this")
    a = ap.parse_args()

    L = []
    for u in a.urls:
        req = urllib.request.Request(u, headers={
            "User-Agent": UA,
            "Accept": "application/pdf,text/html,*/*",
            "Referer": "https://ieeexplore.ieee.org/",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
                L.append("OK   %d  %s  ct=%s  bytes=%d  magic=%r"
                         % (r.status, u, r.headers.get("Content-Type"),
                            len(body), body[:8]))
                if len(body) <= 4000:
                    try:
                        L.append("     body> " + body.decode("utf-8", "replace"))
                    except Exception:  # noqa: BLE001
                        pass
                if a.save and (a.save_if is None or body[:len(a.save_if)] == a.save_if.encode()):
                    io.open(a.save, "wb").write(body)
                    L.append("     saved -> %s" % a.save)
        except Exception as e:  # noqa: BLE001 - probe, report everything
            L.append("FAIL %s  %s: %s" % (u, type(e).__name__, e))
    io.open(a.log, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("probe done -> %s" % a.log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
