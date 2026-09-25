# -*- coding: utf-8 -*-
"""fig_index.py -- audit a figure directory against the figure-channel rule.

WHAT IT CHECKS
--------------
1. every PNG/JPEG in --figs gets a **channel** from the naming rules
   (`--rule CHANNEL=REGEX`, first match wins; anything unmatched = "external");
2. every figure whose channel is "external" must carry the channel label --
   i.e. a PNG tEXt chunk (key from fig_channel.CHUNK) containing the ASCII mark
   (fig_channel.MARK).  Missing chunk / missing mark => VIOLATION (exit 1);
3. each figure's bytes / pixels / md5 are recorded, and matched against any
   provenance JSON passed with --prov (a JSON that contains figure records with
   a "path" key, e.g. MATERIAL_FIGS.json / OFFICIAL_VIEWS.json) so
   the "engine / commands / bytes" evidence travels with the file name;
4. output: --index JSON (machine readable) + optional --md Markdown table.

WHY: the rule forbids quoting an external (matplotlib) figure as if it were
an official solver export.  Rather than trusting a report to say so, the label
lives IN the file and this tool reads it back -- "the file is the evidence".

Usage
-----
  python fig_index.py \
      --figs figs \
      --index out/FIGS_INDEX.json \
      --md out/figs_README.md \
      --rule official-monitor=_idx_ --rule official-view=_exportview_ \
      --prov out/MATERIAL_FIGS.json \
      --prov out/OFFICIAL_VIEWS.json

ASCII stdout only; exit code 1 = at least one violation.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fig_channel as FC  # noqa: E402

DEFAULT_RULES = [("official-monitor", r"_idx_"), ("official-view", r"_exportview_")]


def magic_and_px(path):
    """(kind, [w, h]) sniffed from the BYTES, not the extension  (historical note)."""
    with open(path, "rb") as fh:
        head = fh.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return "PNG", list(struct.unpack(">II", head[16:24]))
        if head[:2] == b"\xff\xd8":                    # JPEG: walk to a SOF marker
            fh.seek(2)
            while True:
                b = fh.read(1)
                if not b:
                    return "JPEG", []
                if b != b"\xff":
                    continue
                while b == b"\xff":
                    b = fh.read(1)
                mk = b[0]
                if mk in (0xD8, 0x01) or 0xD0 <= mk <= 0xD7:
                    continue
                ln = fh.read(2)
                if len(ln) < 2:
                    return "JPEG", []
                seg = struct.unpack(">H", ln)[0] - 2
                if mk in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    d = fh.read(5)
                    if len(d) < 5:
                        return "JPEG", []
                    h, w = struct.unpack(">HH", d[1:5])
                    return "JPEG", [w, h]
                fh.seek(seg, os.SEEK_CUR)
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return "GIF", []
    return "other", []


def md5_12(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:12]


def prov_records(paths):
    """basename -> {provenance_source, record} for every dict with a 'path' key."""
    out = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as fh:
                blob = json.load(fh)
        except Exception:
            continue
        stack = [blob]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                q = node.get("path")
                if isinstance(q, str) and q.lower().endswith(".png"):
                    out.setdefault(os.path.basename(q.replace("\\", "/")),
                                   {"provenance_source": os.path.basename(p),
                                    "record": node})
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return out


def classify(name, rules):
    for chan, rx in rules:
        if re.search(rx, name):
            return chan
    return "external"


def main():
    ap = argparse.ArgumentParser(description="figure-channel audit")
    ap.add_argument("--figs", required=True, help="directory holding the figures")
    ap.add_argument("--index", default=None, help="write the JSON index here")
    ap.add_argument("--md", default=None, help="write a Markdown table here")
    ap.add_argument("--rule", action="append", default=[],
                    help="CHANNEL=REGEX (repeatable); default: "
                         + ", ".join("%s=%s" % r for r in DEFAULT_RULES))
    ap.add_argument("--prov", action="append", default=[],
                    help="provenance JSON to cross-reference (repeatable)")
    ap.add_argument("--label-key", default=FC.CHUNK)
    ap.add_argument("--mark", default=FC.MARK)
    a = ap.parse_args()

    rules = []
    for s in a.rule:
        chan, _, rx = s.partition("=")
        rules.append((chan.strip(), rx.strip()))
    if not rules:
        rules = list(DEFAULT_RULES)

    names = sorted(f for f in os.listdir(a.figs)
                   if os.path.isfile(os.path.join(a.figs, f))
                   and f.lower().endswith((".png", ".jpg", ".jpeg")))
    prov = prov_records(a.prov)

    figs, viol, chan_count = [], [], {}
    for nm in names:
        p = os.path.join(a.figs, nm)
        kind, px = magic_and_px(p)
        chan = classify(nm, rules)
        chunk = FC.read_text(p)
        lab = chunk.get(a.label_key, "")
        if chan == "external":
            ok = bool(lab) and a.mark in lab
        else:
            ok = True                      # official files need no label
        rec = {"name": nm, "path": p, "bytes": os.path.getsize(p), "kind": kind,
               "px": px, "md5": md5_12(p), "channel": chan,
               "label_ok": bool(ok), "label": lab[:200]}
        if chan == "external" and kind != "PNG":
            rec["note"] = "non-PNG: no tEXt channel -> label cannot be audited"
        if nm in prov:
            rec["provenance_source"] = prov[nm]["provenance_source"]
            r = prov[nm]["record"]
            rec["provenance"] = {k: r[k] for k in
                                 ("engine", "view", "commands", "bytes", "px",
                                  "md5", "monitor", "span", "note")
                                 if k in r}
        if not rec["label_ok"]:
            viol.append("%s [%s] missing the %s label" % (nm, chan, a.label_key))
        chan_count[chan] = chan_count.get(chan, 0) + 1
        figs.append(rec)

    out = {"tool": "fig_index.py", "config": "channel rules from --rule",
           "figs_dir": os.path.abspath(a.figs),
           "scanned": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "rules": [{"channel": c, "regex": r} for c, r in rules],
           "n_figures": len(figs), "n_by_channel": chan_count,
           "n_violations": len(viol), "violations": viol, "figures": figs}
    if a.index:
        with open(a.index, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, ensure_ascii=False)

    lines = ["# figure index (channel rule)", "",
             "Auto-generated by `fig_index.py` on %s. "
             "Do not hand-edit: regenerate." % out["scanned"], "",
             "**Channel rule**: a figure drawn by an official "
             "Lumerical export (`addindex`+`image`+`exportfigure` = official-monitor, "
             "`exportview` = official-view) is solver evidence; a **matplotlib** "
             "figure is a human re-projection and is *not* equivalent. External "
             "figures need prior user approval and carry an on-figure label plus "
             "a PNG `%s` metadata chunk -- that chunk is what the `label` column "
             "asserts." % a.label_key, "",
             "| figure | channel | bytes | px | md5 | label | provenance |",
             "|---|---|---|---|---|---|---|"]
    for r in figs:
        lines.append("| `%s` | %s | %d | %s | `%s` | %s | %s |" % (
            r["name"], r["channel"], r["bytes"],
            "x".join(str(v) for v in r["px"]) or "?",
            r["md5"], "OK" if r["label_ok"] else "**MISSING**",
            r.get("provenance_source", "-")))
    lines += ["", "Totals: %s | violations: %d" % (
        ", ".join("%s=%d" % kv for kv in sorted(chan_count.items())), len(viol)), ""]
    if a.md:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    print("figs=%d  %s  violations=%d"
          % (len(figs), " ".join("%s=%d" % kv for kv in sorted(chan_count.items())),
             len(viol)))
    for v in viol:
        print("  VIOLATION %s" % v)
    for r in figs:
        print("  %-46s %-17s %8d B %s %s" % (
            r["name"], r["channel"], r["bytes"],
            "x".join(str(v) for v in r["px"]) or "?", r["md5"]))
    if a.index:
        print("WROTE %s" % a.index)
    if a.md:
        print("WROTE %s" % a.md)
    return 1 if viol else 0


if __name__ == "__main__":
    sys.exit(main())

