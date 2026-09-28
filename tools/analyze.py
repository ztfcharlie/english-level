# -*- coding: utf-8 -*-
"""Group the raw scan by uploader to find systematic AA..Z collections."""
import json, os, re, collections

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
LEVELS = ["AA"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]


def load_all():
    by_level = {}
    for lv in LEVELS:
        p = os.path.join(RAW, "%s.json" % lv)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                by_level[lv] = json.load(f)
    return by_level


def level_re(lv):
    if lv == "AA":
        return re.compile(r"\bAA\b|AA\s*级|aa级", re.I)
    return re.compile(r"(?<![A-Za-z])%s\s*级|(?<![A-Za-z])%s级|\bRAZ[\s\-]*%s\b" % (lv, lv, lv), re.I)


def main():
    by_level = load_all()
    # author -> set of levels they appear in
    authors = collections.defaultdict(lambda: collections.defaultdict(int))
    for lv, rows in by_level.items():
        for r in rows:
            if r.get("author"):
                authors[r["author"]][lv] += 1

    ranked = sorted(authors.items(), key=lambda kv: -len(kv[1]))
    print("=== Uploaders covering the most levels ===")
    for a, lvmap in ranked[:18]:
        lvs = [l for l in LEVELS if l in lvmap]
        print("%-22s levels=%-3d  %s" % (a[:22], len(lvs), ",".join(lvs)))

    print("\n=== Best per-level candidate (title matches level + collection-ish) ===")
    COLL = re.compile(r"全|合集|全集|本|册|套|级")
    best = {}
    for lv in LEVELS:
        rows = by_level.get(lv, [])
        scored = []
        for r in rows:
            t = r["title"]
            s = 0
            if level_re(lv).search(t):
                s += 10
            if r["hits"] > 1:
                s += 4
            if COLL.search(t):
                s += 3
            # bonus for explicit "N本(全)" style completeness claims
            if re.search(r"\d+\s*本", t):
                s += 5
            if re.search(r"全\s*\d+|\(\s*全\s*\)|（全）|全集", t):
                s += 6
            if re.search(r"AA\s*-\s*Z|AA-Z", t, re.I):
                s += 8
            play = r.get("play") or 0
            s += min(play / 200000.0, 6)
            scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        best[lv] = scored[:5]
        print("\n--- %s ---" % lv)
        for s, r in scored[:5]:
            print("  %5.1f %s %-11s %-22s %s" % (
                s, r["bvid"], r["duration"], (r.get("author") or "")[:20], r["title"][:60]))

    with open(os.path.join(os.path.dirname(RAW), "best.json"), "w", encoding="utf-8") as f:
        json.dump({lv: [dict(r, score=s) for s, r in v] for lv, v in best.items()},
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
