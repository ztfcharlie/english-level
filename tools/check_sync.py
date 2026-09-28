# -*- coding: utf-8 -*-
"""Keep data.json honest when the bilibili uploads change underneath us.

BVIDs are permanent, but an uploader can insert, delete or reorder 分P at any
time. Our player addresses episodes by page number, so an insert silently
shifts everything after it - the app would play the WRONG book and nothing
would look broken. This script re-reads each level and re-anchors our stored
episodes by BOOK TITLE, which survives reordering.

    python check_sync.py          # report only
    python check_sync.py --fix    # repair page numbers in data.json
"""
import json, io, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, video_info
from build_data import parse_part

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")


def norm_title(s):
    """Loose key for matching: case, punctuation and spacing all drift."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9一-鿿]+", " ", s)
    return " ".join(s.split())


def fetch_pages(op, mixin, bvid):
    res = video_info(op, mixin, bvid)
    code = res.get("code")
    if code != 0:
        return None, "接口返回 %s %s" % (code, res.get("message"))
    d = res.get("data") or {}
    pages = []
    for p in (d.get("pages") or []):
        raw = (p.get("part") or "").strip() or ("P%s" % p.get("page"))
        no, clean, notice = parse_part(raw)
        pages.append({"page": p.get("page"), "title": clean, "n": no,
                      "dur": p.get("duration") or 0, "notice": notice})
    if not pages:
        return None, "分P列表为空（可能已设为私密或删除）"
    return {"title": d.get("title"), "pages": pages}, None


def diff_level(rec, live):
    """Compare stored episodes against the live part list."""
    by_title = {}
    for p in live["pages"]:
        by_title.setdefault(norm_title(p["title"]), []).append(p)

    mapping, gone = {}, []
    for e in rec["episodes"]:
        bucket = by_title.get(norm_title(e["t"]))
        if bucket:
            mapping[e["i"]] = bucket.pop(0)["page"]
        else:
            gone.append(e)

    moved = {o: n for o, n in mapping.items() if o != n}
    stored_pages = {e["i"] for e in rec["episodes"]}
    added = [p for p in live["pages"] if p["page"] not in set(mapping.values())]
    # parts the uploader removed entirely
    return {"mapping": mapping, "gone": gone, "moved": moved,
            "added": added, "live_n": len(live["pages"])}


def main():
    fix = "--fix" in sys.argv
    with io.open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    op, mixin = init_session()
    report, dirty = [], False

    for rec in data["levels"]:
        lv = rec["level"]
        live, err = fetch_pages(op, mixin, rec["bvid"])
        if err:
            report.append((lv, "DEAD", err, None))
            continue
        d = diff_level(rec, live)
        if d["gone"]:
            report.append((lv, "MISSING", "%d 本找不到了: %s" % (
                len(d["gone"]), "、".join(e["t"][:18] for e in d["gone"][:4])), None))
        if d["moved"]:
            dirty = True
            sample = list(d["moved"].items())[:4]
            report.append((lv, "MOVED", "%d 个分P位置变了 (旧->新): %s" % (
                len(d["moved"]),
                ", ".join("%s->%s" % (a, b) for a, b in sample)), None))
            if fix:
                for e in rec["episodes"]:
                    if e["i"] in d["mapping"]:
                        e["i"] = d["mapping"][e["i"]]
                rec["episodes"].sort(key=lambda e: (e["n"] if e["n"] else 9999, e["i"]))
        if d["added"]:
            report.append((lv, "ADDED", "上传者新增了 %d 个分P（未纳入，可重跑 build_data.py）"
                           % len(d["added"]), None))
        if not (d["gone"] or d["moved"] or d["added"]):
            report.append((lv, "OK", "%d 本，无变化" % len(rec["episodes"]), None))
        time.sleep(1.2)

    order = {"DEAD": 0, "MISSING": 1, "MOVED": 2, "ADDED": 3, "OK": 4}
    report.sort(key=lambda r: order[r[1]])
    print("=" * 66)
    for lv, kind, msg, _ in report:
        mark = {"OK": "  ", "DEAD": "!!", "MISSING": "!!", "MOVED": " ~", "ADDED": " +"}[kind]
        print("%s %-3s %-8s %s" % (mark, lv, kind, msg))
    print("=" * 66)

    bad = [r for r in report if r[1] in ("DEAD", "MISSING")]
    moved = [r for r in report if r[1] == "MOVED"]
    print("正常 %d · 位置变动 %d · 有问题 %d"
          % (len(report) - len(bad) - len(moved), len(moved), len(bad)))

    if fix and dirty:
        data["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with io.open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("\n已修正 data.json 的 page 号。接着跑：python make_app.py")
    elif moved:
        print("\n位置有变动，加 --fix 可以自动修正。")
    if bad:
        print("\n有级别失效：去 RAZ-B站合集清单.md 的「备用源」换一个，")
        print("改 build_data.py 里的 OVERRIDE 再重跑 build_data.py。")


if __name__ == "__main__":
    main()
