# -*- coding: utf-8 -*-
"""Build the canonical AA..Z dataset from 惊叹号的英语世界's RAZ 蓝标 collection."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, video_info

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = ["AA"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
SEASON_VIDEO = "BV1fDF2esEzi"   # any member of the season works as an entry point

# Title shape: "RAZ N·80本(全)丨总词汇：52853词【阅读丨飞跃之旅·蓝标RAZ】"
RE_LEVEL = re.compile(r"RAZ\s*([A-Z]{1,2})\s*[·・]\s*(\d+)\s*本")
RE_VOCAB = re.compile(r"总词汇[：:]\s*([\d,]+)\s*词")

# Some levels in the season video are incomplete; swap in a fuller upload.
# V is missing 25 of 88 books in the 蓝标 cut, so we use a complete one.
OVERRIDE = {
    "V": {
        "bvid": "BV1YiA4zWEFv",
        "season_title": "Raz英语分级阅读|V级别(88本全)(每天进度:1本新，1本旧,拓展尝试中章书)",
        "claimed_books": 88,
        "note": "蓝标合集里 V 级缺 25 本，改用此完整版",
    },
}

# Episode part titles vary by level: "AA-01☆Farm Animals", "C-01·What Is at the Zoo",
# "N-64--Slithery Snakes", "X-98-Whale Sharks". Normalise them all.
RE_NOTICE = re.compile(r"^【[^】]*(?:简介|说明|必看|使用)[^】]*】")
RE_NUM = re.compile(r"^([A-Za-z]{1,3})\s*[-–—]\s*(\d+)\s*(.*)$")
RE_LEADSEP = re.compile(r"^[\s\-–—·☆★丨|:：.]+")


def parse_part(raw):
    """-> (book_no or None, clean_title, is_notice)"""
    s = (raw or "").strip()
    notice = False
    m = RE_NOTICE.match(s)
    if m:
        notice = True
        s = s[m.end():].strip()
    m = RE_NUM.match(s)
    if not m:
        return None, s, notice
    no = int(m.group(2))
    rest = RE_LEADSEP.sub("", m.group(3) or "").strip()
    return no, rest or s, notice


def get_season(op, mixin):
    res = video_info(op, mixin, SEASON_VIDEO)
    data = res.get("data") or {}
    season = data.get("ugc_season") or {}
    if not season:
        raise SystemExit("season not found")
    return season


def main():
    op, mixin = init_session()
    season = get_season(op, mixin)

    picked = {}
    for sec in (season.get("sections") or []):
        if "蓝标" not in (sec.get("title") or ""):
            continue
        for ep in (sec.get("episodes") or []):
            title = ep.get("title") or ""
            m = RE_LEVEL.search(title)
            if not m:
                continue
            lv = m.group(1).upper()
            if lv in picked or lv not in LEVELS:
                continue
            v = RE_VOCAB.search(title)
            picked[lv] = {
                "level": lv,
                "bvid": ep.get("bvid"),
                "season_title": title,
                "claimed_books": int(m.group(2)),
                "claimed_vocab": int(v.group(1).replace(",", "")) if v else None,
                "season_dur": (ep.get("arc") or {}).get("duration"),
            }
    print("levels found in season: %d -> %s" % (len(picked), ",".join(
        l for l in LEVELS if l in picked)))
    missing = [l for l in LEVELS if l not in picked]
    if missing:
        print("MISSING:", ",".join(missing))

    # Pull part lists for each level video.
    out = []
    for lv in LEVELS:
        rec = dict(picked.get(lv) or {})
        if not rec:
            continue
        if lv in OVERRIDE:
            rec.update(OVERRIDE[lv])
        try:
            res = video_info(op, mixin, rec["bvid"])
        except Exception as e:
            print("  !! %s %s" % (lv, e))
            time.sleep(2)
            continue
        d = res.get("data") or {}
        pages = d.get("pages") or []
        eps = []
        for p in pages:
            name = (p.get("part") or "").strip() or ("P%d" % p.get("page"))
            no, clean, notice = parse_part(name)
            eps.append({"i": p.get("page"), "t": clean, "n": no,
                        "d": p.get("duration") or 0, "x": notice})
        # Parts inside one upload are NOT in book order (e.g. N starts at book 64).
        # Sort by book number for display; `i` still holds the real page for the player.
        # A "notice" part is still a real book (its bracket prefix is just a housekeeping
        # banner), so it sorts by number like everything else - only its flag differs.
        eps.sort(key=lambda e: (e["n"] if e["n"] else 9999, e["i"]))

        # Book numbers the uploader's cut is missing, so the UI can say so plainly.
        nums = [e["n"] for e in eps if e["n"]]
        gaps = [i for i in range(1, (max(nums) + 1) if nums else 1) if i not in nums]
        rec.update({
            "title": d.get("title"),
            "pic": d.get("pic"),
            "owner": (d.get("owner") or {}).get("name"),
            "mid": (d.get("owner") or {}).get("mid"),
            "pubdate": d.get("pubdate"),
            "views": (d.get("stat") or {}).get("view"),
            "likes": (d.get("stat") or {}).get("like"),
            "favorites": (d.get("stat") or {}).get("favorite"),
            "n_parts": len(eps),
            "total_sec": d.get("duration"),
            "gaps": gaps,
            "episodes": eps,
        })
        flag = ""
        if rec["claimed_books"] and len(eps) < rec["claimed_books"] * 0.9:
            flag = "  <-- SHORT vs claim"
        print("%-3s %s parts=%-4d claim=%-4d %5.1fh %s" % (
            lv, rec["bvid"], len(eps), rec["claimed_books"],
            (d.get("duration") or 0) / 3600.0, flag))
        out.append(rec)
        time.sleep(1.2)

    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": {
            "season_title": season.get("title"),
            "season_id": season.get("id"),
            "mid": season.get("mid"),
            "uploader": "惊叹号的英语世界",
            "url": "https://space.bilibili.com/%s" % season.get("mid"),
        },
        "levels": out,
    }
    path = os.path.join(HERE, "data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    total = sum(r["n_parts"] for r in out)
    print("\nwrote %s: %d levels, %d episodes, %.1f hours" % (
        path, len(out), total, sum(r["total_sec"] or 0 for r in out) / 3600.0))


if __name__ == "__main__":
    main()
