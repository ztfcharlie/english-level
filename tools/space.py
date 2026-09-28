# -*- coding: utf-8 -*-
"""List every upload from a bilibili user, so we can map level -> video precisely."""
import json, os, sys, time, re, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, get_json, wbi_sign, strip, UA

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")


def find_mid(name):
    for lv in ["AA"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]:
        p = os.path.join(RAW, "%s.json" % lv)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for r in json.load(f):
                if r.get("author") == name and r.get("mid"):
                    return r["mid"]
    return None


# dm_* params are client-fingerprint fields bilibili's risk control expects.
# Values below are the well-known benign constants the web player sends.
DM = {
    "dm_img_list": "[]",
    "dm_img_str": "V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ",
    "dm_cover_img_str": "QU5HTEUgKEludGVsLCBJbnRlbChSKSBVSEQgR3JhcGhpY3MgNjMwKSBPcGVuR0wgRVMgMy4wIChDaHJvbWl1bSksIE9wZW5HTCA0LjYp",
    "dm_img_inter": '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}',
}


def warmup(op, mid):
    """Hit the space HTML page so we pick up the cookies risk control wants."""
    req = urllib.request.Request("https://space.bilibili.com/%s/video" % mid)
    req.add_header("User-Agent", UA)
    try:
        op.open(req, timeout=20).read()
    except Exception:
        pass


def list_space(op, mixin, mid, max_pages=8):
    out, seen = [], set()
    for pn in range(1, max_pages + 1):
        params = {"mid": mid, "ps": 30, "pn": pn, "order": "pubdate",
                  "platform": "web", "web_location": "1550101",
                  "order_avoided": "true", "tid": 0, "keyword": "",
                  "index": 0, "voice_balance": 1}
        params.update(DM)
        url = "https://api.bilibili.com/x/space/wbi/arc/search?" + wbi_sign(params, mixin)
        try:
            res = get_json(op, url)
        except Exception as e:
            print("  !! page %d: %s" % (pn, e))
            break
        if res.get("code") != 0:
            print("  !! page %d code=%s %s" % (pn, res.get("code"), res.get("message")))
            break
        vlist = ((res.get("data") or {}).get("list") or {}).get("vlist") or []
        if not vlist:
            break
        for v in vlist:
            bv = v.get("bvid")
            if bv and bv not in seen:
                seen.add(bv)
                out.append({"bvid": bv, "title": strip(v.get("title")),
                            "created": v.get("created"), "length": v.get("length"),
                            "play": v.get("play")})
        total = ((res.get("data") or {}).get("page") or {}).get("count") or 0
        if pn * 30 >= total:
            break
        time.sleep(1.5)
    return out


if __name__ == "__main__":
    names = sys.argv[1:]
    op, mixin = init_session()
    for nm in names:
        mid = find_mid(nm)
        print("\n########## %s (mid=%s) ##########" % (nm, mid))
        if not mid:
            continue
        warmup(op, mid); time.sleep(1)
        vids = list_space(op, mixin, mid)
        print("total uploads fetched: %d" % len(vids))
        with open(os.path.join(RAW, "space_%s.json" % mid), "w", encoding="utf-8") as f:
            json.dump(vids, f, ensure_ascii=False, indent=1)
        for v in vids:
            print("  %s %-8s %s" % (v["bvid"], v["length"], v["title"][:78]))
