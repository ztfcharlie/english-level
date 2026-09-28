# -*- coding: utf-8 -*-
"""Verify candidate collections: real part count, episode list, cover art."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, video_info

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

# Curated primary candidate per level, from analyze.py output.
PRIMARY = {
    "AA": "BV19T4y1M7GE", "A": "BV18bELzWEuk", "B": "BV1GkFdzwE2W",
    "C": "BV12e78zpEjL", "D": "BV1CecszFEto", "E": "BV1W54y1d75m",
    "F": "BV1bz411b7qx", "G": "BV1RUZ4B2EZG", "H": "BV1W5411t75F",
    "I": "BV1LK4y1k79C", "J": "BV1n64y1M7jT", "K": "BV1Bf4y1S7X8",
    "L": "BV1e54y1D7CU", "M": "BV1ue411W7V1", "N": "BV1fDF2esEzi",
    "O": "BV1GQFSeHEWk", "P": "BV18bFZeuEBF", "Q": "BV1fbFoeJEXJ",
    "R": "BV1oYFoe2Ea3", "S": "BV1f8FoeUEeM", "T": "BV1Q1FoeBEJq",
    "U": "BV1rvF6e3EHB", "V": "BV1hfPYejEAp", "W": "BV1tUPieDEsf",
    "X": "BV1WT9RYKEu6", "Y": "BV1hBLNzdEbv", "Z": "BV1uDGez8EPQ",
}

# Second choice, used when the primary fails verification.
ALT = {
    "AA": "BV1bhoLBiEyD", "A": "BV18r4y1K7Td", "B": "BV1Ds78zbEJa",
    "C": "BV1AwFozEEts", "D": "BV1Vt4y1K7ph", "E": "BV1KP411c7Cc",
    "F": "BV1RG4y1Z7cG", "G": "BV1qi4y187eP", "H": "BV1BkZ4BQEww",
    "I": "BV17jcMzBEgT", "J": "BV13EFDzVEHe", "K": "BV1DjZPBgEHc",
    "L": "BV1kuZZByEib", "M": "BV1paZfBUExA", "N": "BV1ABfABcE37",
    "O": "BV1ukf1BtEgj", "P": "BV1bCf1BoEBn", "Q": "BV1ZxfsBmEsN",
    "R": "BV13FfsBiEhj", "S": "BV1gpfvBhEFo", "T": "BV1ptA2zhEZB",
    "U": "BV16JA4zNEoq", "V": "BV1YiA4zWEFv", "W": "BV15oA8zqEra",
    "X": "BV1XMAvzyEnW", "Y": "BV1mMPGzgEFr", "Z": "BV1BmPVzaEeX",
}


def norm(data):
    """Flatten a view API response into our own episode schema."""
    pages = data.get("pages") or []
    eps = []
    for p in pages:
        eps.append({
            "page": p.get("page"),
            "title": (p.get("part") or "").strip() or ("P%d" % p.get("page")),
            "dur": p.get("duration") or 0,
        })
    season = data.get("ugc_season") or {}
    return {
        "bvid": data.get("bvid"),
        "aid": data.get("aid"),
        "title": data.get("title"),
        "desc": (data.get("desc") or "")[:400],
        "pic": data.get("pic"),
        "owner": (data.get("owner") or {}).get("name"),
        "mid": (data.get("owner") or {}).get("mid"),
        "duration": data.get("duration"),
        "pubdate": data.get("pubdate"),
        "stat": {k: (data.get("stat") or {}).get(k)
                 for k in ("view", "like", "favorite", "coin")},
        "n_pages": len(eps),
        "n_season": len((season.get("sections") or [{}])[0].get("episodes") or [])
        if season else 0,
        "season_title": season.get("title"),
        "episodes": eps,
    }


def fetch(op, mixin, bvid):
    try:
        res = video_info(op, mixin, bvid)
    except Exception as e:
        return {"bvid": bvid, "error": str(e)}
    if res.get("code") != 0:
        return {"bvid": bvid, "error": "code %s %s" % (res.get("code"), res.get("message"))}
    return norm(res.get("data") or {})


def main():
    which = sys.argv[1:] or list(PRIMARY)
    op, mixin = init_session()
    result = {}
    for lv in which:
        for tag, table in (("primary", PRIMARY), ("alt", ALT)):
            bv = table.get(lv)
            if not bv:
                continue
            info = fetch(op, mixin, bv)
            if "error" in info:
                print("%-3s %-8s %-8s ERROR %s" % (lv, tag, bv, info["error"]))
                time.sleep(1.5)
                continue
            print("%-3s %-8s %s  parts=%-4d season=%-4d %-9s %s" % (
                lv, tag, bv, info["n_pages"], info["n_season"],
                "%dmin" % ((info["duration"] or 0) // 60), (info["title"] or "")[:44]))
            if tag == "primary":
                result[lv] = info
            else:
                result.setdefault(lv + "_alt", info)
            break
        time.sleep(1.5)
    with open(os.path.join(HERE, "levels.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("\nwrote levels.json with %d levels" % len([k for k in result if not k.endswith("_alt")]))


if __name__ == "__main__":
    main()
