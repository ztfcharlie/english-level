# -*- coding: utf-8 -*-
"""Bilibili search + video-info helper with wbi signing (no login required)."""
import json, time, hashlib, urllib.parse, urllib.request, http.cookiejar, sys, os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def build_opener():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [
        ("User-Agent", UA),
        ("Referer", "https://www.bilibili.com/"),
        ("Accept", "application/json, text/plain, */*"),
        ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8"),
        ("Origin", "https://www.bilibili.com"),
    ]
    return op, cj


def get_json(op, url, tries=3):
    last = None
    for i in range(tries):
        try:
            with op.open(url, timeout=25) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:  # noqa
            last = e
            time.sleep(1.2 * (i + 1))
    raise RuntimeError("request failed: %s -> %s" % (url, last))


def init_session():
    """Grab buvid cookies + wbi keys. Returns (op, mixin_key)."""
    op, cj = build_opener()
    try:
        spi = get_json(op, "https://api.bilibili.com/x/frontend/finger/spi")
        d = spi.get("data") or {}
        for name, val in (("buvid3", d.get("b_3")), ("buvid4", d.get("b_4"))):
            if val:
                cj.set_cookie(http.cookiejar.Cookie(
                    0, name, val, None, False, ".bilibili.com", True, True,
                    "/", True, False, None, False, None, None, {}))
    except Exception:
        pass
    nav = get_json(op, "https://api.bilibili.com/x/web-interface/nav")
    wbi = (nav.get("data") or {}).get("wbi_img") or {}
    img = (wbi.get("img_url") or "").rsplit("/", 1)[-1].split(".")[0]
    sub = (wbi.get("sub_url") or "").rsplit("/", 1)[-1].split(".")[0]
    raw = img + sub
    mixin = "".join(raw[i] for i in MIXIN_TAB)[:32]
    return op, mixin


def wbi_sign(params, mixin_key):
    p = dict(params)
    p["wts"] = int(time.time())
    items = []
    for k in sorted(p):
        v = str(p[k])
        v = "".join(ch for ch in v if ch not in "!'()*")
        items.append((k, urllib.parse.quote(v, safe="")))
    q = "&".join("%s=%s" % (k, v) for k, v in items)
    p["w_rid"] = hashlib.md5((q + mixin_key).encode()).hexdigest()
    return urllib.parse.urlencode(p)


def search(op, mixin, keyword, page=1, order="totalrank"):
    params = {
        "search_type": "video", "keyword": keyword, "page": page,
        "order": order, "duration": 0, "tids": 0,
        "platform": "pc", "web_location": "1430650",
    }
    url = "https://api.bilibili.com/x/web-interface/wbi/search/type?" + wbi_sign(params, mixin)
    return get_json(op, url)


def video_info(op, mixin, bvid):
    params = {"bvid": bvid, "web_location": "1550101"}
    url = "https://api.bilibili.com/x/web-interface/wbi/view?" + wbi_sign(params, mixin)
    return get_json(op, url)


def strip(s):
    """Remove the <em class="keyword"> highlight tags bilibili injects."""
    if not s:
        return ""
    out, depth = [], 0
    i = 0
    while i < len(s):
        if s[i] == "<":
            j = s.find(">", i)
            if j == -1:
                break
            i = j + 1
            continue
        out.append(s[i])
        i += 1
    return "".join(out).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


if __name__ == "__main__":
    op, mixin = init_session()
    kw = sys.argv[1] if len(sys.argv) > 1 else "RAZ AA级 合集"
    res = search(op, mixin, kw)
    if res.get("code") != 0:
        print("ERR", res.get("code"), res.get("message"))
        sys.exit(1)
    data = res.get("data") or {}
    for it in (data.get("result") or [])[:20]:
        print("%-14s p=%-4s %-9s %s" % (
            it.get("bvid"), it.get("video_review"), it.get("duration"),
            strip(it.get("title"))[:70]))
