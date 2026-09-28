# tools/ — 数据管线

这个目录负责**抓 B 站数据 → 生成播放器**。播放器本身（`../英语分级播放器.html`）
是纯静态的单文件，不依赖这里。只有想更新数据时才需要跑这些脚本。

## 依赖

只要 Python 3（标准库就够，不需要 pip 装任何东西）和网络。

## 完整重建

```bash
cd tools
python build_data.py     # 抓 27 个级别的分P列表 -> data.json   （约 2 分钟）
python make_list.py      # -> ../RAZ-B站合集清单.md
python make_app.py       # -> ../英语分级播放器.html 和 ../index.html
```

改 UI 只需要动 `app_template.html`，然后跑 `make_app.py`（秒级，不联网）。

## 各文件做什么

| 文件 | 作用 |
|---|---|
| `bili.py` | B 站接口封装。核心是 **wbi 签名**——B 站 2023 年后要求所有 web 接口带 `w_rid` 签名，否则返回 `-352 风控校验失败`。密钥从 `nav` 接口取，按 `MIXIN_TAB` 重排取前 32 位，再对排序后的查询串做 MD5。**未登录**即可工作。 |
| `scan.py` | 全级别关键词扫描，结果落 `raw/<级别>.json`。初次探索用的，日常重建不需要跑。 |
| `analyze.py` | 按 UP 主聚合扫描结果，找出"覆盖级别最多"的 UP 主和每级最佳候选。 |
| `season.py` | 打印某个视频所属**合集**（ugc_season）的完整目录。就是靠它发现主源的。 |
| `build_data.py` | **主力脚本**。从主源合集拉 AA→Z，逐级取分P列表，解析书名编号，输出 `data.json`。 |
| `make_list.py` | 生成给人看的 markdown 清单。 |
| `make_app.py` | 把 `data.json` 注入 `app_template.html`。 |
| `check_sync.py` | **同步检查**。重拉 27 级分P，跟 `data.json` 对账。`--fix` 可自动修正位置漂移。见下节。 |
| `check_bats.py` | 检查根目录的 `.bat` 是不是 CRLF 换行。见下面的坑。 |
| `verify.py` / `check_v.py` / `probe_play.py` | 排查用的：验证候选、检查缺口、探测可播放性。 |
| `debug_app.py` | 往生成的 HTML 里塞一个错误捕获器，用 headless Chrome 把 JS 报错 dump 出来。 |

## 数据源是怎么选出来的

B 站的 RAZ 资源非常多但**质量参差**，很多标题写"全 97 本"实际只有 38 个分P。
筛选过程：

1. `scan.py` 扫 27 个级别，拿到 854 个候选。
2. `analyze.py` 按 UP 主聚合 → 发现 `惊叹号的英语世界` 覆盖 26 个级别。
3. `season.py` 查它的合集 → 找到《分阶阅读☆自然习得丨阅读·飞跃之旅》里的
   `RAZ丨蓝标·全` 分区，**一个视频对一个级别，AA→Z 一个不落**。
4. `verify.py` 逐个核对**真实分P数**，发现 V 级只有 63 本（标称 88），
   在 `build_data.py` 的 `OVERRIDE` 里换成辅帮带的完整版。

## 三个坑

**`.bat` 必须是 CRLF 换行，纯 LF 会把 cmd 搞崩。** 这个坑踩过一次，
现象很迷惑：`'hich' 不是内部或外部命令`（`which` 掉了首字母）、
`'file:'` 被当成命令、`echo.` 跟上一行粘在一起、`cd /d "%~dp0"` 报
「系统找不到指定的驱动器」。原因是 **cmd.exe 在纯 LF 下行界判断错位，
会吃掉下一行的第一个字符**，然后一路累积。中途还会 `goto` 到奇怪的地方，
所以报错信息完全对不上真正的毛病。

改完 bat 记得跑一下：

```bash
python check_bats.py          # 报告
python check_bats.py --fix    # 重写成 CRLF
```

（`chcp 65001` + UTF-8 中文本身**没问题**，CRLF 下三种编码组合都验证过；
别为了躲这个坑就把中文删掉。）



**分P顺序不等于书序。** 比如 N 级的分P 1 是第 64 本、分P 3 是第 6 本。
`build_data.py` 按解析出的书名编号重排，但每条仍保留真实的 `i`（分P号），
播放器用 `i` 拼 iframe 地址。**改这块要小心，别把 `i` 丢了。**

**分集标题格式每级都不一样。** 见过 `AA-01☆Farm Animals`、`C-01·What Is at the Zoo`、
`N-64--Slithery Snakes`、`X-98-Whale Sharks` 四种。`parse_part()` 负责统一。
有些分P带 `【先看简介·再使用】` 前缀——它**仍然是真书**（AA 的第一本就是它），
所以只打 `x` 标记，不参与重排。

## 链接会变吗？怎么保持同步

**BVID 不会变**（它是 B 站的永久 ID，改标题、改 UP 主名都不影响），
但**分P会变**，而且有两种，危险程度差很多：

| 变化 | 后果 | 能不能立刻发现 |
|---|---|---|
| 增删/重排分P | `page=N` 指向**错的书** | ❌ 静默放错，最难查 |
| 视频删除/私密/下架 | 播不了 | ✅ 一打开就报错 |

第一种是要防的：播放器用 `page` 定位，上传者往中间插一个分P，后面全部偏移一位，
小朋友听到的还是英语，只是**书不对了**。

`check_sync.py` 的做法是**按书名匹配，而不是按位置匹配**：

```bash
python check_sync.py         # 只看报告
python check_sync.py --fix   # 顺手把 data.json 的 page 号修回去
```

书名匹配能扛住重排——即使某本书从 P12 挪到了 P15，也能认出来并更新。
匹配不上的才算真的丢了（`MISSING`）。日常用双击 `../同步检查.bat` 就行。

`--fix` 之后要跑 `python make_app.py` 重新生成播放器（bat 里已经串好了）。

## 接口失效了怎么办

B 站接口会变。如果 `build_data.py` 开始报 `-352` 或 `-403`：

1. 先确认 `nav` 接口还能返回 `wbi_img`（`bili.py:init_session`）。
2. 报 `412`/`-352` 通常是风控，等几分钟再试，或降低请求频率（脚本里已经加了 1.2s 延迟）。
3. 空间接口 `x/space/wbi/arc/search` 目前**稳定触发 412**，所以整条链路刻意
   不依赖它——搜索接口和 view 接口都还正常。

## 播放器里几个设计决定

- **单个 HTML 文件、数据内嵌。** `file://` 下 `fetch('data.json')` 会被 CORS 拦掉，
  所以数据必须内联。代价是文件 186KB，无所谓。
- **播放用 B 站官方 iframe**（`player.bilibili.com/player.html`）。不解析、不代理、
  不下载视频流，跑在用户自己的浏览器和登录态里。
- **自动连播靠计时器**，因为跨域 iframe 拿不到播放进度。每本时长是从接口取的，
  定时器按"时长 + 6 秒"推进。这是为「磨耳朵」场景做的取舍。
- **统计数据只存 localStorage**，不上传。
