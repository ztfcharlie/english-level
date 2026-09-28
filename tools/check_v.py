# -*- coding: utf-8 -*-
"""Check the V-level fallback upload and sample episode-title formats."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, video_info

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    data = json.load(f)

print("=== episode title samples ===")
for lv in ("AA", "C", "N", "X"):
    rec = next((r for r in data["levels"] if r["level"] == lv), None)
    if not rec:
        continue
    print("\n[%s] %s  (%d parts)" % (lv, rec["bvid"], rec["n_parts"]))
    for e in rec["episodes"][:6]:
        print("   p%-3s %-52s %ss" % (e["i"], e["t"][:52], e["d"]))
    print("   ...")
    for e in rec["episodes"][-2:]:
        print("   p%-3s %-52s %ss" % (e["i"], e["t"][:52], e["d"]))

# What is V missing?
v = next((r for r in data["levels"] if r["level"] == "V"), None)
if v:
    print("\n=== V current parts (%d) ===" % v["n_parts"])
    for e in v["episodes"]:
        print("   p%-3s %-58s %ss" % (e["i"], e["t"][:58], e["d"]))

op, mixin = init_session()
for bv in ("BV1YiA4zWEFv", "BV16JA4zNEoq"):
    try:
        res = video_info(op, mixin, bv)
        d = res.get("data") or {}
        print("\nALT %s: %s | parts=%d dur=%.1fh" % (
            bv, (d.get("title") or "")[:60], len(d.get("pages") or []),
            (d.get("duration") or 0) / 3600.0))
        for p in (d.get("pages") or [])[:8]:
            print("   p%-3s %-54s %ss" % (p.get("page"), (p.get("part") or "")[:54],
                                          p.get("duration")))
    except Exception as e:
        print("ALT %s error %s" % (bv, e))
