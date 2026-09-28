# -*- coding: utf-8 -*-
"""Validate the built app: embedded JSON parses, shape is sane, no duplicate parts."""
import json, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with io.open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
    html = f.read()

m = re.search(r"const DATA = (\{.*?\});\s*\n\s*const BANDS", html, re.S)
if not m:
    print("FAIL: could not locate embedded DATA")
    sys.exit(1)
d = json.loads(m.group(1))

eps = sum(len(r["episodes"]) for r in d["levels"])
print("levels            : %d" % len(d["levels"]))
print("episodes          : %d" % eps)
print("hours             : %.1f" % (sum(r["total_sec"] or 0 for r in d["levels"]) / 3600.0))
print("uploader          : %s" % d["source"]["uploader"])

problems = []
for r in d["levels"]:
    pages = [e["i"] for e in r["episodes"]]
    if len(pages) != len(set(pages)):
        problems.append("%s: duplicate page numbers" % r["level"])
    if not isinstance(r.get("gaps"), list):
        problems.append("%s: missing gaps" % r["level"])
    for e in r["episodes"]:
        if not isinstance(e.get("i"), int) or not isinstance(e.get("d"), int):
            problems.append("%s: bad episode shape %r" % (r["level"], e))
            break

# books that appear twice under different parts (a quirk of the source upload,
# not of this pipeline - worth surfacing so nobody thinks it is a bug)
dupes = []
for r in d["levels"]:
    seen = {}
    for e in r["episodes"]:
        if e["n"] is None:
            continue
        seen.setdefault(e["n"], []).append(e["i"])
    for n, ps in seen.items():
        if len(ps) > 1:
            dupes.append("%s book %d -> parts %s" % (r["level"], n, ps))

print("shape problems    : %d %s" % (len(problems), problems[:5]))
print("duplicate books   : %d %s" % (len(dupes), dupes[:6]))
print("total gaps        : %d levels have gaps" % sum(1 for r in d["levels"] if r["gaps"]))
print("RESULT            : %s" % ("OK" if not problems else "PROBLEMS"))
