# -*- coding: utf-8 -*-
"""Inject data.json into app_template.html -> ../英语分级播放器.html"""
import json, os, io, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    with io.open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with io.open(os.path.join(HERE, "app_template.html"), encoding="utf-8") as f:
        tpl = f.read()

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("__RAZ_DATA__", payload)

    # Same bytes under two names: the Chinese one for double-clicking, and
    # index.html so the local server's URL stays ASCII (http://localhost:8899/).
    for name in ("英语分级播放器.html", "index.html"):
        out = os.path.join(ROOT, name)
        with io.open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote %s  (%.0f KB)" % (out, os.path.getsize(out) / 1024.0))


if __name__ == "__main__":
    main()
