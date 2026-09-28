# -*- coding: utf-8 -*-
"""Scan bilibili for RAZ collections across every level AA..Z."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, search, strip

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
os.makedirs(OUT, exist_ok=True)

LEVELS = ["AA"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]

# Query templates per level. Kept small to stay polite to the API.
def queries(level):
    if level == "AA":
        return ["RAZ AA级 全集", "RAZ AA 合集 99本"]
    return ["RAZ %s级 全集" % level, "RAZ %s级 合集 全" % level]


def main():
    only = sys.argv[1:] or LEVELS
    op, mixin = init_session()
    summary = []
    for lv in only:
        bucket = {}
        for q in queries(lv):
            try:
                res = search(op, mixin, q)
            except Exception as e:
                print("  !! %s %r -> %s" % (lv, q, e))
                continue
            if res.get("code") != 0:
                print("  !! %s %r -> code %s" % (lv, q, res.get("code")))
                time.sleep(2)
                continue
            for it in (res.get("data") or {}).get("result") or []:
                bv = it.get("bvid")
                if not bv:
                    continue
                rec = bucket.setdefault(bv, {
                    "bvid": bv,
                    "title": strip(it.get("title")),
                    "author": it.get("author"),
                    "mid": it.get("mid"),
                    "duration": it.get("duration"),
                    "play": it.get("play"),
                    "danmaku": it.get("video_review"),
                    "pubdate": it.get("pubdate"),
                    "desc": strip(it.get("description"))[:300],
                    "pic": it.get("pic"),
                    "hits": 0,
                })
                rec["hits"] += 1
            time.sleep(1.5)
        # keep anything that matched more than one query first, then by play count
        rows = sorted(bucket.values(), key=lambda r: (-r["hits"], -(r["play"] or 0)))
        path = os.path.join(OUT, "%s.json" % lv)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        summary.append((lv, len(rows)))
        print("[%s] %d candidates" % (lv, len(rows)))
        for r in rows[:6]:
            print("    %s play=%-8s %-9s %s" % (
                r["bvid"], r["play"], r["duration"], r["title"][:56]))
    print("\nTOTAL:", sum(n for _, n in summary))


if __name__ == "__main__":
    main()
