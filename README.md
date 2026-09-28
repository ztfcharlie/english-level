# RAZ 分级阅读 · 磨耳朵播放器

一个单文件网页。AA → Z 共 27 个级别、2378 集，数据全部内嵌在里面，
所以**没有后端、没有数据库、不需要联网配置** —— 打开就是一排级别，
点一下就开始放。播放走 B 站官方嵌入播放器，跑在浏览器自己的登录态里。

> 视频版权归原 UP 主所有，这里只做索引，不转载、不下载。
> 合集清单和备用源见 [`RAZ-B站合集清单.md`](RAZ-B站合集清单.md)。

---

## 跑起来的三种方式

### 1. 直接双击（最省事）

双击 **`英语分级播放器.html`**。数据内嵌，`file://` 下也能跑。

### 2. 本地小服务器（推荐 Windows 上用）

双击 **`启动.bat`** —— 起一个只监听本机的服务，然后自动开浏览器到
<http://localhost:8899/index.html>。关掉那个黑窗口就是停止。

`启动.bat` 和 `index.html` 内容完全一样，只是走 HTTP 比 `file://` 少一些
浏览器怪毛病。

### 3. Docker（要长期挂着、或想让平板/电视也能看）

```bash
docker compose up -d --build
```

然后打开 <http://localhost:8899>。

**同一局域网里的其他设备**（平板、电视盒子）用 `http://<这台机器的IP>:8899`
也能打开 —— 这才是 Docker 化的意义：小朋友可以直接用自己那台平板听，
不用碰你的电脑。

| 想做的事 | 怎么做 |
|---|---|
| 换端口 | 改 `docker-compose.yml` 里 `"8899:80"` 左边那个数字 |
| 只给本机，不给局域网 | `RAZ_HOST=127.0.0.1 docker compose up -d` |
| 看日志 | `docker compose logs -f player` |
| 停止 | `docker compose down` |
| 开机自动起 | 已经配好了（`restart: unless-stopped`），但要在 Docker Desktop 里勾上 "Start Docker Desktop when you sign in" |

> **没验证过的地方，先说实话**：这套 Docker 文件是在一台没跑 Docker 引擎的
> 机器上写的，所以 `Dockerfile` 和 `nginx.conf` **没有真正构建/启动验证过**。
> 能验的都验了：`docker compose config` 两个服务都解析通过（`--profile tools`
> 也通过）、Dockerfile 里每个 `COPY` 源都存在、`*.md` 通配只匹配一个文件。
> 剩下的是语法正确但没跑过 —— 第一次 `up` 如果报错，把输出贴给我。

---

## 更新数据

B 站那边的视频被改动或下架时，重新对一遍账：

```bash
python tools/check_sync.py          # 只看报告
python tools/check_sync.py --fix    # 顺便修 page 号
python tools/make_app.py            # 重新生成播放器
```

Windows 上更省事：双击 **`同步检查.bat`**，它会串好这三步。

Docker 部署的话，最后再加一句重建：

```bash
docker compose --profile tools run --rm tools python check_sync.py --fix
docker compose up -d --build
```

（`tools` 服务默认不启动，只有显式 `run` 才会跑。它的镜像是 Python，
跟播放器那个 nginx 镜像是两回事。）

---

## 文件说明

| 文件 | 是什么 |
|---|---|
| `index.html` | **播放器本体。** 数据内嵌的单文件，190KB |
| `英语分级播放器.html` | 跟 `index.html` 逐字节相同。给你双击用的中文名 |
| `启动.bat` | Windows 上起本地服务器 + 开浏览器 |
| `同步检查.bat` | Windows 上一键对账 + 修复 + 重建 |
| `RAZ-B站合集清单.md` | 给人看的清单：每级集数、缺本、备用源 |
| `Dockerfile` / `docker-compose.yml` | 播放器的容器化 |
| `Dockerfile.tools` | 可选：跑数据脚本用的 Python 镜像 |
| `docker/nginx.conf` | 静态服务的 nginx 配置 |
| `tools/` | 抓 B 站数据、生成播放器的脚本。[说明在这](tools/README.md) |

改 UI 只动 `tools/app_template.html`，然后 `python tools/make_app.py`（秒级，不联网）。
"# english-level" 
