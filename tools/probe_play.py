# -*- coding: utf-8 -*-
"""Sanity-check that each level's video is actually playable (not region/pay walled)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili import init_session, get_json, wbi_sign

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    data = json.load(f)

op, mixin = init_session()
bad = []
for r in data["levels"]:
    params = {"bvid": r["bvid"], "cid": "", "qn": 64, "fnval": 16,
              "fourk": 1, "fnver": 0}
    # need cid; grab it from the view API first
    try:
        v = get_json(op, "https://api.bilibili.com/x/web-interface/wbi/view?"
                     + wbi_sign({"bvid": r["bvid"]}, mixin))
        cid = ((v.get("data") or {}).get("pages") or [{}])[0].get("cid")
        params["cid"] = cid
        pu = get_json(op, "https://api.bilibili.com/x/player/wbi/playurl?"
                      + wbi_sign(params, mixin))
        code = pu.get("code")
        d = pu.get("data") or {}
        dash = (d.get("dash") or {}).get("video") or []
        ok = code == 0 and (dash or d.get("durl"))
        print("%-3s %s code=%-4s %s" % (r["level"], r["bvid"], code,
                                        "OK qn=%s" % d.get("quality") if ok else pu.get("message")))
        if not ok:
            bad.append((r["level"], r["bvid"], code, pu.get("message")))
    except Exception as e:
        print("%-3s %s ERROR %s" % (r["level"], r["bvid"], e))
        bad.append((r["level"], r["bvid"], "exc", str(e)))
    time.sleep(1.2)

print("\n%d/%d playable" % (len(data["levels"]) - len(bad), len(data["levels"])))
for b in bad:
    print("  NOT PLAYABLE:", b)
