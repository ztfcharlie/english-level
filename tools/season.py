# -*- coding: utf-8 -*-
"""Dump the ugc_season (bilibili 合集) structure for a video."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, video_info

op, mixin = init_session()
bvid = sys.argv[1] if len(sys.argv) > 1 else "BV1fDF2esEzi"
res = video_info(op, mixin, bvid)
data = res.get("data") or {}
season = data.get("ugc_season") or {}
if not season:
    print("no season on", bvid)
    sys.exit(0)
print("SEASON: %s" % season.get("title"))
print("  id=%s ep_count=%s mid=%s" % (season.get("id"), season.get("ep_count"),
                                      (season.get("mid") or "")))
for sec in (season.get("sections") or []):
    eps = sec.get("episodes") or []
    print("  section %r -> %d episodes" % (sec.get("title"), len(eps)))
    for e in eps:
        arc = e.get("arc") or {}
        print("     %-38s %s  %ss" % ((e.get("title") or "")[:38],
                                      e.get("bvid"), arc.get("duration")))
