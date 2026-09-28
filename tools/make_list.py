# -*- coding: utf-8 -*-
"""Emit the human-readable collection list (markdown) from data.json."""
import json, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

HEAD = """# RAZ 分级阅读 · B 站合集清单

> 视频版权归原 UP 主所有，这里只做**索引**，不转载、不下载。
> 数据抓取时间：{gen}

## 主源：一个合集打通 AA → Z

**UP 主：** [{uploader}]({url})
**合集：** 《{season}》
**规模：** {nlev} 个级别 · {nep} 集 · 约 {hours} 小时

这个合集的好处是**同一个 UP 主、同一套格式**，每级的「总词汇量」都标好了，
可以直接当进度用。缺点是个别级别有缺本（下表已标出）。

- **可播放** = 这个视频实际有几个分P，也就是能点开多少集。
- **该合集缺** = 原 UP 主剪辑时跳号漏掉的书（按书名编号算）。缺得不多的级别
  用下面的「备用源」就能补齐。

| 级别 | 阶段 | 可播放 | 时长 | 该合集缺 | 链接 |
|---|---|---|---|---|---|
"""

FOOT = """

## 备用源

主源有缺本时可以用这些补（都是各级别里集数最全的）：

| 级别 | UP 主 | 说明 | 链接 |
|---|---|---|---|
| V | 辅帮带 | 88 本全，主源 V 级只有 63 本时用的就是它 | [BV1YiA4zWEFv](https://www.bilibili.com/video/BV1YiA4zWEFv) |
| M | 辅帮带 | 81 本全 | [BV1paZfBUExA](https://www.bilibili.com/video/BV1paZfBUExA) |
| AA | 流尘学AI | 97 本全 | [BV1bhoLBiEyD](https://www.bilibili.com/video/BV1bhoLBiEyD) |
| A | 学习星球AAA | 全 97 本，跟读视频 | [BV18bELzWEuk](https://www.bilibili.com/video/BV18bELzWEuk) |
| B | 辅帮带 | 97 本全 | [BV1GkFdzwE2W](https://www.bilibili.com/video/BV1GkFdzwE2W) |
| C | 学习星球AAA | 全 95 本 | [BV12e78zpEjL](https://www.bilibili.com/video/BV12e78zpEjL) |
| E | 昆西来了 | 88 本全，含快速伴读 | [BV1W54y1d75m](https://www.bilibili.com/video/BV1W54y1d75m) |
| F | 昆西来了 | 89 本全 | [BV1bz411b7qx](https://www.bilibili.com/video/BV1bz411b7qx) |
| I | 辅帮带 | 86 本全 | [BV17jcMzBEgT](https://www.bilibili.com/video/BV17jcMzBEgT) |
| J | 辅帮带 | 86 本全 | [BV13EFDzVEHe](https://www.bilibili.com/video/BV13EFDzVEHe) |
| N | 辅帮带 | 81 本全 | [BV1ABfABcE37](https://www.bilibili.com/video/BV1ABfABcE37) |
| X | 辅帮带 | 111 本全 | [BV1XMAvzyEnW](https://www.bilibili.com/video/BV1XMAvzyEnW) |
| Y | 辅帮带 | 98 本全 | [BV1mMPGzgEFr](https://www.bilibili.com/video/BV1mMPGzgEFr) |

**另一个可选项：** 想让孩子看「唱读动画」而不是静态绘本，可以看
《0基础磨耳朵《RAZ唱读动画》共340集》（[BV1tp4y1V7ef](https://www.bilibili.com/video/BV1tp4y1V7ef)），
覆盖 aa–h，节奏更活泼，适合更小的孩子。

## 怎么用

- **点开就能听**：双击 `英语分级播放器.html`，或双击 `启动.bat`（推荐，走本地服务器更稳）。
- **直接跳某一级**：在浏览器地址后面加 `#lv=AA`、`#lv=N` 这样。
- **每周一早上从上次的地方接着听**：首页那个蓝色大按钮就是。

## 说明

- 本清单由脚本自动生成（`tools/` 目录），B 站接口变动后可重新跑 `tools/build_data.py` 更新。
- 视频能不能高清、能不能播，取决于你自己的 B 站账号状态——播放器用的是 B 站官方嵌入播放器，
  跑在你自己的浏览器里，不经过任何第三方。
"""


def main():
    with io.open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        d = json.load(f)

    bands = [("AA", "A", "B", "C"), ("D", "E", "F", "G", "H", "I"),
             ("J", "K", "L", "M", "N", "O", "P"), tuple("QRSTUVWXYZ")]
    bandname = {}
    for nm, lv in zip(["启蒙", "进阶", "中级", "高级"], bands):
        for l in lv:
            bandname[l] = nm

    rows = []
    for r in d["levels"]:
        gaps = r.get("gaps") or []
        rows.append("| **%s** | %s | %d | %.1f h | %s | [%s](https://www.bilibili.com/video/%s) |" % (
            r["level"], bandname.get(r["level"], ""), r["n_parts"],
            (r["total_sec"] or 0) / 3600.0,
            ("第 " + "、".join(str(g) for g in gaps) + " 本") if gaps else "—",
            r["bvid"], r["bvid"]))

    total = sum(r["n_parts"] for r in d["levels"])
    hours = sum(r["total_sec"] or 0 for r in d["levels"]) / 3600.0
    body = HEAD.format(gen=d["generated"], uploader=d["source"]["uploader"],
                       url=d["source"]["url"], season=d["source"]["season_title"],
                       nlev=len(d["levels"]), nep=total, hours="%.0f" % hours)
    out = body + "\n".join(rows) + "\n" + FOOT
    path = os.path.join(ROOT, "RAZ-B站合集清单.md")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s" % path)


if __name__ == "__main__":
    main()
