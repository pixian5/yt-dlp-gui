# yt-dlp GUI（独立外挂）使用说明

本目录是 **yt-dlp 的 GUI 外挂**，不包含、不修改也不补丁 `yt_dlp/` 核心代码。原仓库的唯一自定义内容是 `gui/`；上游更新不会与该目录重叠，GUI 通过子进程调用原版核心。

## 目录关系与启动

默认目录布局：

```text
/Users/x/code/yt-dlp/
├── yt_dlp/       # 原版核心代码：直接同步 https://github.com/yt-dlp/yt-dlp
└── gui/          # 本项目：仅 GUI、文档和启动器
```

在 GUI 项目中运行：

```bash
cd /Users/x/code/yt-dlp/gui
./run_gui.sh
```

如使用其他核心 checkout，显式设置路径：

```bash
YT_DLP_CORE_DIR=/absolute/path/to/yt-dlp ./run_gui.sh
```

`YT_DLP_CORE_DIR` 必须包含 `yt_dlp/__init__.py`。GUI 将该目录加入 **GUI 子进程** 的 `PYTHONPATH`，再调用 `python -m yt_dlp`；不会写入核心目录，也不依赖 `yt_dlp.main_gui()` 这样的内部入口。

这份文档说明本仓库图形界面（运行时代码在 [`guiapi/app.py`](guiapi/app.py)）的选项与**有意设计的行为约定**。
目标：既能当使用说明，也能当维护备忘——**改下载/解析逻辑前务必先读「重要行为约定」**，避免再次把倒序序号、勾选下载等改坏。

历史未接线模块在 [`guiapi/_legacy/`](guiapi/_legacy/)；**不要改 `_legacy` 指望运行时生效**。

## 启动方式

推荐在项目虚拟环境里启动：

```bash
source .venv/bin/activate
python -m guiapi
# 或
python yt-dlp-gui.py
# 或
python guiapi-run.py
```

GUI 不再向核心包注册 `yt_dlp.main_gui()`；请从本项目的启动器运行。

## 界面总体结构

GUI 由四部分组成：

1. 顶部输入区
   主 URL、语言、粘贴/解析/下载快捷按钮。

2. 中间页签区
   含 **批量下载**、**文件列表（播放列表勾选）** 以及按功能分类的 `yt-dlp` 参数页。

3. 底部输出控制台
   运行日志、错误、进度相关输出。

4. 状态栏
   当前是否在下载、进度摘要等。

---

## 重要行为约定（维护者必读）

以下行为是**产品设计**，不是偶然实现。改代码前先对照；改了行为必须同步改本节。

### 1. 播放列表「倒序序号」是稳定编号，不是 UI 装饰

**位置：** 文件列表页签「#」列；下载文件名前缀 `NNN-标题.ext` 用的是同一数字。

**规则：**

- 对每条视频计算：
  `display_idx = playlist_count - original_index + 1`
  其中 `original_index` 是 yt-dlp 的 1-based 列表位（优先用 `requested_entries`）。
- **默认始终用倒序编号**（最新/列表前端更靠近大号或按 total 翻转后的号）。
- 勾选 **「播放列表倒序」** 只改变树里的**行显示顺序**，**不改变** `display_idx` / 文件名前缀。
- 下载任务用 `vis_to_orig[display_idx] → original_idx` 映射回真实条目，文件名用 `display_idx`。

**为什么必须这样：**

- 频道/播放列表**前端不断新增**时，旧视频的 `original_index` 会后移。
- 若用正序 `original_index` 当文件名，**同一条视频再次同步会变成新序号**（同片不同名）。
- 倒序编号下：列表前方插入新片 → 新片拿更大的 `display_idx`，**旧片 `display_idx` 尽量保持不变**，便于增量更新、去重、对照本地已下文件。

**禁止：**

- 不要再改成「仅勾选倒序时才用 reverse index」。
- 不要用树的视觉行号 `1..N`（过滤私有后）当文件名主序号；应用 **绝对** `display_idx`。
- 不要把 `display_idx` 和 yt-dlp 的 `playlist_index` 混为一谈（批量整表下载时模板里的 `%(playlist_index)s` 是另一套）。

### 2. 主 URL 命中已解析列表时：永远只听「文件列表」勾选

**位置：** `start_download`（[`guiapi/app.py`](guiapi/app.py)）。

**规则：**

- 若 `url_entry` 与 `playlist_parsed_url` 相同（URL 会做轻量规范化，如去尾部 `/`），则进入 **playlist_mode**：
  - 只为树中 **勾选 (☑)** 的行生成下载任务；
  - 每条任务单独 URL（或 `--playlist-items` 回退）+ 文件名 `{display_idx:03d}-{title}.%(ext)s`；
  - **忽略** 批量下载页 bulk 池里的其它 URL（即使 bulk 里有很多列表）。
- 若 playlist_mode 下 **一个都没勾选**：直接警告并**拒绝下载**，**禁止**回退成「整表 Single/batch」。
- 只有 **未** 处于「主 URL = 已解析列表」时，才用 bulk / 本地 batch 文件做多地址批量。

**为什么必须这样：**

- 用户常见流程：批量池里囤很多频道/列表 → 顶部解析其中一个 → 在文件列表里勾几条下载。
- 若 bulk 非空就强制 batch，会把整池第一条（常是别的频道）整表下掉，**完全无视勾选**——这是严重误操作。

**禁止：**

- 不要恢复「有 bulk 就 skip 树」的逻辑。
- 不要在「全不选」时用 `tasks = [('Single', base_args)]` 回退整表。

**调试日志：**

- 勾选下载应看到：`Using playlist tree selection` 以及 `下载任务：索引 <display_idx>`。
- 若仍出现 `Batch targets present — skipping playlist tree` 或 `Downloading N items of N` 整表，说明行为又被改坏了。

### 3. 批量下载页（bulk 池） vs 文件列表页

| 场景 | 行为 |
| --- | --- |
| 顶部主 URL = 已解析列表，文件列表有勾选 | 只下勾选项（§2） |
| 主 URL 空/不是当前解析结果，bulk 有多 URL | 用 bulk 做 `-a` 批量（每条 URL 各自整链/整视频） |
| Parse All（多条 bulk） | **串行只拉标题** 写入行内，不并发抢文件列表树 |
| Parse All / 行内 Parse **仅 1 条** | 可走完整 `parse_playlist`，打开文件列表树 |
| 密码等字段 | **不写入** `~/.yt-dlp-gui-config.json`；用户名仍可能保存 |

### 4. 停止 / Esc

- **停止** 按钮与 **Esc**：立刻 cancel 当前任务（`_download_cancel`），**无确认对话框**。
- List Formats / Extract Info 也走同一 runner，但 `_runner_kind == 'inspect'`：**停止时不提示删除 .part**。
- 真正下载任务同样不弹确认（按产品要求即时停）。

### 5. 倒序编号与「播放列表倒序」勾选对照

| 控件 | 作用 |
| --- | --- |
| `#` / 文件名前缀 | 始终 `total - original + 1`（稳定倒序号） |
| 播放列表倒序（checkbox） | 仅反转树中**行顺序**（从上到下浏览顺序） |
| 隐藏私有视频 | 过滤树显示；被过滤条目不参与勾选下载 |

### 6. 代码落点（改行为时搜这些）

| 行为 | 函数 / 符号 |
| --- | --- |
| 倒序序号 | `_show_playlist_tab`，`display_idx = total_entries - original_idx + 1` |
| 勾选下载 | `start_download` → `playlist_mode` / `vis_to_orig` |
| 批量参数 | `build_command_args` / `collect_batch_targets` |
| 停止 | `stop_download`、`_download_cancel`、`_on_escape_key` |
| 配置 | `get_current_config` / `apply_config` / `_SECRET_CONFIG_KEYS` |
| 运行时入口 | `guiapi.app.YtDlpGUI`；**不是** `guiapi/_legacy/*` |

---

## 顶部区域

### `Language`

- 切换 GUI 语言（可含「自动检测」；配置里可持久化 `auto`，会话内解析成具体语言）。
- 主要影响界面文案；下载参数里可能联动 metadata / 字幕语言相关默认。

### 主 URL 输入框

- 输入单个视频、播放列表、频道 `/videos`、合集等。
- **与文件列表联动：** 解析成功后 `playlist_parsed_url` 会记住该地址；下载时若主 URL 仍等于它，则只按勾选下载（见上文 §2）。
- 手动改主 URL 且不同于已解析地址时，会清空文件列表解析状态。

### 批量相关

- 主界面不再强调单独的「Or Batch File」输入框；批量 URL 主要在 **批量下载** 页签的池子（bulk 行）里管理。
- 配置可恢复 bulk 列表；清空后应写空列表，避免旧 URL「复活」。

### 快捷按钮

#### `粘贴链接并解析` / `解析链接` / `粘贴链接+解析+下载`

- 粘贴剪贴板、解析播放列表/频道、或解析后自动开始下载（按当前勾选/规则）。

#### `Download` / `停止`

- 空闲时开始下载；运行中变为停止。
- **Esc** 等同于按停止（运行中）。

#### `List Formats` / `Extract Info`

- 分别接近 `yt-dlp -F` / `yt-dlp --dump-json`（经 GUI runner，带 cancel）。
- 停止这两类任务时**不会**提示清理 partial 文件。

#### `Load Config` / `Save Config`

- 导入/导出 JSON；日常状态另有自动保存到 `~/.yt-dlp-gui-config.json`。

## 配置保存机制

- 自动保存：`~/.yt-dlp-gui-config.json`
- 重新打开会恢复多数选项与 bulk 池
- **不会**把 password / video_password / 2FA / 证书密码写入配置
- `language: auto` 应保留为 auto，不要在每次全量保存时改成已解析的 `zh`/`en`

## General 页签

这一页放“通用行为控制”。

### `Ignore errors (--ignore-errors)`

- 某个条目失败时继续往后跑。
- 批量下载、播放列表下载时很常用。

### `Ignore warnings (--no-warnings)`

- 不显示警告。
- 只建议在你已经知道警告内容、嫌日志太吵时使用。

### `Abort on error (--abort-on-error)`

- 遇到错误立刻停止整个任务。
- 和 `Ignore errors` 是相反思路，二选一更合理。

### `Download only video, not playlist (--no-playlist)`

- 当 URL 同时包含单视频和播放列表信息时，只下当前视频，不展开整个列表。
- 例如 YouTube `watch?v=...&list=...` 常用这个。

### `Download playlist (--yes-playlist)`

- 明确要求按播放列表处理。
- 适合你输入的是某个视频页，但想把整个列表都下下来。

### `Include private/unavailable videos in YouTube playlists`

- 控制是否把 YouTube 播放列表里的私有视频、地区受限视频、已失效视频等一并纳入列表识别。
- 默认开启，保持 `yt-dlp` 当前默认行为。
- 关闭后，GUI 会加上 `--compat-options no-youtube-unavailable-videos`。
- 这只是“是否把这些条目纳入列表处理”，不是绕过权限。
- 真正能不能下载私有视频，仍取决于你当前账号是否有权限。

### `Mark videos as watched (--mark-watched)`

- 下载后把视频标记成“已观看”。
- 主要对支持该行为的网站有意义。

### `Do not mark videos as watched (--no-mark-watched)`

- 显式禁止标记已观看。

### `Default search prefix`

- 给非 URL 文本自动补搜索前缀。
- 例如填 `ytsearch5:` 后，输入关键词时就会按 YouTube 搜索前 5 条。

### `Configuration file`

- 指定额外的 `yt-dlp` 配置文件路径。
- 适合你已有长期维护的命令行配置。

### `Flat playlist extraction`

- 控制是否加 CLI 的 `--flat-playlist`（固定为 `in_playlist` 语义）。
- 空白：不加该选项（正常提取）。
- `in_playlist`：等价于 `--flat-playlist`，列表项尽量平铺、更快。
- **注意：** GUI 不再提供 `discard` / `discard_in_playlist` 选项（CLI 无法单独表达）；旧配置若仍是 discard 值，加载时会迁成 `in_playlist`。

### `Age limit`

- 只处理符合年龄限制的视频。

### `Download archive file`

- 指定“下载归档”文件。
- 已记录过的 ID 下次会跳过。
- 长期增量下载非常有用。

### `Max downloads`

- 限制本次最多下载多少个条目。

## Network 页签

这一页主要影响连接、超时、速率、重试。

### `Proxy URL`

- 设置代理，如 `http://127.0.0.1:7890`。
- 遇到地区限制、公司网络限制、访问不稳定时常用。

### `Socket timeout (seconds)`

- 设置网络超时时间。

### `Source address (bind to)`

- 指定本机发起连接使用的源地址。
- 多网卡环境才常用。

### `Force IPv4 (--force-ipv4)`

- 强制 IPv4。
- 某些网络 IPv6 很差时可开。

### `Force IPv6 (--force-ipv6)`

- 强制 IPv6。

### `Enable file:// URLs (--enable-file-urls)`

- 允许把 `file://` 形式的本地路径当输入。

### `Sleep interval`

- 每次下载前额外等待的秒数。
- 用于降低请求频率。

### `Max sleep interval`

- 与 `Sleep interval` 组合使用，做随机等待上限。

### `Sleep interval for requests`

- 针对网络请求的等待间隔。

### `Sleep interval for subtitles`

- 字幕请求单独的等待时间。

### `Rate limit`

- 总下载速率上限。
- 例如 `500K`、`4.2M`。

### `Throttled rate`

- 把低于此速度视为“被节流”。
- 某些站点限速场景下可辅助重试逻辑。

### `Retries`

- 整体重试次数。

### `Fragment retries`

- 分片下载的重试次数。
- 对 HLS、DASH 等流媒体更常用。

## Geo-restriction 页签

这一页处理地区限制相关行为。

### `Geo verification proxy`

- 专门用于地区验证的代理。

### `Bypass geo restriction (--geo-bypass)`

- 尝试绕过地区限制。

### `Do not bypass geo restriction (--no-geo-bypass)`

- 显式关闭绕过。

### `Geo bypass country`

- 指定伪装国家代码。

### `Geo bypass IP block`

- 指定伪装 IP 段，CIDR 格式。

## Video Selection 页签

这一页决定“挑哪些视频下载”。

### `Playlist items`

- 只下载播放列表中的指定编号。
- 例如 `1-5,10,15-20`。

### `Playlist start`

- 从第几个开始。

### `Playlist end`

- 到第几个结束。

### `Match title (regex)`

- 只下载标题匹配正则的条目。

### `Reject title (regex)`

- 排除标题匹配正则的条目。

### `Min filesize`

- 只下载大于这个大小的文件。

### `Max filesize`

- 只下载小于这个大小的文件。

### `Date`

- 只下载指定日期的内容。
- 格式 `YYYYMMDD`。

### `Date before`

- 只下载该日期之前的内容。

### `Date after`

- 只下载该日期之后的内容。

### `Min views`

- 最低播放量门槛。

### `Max views`

- 最高播放量门槛。

### `Match filter`

- 高级筛选表达式。
- 适合熟悉 `yt-dlp --match-filter` 的用户。

### `Break on existing (--break-on-existing)`

- 一旦遇到已存在文件就停止后续处理。

### `Break on reject (--break-on-reject)`

- 一旦有条目被筛选条件排除，就停止任务。

### `No break on existing (--no-break-on-existing)`

- 显式允许遇到已存在文件时继续。

## Download 页签

这一页管“下载过程本身”。

### `Concurrent fragments`

- 分片并发数。
- 对 HLS、DASH 下载可提速，但太高可能更容易触发限流。

### `Limit download rate`

- 下载速率上限。

### `Buffer size`

- 下载缓冲区大小。

### `HTTP chunk size`

- HTTP 分块大小。
- 某些服务器在较小块大小时更稳定。

### `Do not resize buffer (--no-resize-buffer)`

- 禁止自动调整缓冲区。

### `Test mode - do not download (--test)`

- 测试模式，只下很小的一部分。
- 适合检查链路是否通畅。

### `External downloader`

- 指定外部下载器，如 `aria2c`、`curl`、`ffmpeg`。

### `External downloader args`

- 传给外部下载器的额外参数。

### `Prefer native HLS downloader (--hls-prefer-native)`

- HLS 优先用内置下载器。

### `Prefer ffmpeg for HLS (--hls-prefer-ffmpeg)`

- HLS 优先用 ffmpeg。
- 某些直播流、复杂流更稳。

### `Use MPEG-TS container for HLS (--hls-use-mpegts)`

- HLS 输出更偏向 MPEG-TS 容器。
- 某些直播、断流恢复场景更有帮助。

## Filesystem 页签

这一页控制文件名、目录、缓存、旁路元数据文件。

### `Output template`

- 输出文件命名模板。
- 例如 `%(title)s.%(ext)s`。
- 你当前默认是 `%(playlist_index)s-%(title)s.%(ext)s`，适合播放列表。

### `Output directory`

- 输出目录。

### `Paths configuration`

- 对不同类型输出路径做更细分配置。
- 适合高级用法。

### `Restrict filenames to ASCII (--restrict-filenames)`

- 文件名尽量只用 ASCII。
- 对跨平台兼容更友好，但标题可读性会下降。

### `Allow Unicode in filenames (--no-restrict-filenames)`

- 允许 Unicode 文件名。
- 中文、日文标题更自然。

### `Create playlist subfolder for playlist downloads`

- 勾选后，GUI 会在输出模板前自动补上 `%(playlist)s/`。
- 例如原模板是 `%(playlist_index)s-%(title)s.%(ext)s`，启用后实际效果会变成：
  `%(playlist)s/%(playlist_index)s-%(title)s.%(ext)s`
- 适合把每个播放列表自动放进自己的同名文件夹。
- 如果你的输出模板本来就已经手写了 `%(playlist)s/`，GUI 不会重复再套一层。

### `Force Windows-compatible filenames (--windows-filenames)`

- 文件名进一步兼容 Windows 保留字符规则。

### `Do not overwrite files (--no-overwrites)`

- 已有文件不覆盖。

### `Force overwrite files (--force-overwrites)`

- 强制覆盖已有文件。
- 使用前要确认目录里没有要保留的旧文件。

### `Continue partially downloaded files (--continue)`

- 继续未完成下载。
- 这是比较推荐的默认行为。

### `Do not continue downloads (--no-continue)`

- 不续传，从头开始。

### `Do not use .part files (--no-part)`

- 不生成临时 `.part` 文件。
- 简洁，但下载中断时恢复能力会差一些。

### `Do not use Last-modified header (--no-mtime)`

- 不用服务器返回的修改时间设置本地文件时间。

### `Write description to .description file (--write-description)`

- 额外保存描述文本。

### `Write metadata to .info.json file (--write-info-json)`

- 额外保存完整元数据 JSON。
- 排查问题、做二次处理非常有用。

### `Write annotations to .annotations.xml (--write-annotations)`

- 保存注释文件。
- 只有少数站点/场景还有意义。

### `Write comments to .comments.json (--write-comments)`

- 保存评论到 JSON 文件。

### `Load info JSON`

- 从已有 `info.json` 直接读取信息。
- 适合二次后处理。

### `Cache directory`

- 指定缓存目录。

### `Disable filesystem caching (--no-cache-dir)`

- 完全不用磁盘缓存。

### `Delete cache directory contents (--rm-cache-dir)`

- 删除缓存目录内容。

## Video Format 页签

这一页决定“下什么格式”。

### `Format selection`

- 核心格式表达式。
- 例如：
  - `best`
  - `bv*+ba/b`
  - `bestvideo[height<=1080]+bestaudio/best[height<=1080]`

### `Quick Select Resolution`

- 这是格式表达式的快捷预设，选择后会**立即覆盖**上方 `Format selection` 输入框。
- 例如选择 `720p` 会写入 `bv*[height<=720]+ba`；选择 `1080p` 会写入 `bv*[height<=1080]+ba`。
- `1080p 60fps` / `720p 60fps` 会要求 `fps>=60`，不会误选低帧率版本。
- 要自定义格式时，直接编辑 `Format selection`；下一次选择快速分辨率会再次用预设覆盖它。
- 如果界面仍不覆盖，请确认启动的是 `gui/run_gui.sh`（不是旧的 `python -m guiapi` 进程），然后重新打开 `Video Format` 页签。

### `Format sort`

- 格式排序规则。
- 当多个格式候选都符合条件时，用它决定优先级。

### `Prefer free formats (--prefer-free-formats)`

- 更偏向开放格式。

### `Check available formats (--check-formats)`

- 下载前检查格式可用性。

### `Merge output format`

- 音视频分离下载后，最终合并成什么容器。
- 常用 `mp4`、`mkv`。

### `Video multistreams`

- 是否允许多个视频流。

### `Audio multistreams`

- 是否允许多个音频流。

## Subtitles 页签

这一页处理字幕和一部分嵌入选项。

### `Write subtitle file (--write-subs)`

- 下载普通字幕文件。

### `Write automatic subtitle file (--write-auto-subs)`

- 下载自动生成字幕。

### `List available subtitles (--list-subs)`

- 只列出可用字幕，不下载。

### `Subtitle format`

- 字幕保存格式，如 `srt`、`vtt`、`ass`、`lrc`。

### `Subtitle languages`

- 指定字幕语言，逗号分隔。
- 例如 `en,zh-Hans,ja`。

### `Embed subtitles (--embed-subs)`

- 把字幕嵌入视频容器。
- 一般需要 ffmpeg。

### `Do not embed subtitles (--no-embed-subs)`

- 显式不嵌入字幕。

### `Embed thumbnail (--embed-thumbnail)`

- 把缩略图嵌入媒体文件。
- 虽然这个开关位置在字幕页，但它本质上是封面嵌入选项。

### `Do not embed thumbnail (--no-embed-thumbnail)`

- 显式不嵌入封面。

## Authentication 页签

这一页最关键，很多会员视频、年龄限制视频、私有视频能否访问，都看这里。

### `Username`

- 站点登录用户名。

### `Password`

- 站点登录密码。

### `Two-factor code`

- 两步验证码。

### `Use .netrc authentication (--netrc)`

- 从 `.netrc` 读取登录信息。

### `Video password`

- 对“单视频密码保护”内容使用。

### `Adobe Pass MSO`

- Adobe Pass 电视运营商标识。

### `Adobe Pass username`

- Adobe Pass 用户名。

### `Adobe Pass password`

- Adobe Pass 密码。

### `Client certificate`

- 客户端证书文件。

### `Client certificate key`

- 客户端证书私钥文件。

### `Client certificate password`

- 客户端证书私钥密码。

## Post-processing 页签

这一页管下载后的转换、重封装、元数据写入。

### `Extract audio (-x, --extract-audio)`

- 只保留音频。

### `Audio format`

- 提取音频后的目标格式。
- 常用 `mp3`、`m4a`、`opus`、`flac`。

### `Audio quality`

- 音频质量参数。
- 数值越接近 `0` 越高。

### `Recode video format`

- 重新编码成指定视频格式。
- 这是“转码”，速度慢但兼容性强。

### `Remux video format`

- 只换封装，不重编码。
- 速度快，适合 `webm` 转 `mkv`、`m4a` 转 `mp4` 这类。

### `Keep video file after conversion (--keep-video)`

- 转换后保留原始文件。

### `Do not keep video file (--no-keep-video)`

- 转换后不保留原始文件。

### `Embed metadata (--embed-metadata)`

- 把元数据嵌入媒体文件。

### `Embed chapter markers (--embed-chapters)`

- 嵌入章节信息。

### `Embed info.json (--embed-info-json)`

- 把 `info.json` 嵌入媒体文件。

### `Add metadata to file (--add-metadata)`

- 把常见元数据字段写进文件标签。

### `Metadata fields`

- 从标题中提取元数据字段。

### `Parse metadata`

- 自定义元数据解析规则。

### `FFmpeg location`

- 指定 ffmpeg 路径。
- 如果系统里没配 PATH，这里特别重要。

### `Post-processor args`

- 给后处理器传额外参数。

## Thumbnail 页签

### `Write thumbnail image (--write-thumbnail)`

- 下载缩略图。

### `Write all thumbnail formats (--write-all-thumbnails)`

- 下载全部缩略图版本。

### `List available thumbnails (--list-thumbnails)`

- 只列出缩略图，不下载。

### `Convert thumbnails format`

- 转换缩略图格式，如 `jpg`、`png`、`webp`。

## Verbosity/Simulation 页签

这一页是日志、调试和“只看信息不下载”。

### `Quiet mode (-q, --quiet)`

- 尽量减少输出。

### `No warnings (--no-warnings)`

- 不显示警告。
- 和 General 页里的同类选项本质一致。

### `Verbose output (-v, --verbose)`

- 输出更详细的调试信息。
- 出问题时建议开启。

### `Metadata language`

- 控制 YouTube 返回的标题、频道和播放列表等元数据语言；默认跟随 GUI 当前语言。
- 对播放列表尤为重要：文件列表中显示的标题会直接成为勾选下载后的文件名。
- 例如选择 `Chinese (Simplified) (zh-CN)` 后，GUI 会在**解析和下载**两条路径都传入 `youtube:lang=zh-CN`；不是下载时才处理。
- 这是请求 YouTube 返回本地化标题，不是把原始英文标题进行机器翻译。若视频本身没有可用中文本地化标题，YouTube 仍可能只能返回原文。

### `Simulate, do not download (-s, --simulate)`

- 模拟执行，不下载。
- 用于先验证提取、格式、命名是否正确。

### `Skip download (--skip-download)`

- 跳过媒体下载，但仍可拿元数据、字幕等。

### `Get title / Get ID / Get URL / Get thumbnail / Get description / Get duration / Get filename / Get format`

- 这些都是“只输出某个字段”的快捷模式。
- 适合你想调试字段，或者想配合脚本拿数据。

### `Dump JSON info (--dump-json)`

- 每个视频输出 JSON 元数据。

### `Dump single JSON (--dump-single-json)`

- 对播放列表等，尽量输出单个整合 JSON。

### `Print JSON info (--print-json)`

- 打印 JSON 信息。

### `Show progress (--progress)`

- 显示进度。
- 当前 `yt-dlp` 默认就会显示进度，这个勾选更多是界面上的正向表达。

### `Hide progress (--no-progress)`

- 不显示进度。

### `Display progress in console title (--console-title)`

- 把进度写到控制台标题。

### `Progress template`

- 自定义进度展示模板。

## Workarounds 页签

这一页适合网络环境奇怪、证书异常、站点封锁严格时使用。

### `Encoding`

- 指定字符编码。

### `Skip SSL certificate validation (--no-check-certificate)`

- 跳过 SSL 证书校验。
- 只在证书真的有问题时临时使用，不建议长期默认开。

### `Prefer insecure connections (--prefer-insecure)`

- 优先使用不安全连接。

### `User agent`

- 自定义请求头里的 User-Agent。
- 某些站点很看这个。

### `Referer`

- 自定义 Referer。
- 防盗链场景常用。

### `Add header`

- 增加额外请求头。
- 通常格式类似 `Key:Value`。

### `Bidirectional text workaround (--bidi-workaround)`

- 处理双向文本显示问题。

### `Sleep before requests`

- 每次请求前等待。

### `Use legacy server connect (--legacy-server-connect)`

- 使用较旧的服务器连接方式。
- 很偏兼容性救急选项。

## SponsorBlock 页签

### `Mark SponsorBlock chapters (--sponsorblock-mark)`

- 把 SponsorBlock 片段标成章节。

### `Remove SponsorBlock segments (--sponsorblock-remove)`

- 直接移除 SponsorBlock 标记的片段。

### `SponsorBlock categories to remove`

- 指定要删除的分类。

### `SponsorBlock categories to mark`

- 指定只标记不删除的分类。

### `SponsorBlock chapter title`

- 自定义章节标题格式。

### `Disable SponsorBlock (--no-sponsorblock)`

- 完全关闭 SponsorBlock。

### `SponsorBlock API URL`

- 自定义 SponsorBlock API 地址。

## Extractor 页签

这一页最适合放“站点提取器细节”。

### `Extractor arguments`

- 给某个提取器传特定参数。
- 格式通常是 `提取器名:键=值` 或类似变体。
- 适合高级用户。

### `Extractor retries`

- 提取阶段的重试次数。

### `Allow dynamic MPD manifests (--allow-dynamic-mpd)`

- 允许动态 MPD。

### `Ignore dynamic MPD manifests (--ignore-dynamic-mpd)`

- 忽略动态 MPD。

### `Split HLS segments on discontinuity (--hls-split-discontinuity)`

- HLS 遇到 discontinuity 时拆分处理。

### `Cookies from browser`

- 从浏览器读取登录态。
- 对 YouTube、Bilibili、需要登录的站点最常用。
- 如果要下载你自己账号可见的私有内容，这通常是首选。

### `Cookies file`

- 从文本 cookies 文件读取登录态。
- 适合导出的 Netscape cookies 文件。

## Advanced 页签

### `Raw command-line arguments`

- 手动追加原始命令行参数。
- 一行一个参数或者直接写成一串都可以。
- 当 GUI 还没暴露某个选项时，这里是兜底方案。

### `Generated command`

- 展示 GUI 最终拼出来的命令。
- 很适合排查“为什么这个选项没生效”。

### `Generate Command`

- 刷新并显示当前命令。

### `Copy to Clipboard`

- 把命令复制到剪贴板。

## 常见组合建议

### 下载 YouTube 播放列表，保存为 MP4

建议：

- `General`
  - 勾选 `Download playlist`
  - 保持 `Include private/unavailable videos in YouTube playlists` 开启
- `Extractor`
  - `Cookies from browser = chrome`
- `Video Format`
  - `Format selection = bv*+ba/b`
  - `Merge output format = mp4`
- `Filesystem`
  - 输出目录设到目标文件夹
  - 勾选 `Create playlist subfolder for playlist downloads`
  - 输出模板设为 `%(playlist_index)s-%(title)s.%(ext)s`

### 只下载音频并转 MP3

建议：

- `Post-processing`
  - 勾选 `Extract audio`
  - `Audio format = mp3`

### 只测试不实际下载

建议：

- `Verbosity/Simulation`
  - 勾选 `Simulate`
- 或者：
  - `Download`
  - 勾选 `Test mode`

## 关于私有视频

要区分三件事：

1. 是否在播放列表里显示私有/不可用条目
   由 `Include private/unavailable videos in YouTube playlists` 控制。

2. 是否能识别出该条目是私有视频
   只要列表接口能返回，通常能识别。

3. 是否能真正下载私有视频
   取决于你的登录态是否有权限。

因此，如果你想下载你自己账号能访问的私有视频，通常应这样配：

- `Extractor -> Cookies from browser = chrome`
- Chrome 中登录正确的 YouTube 账号
- `General -> Include private/unavailable videos in YouTube playlists` 保持开启

## 注意事项

### 1. GUI 是 `yt-dlp` 的前端

- 真正下载逻辑仍然是 `yt-dlp` 核心在执行。
- GUI 只是帮你拼参数、展示日志。

### 2. 某些选项互相冲突时，以最终命令和 `yt-dlp` 行为为准

例如：

- `--no-playlist` 和 `--yes-playlist`
- `--continue` 和 `--no-continue`
- `--embed-subs` 和 `--no-embed-subs`

这类最好不要同时勾。

### 3. 很多后处理功能依赖 ffmpeg

例如：

- 合并音视频
- 转码
- 嵌入字幕
- 嵌入封面
- 嵌入章节

如果相关功能没生效，先检查 ffmpeg。

### 4. 生成命令是排查问题的第一入口

当你怀疑 GUI 没按预期工作时，先看 `Advanced` 页里的生成命令，再对照 `yt-dlp` 命令行行为排查。

## 文件位置

- GUI 运行时主代码：[`guiapi/app.py`](guiapi/app.py)
- GUI 包入口：[`guiapi/__init__.py`](guiapi/__init__.py)、[`guiapi/__main__.py`](guiapi/__main__.py)
- 启动脚本：[`yt-dlp-gui.py`](yt-dlp-gui.py)、[`guiapi-run.py`](guiapi-run.py)
- 未接线历史代码（勿当运行时）：[`guiapi/_legacy/`](guiapi/_legacy/)
- 当前文档：[`README.md`](README.md)
- 用户配置：`~/.yt-dlp-gui-config.json`

## 维护者补充：运行时架构与调试

这一节描述当前实现的边界，适用于修改 `guiapi/` 代码的开发者。用户侧选项说明见前面的页签章节；进程生命周期的细节见 [`docs/gui-lifecycle-fixes.md`](docs/gui-lifecycle-fixes.md)。

### 入口与模块职责

| 文件 | 职责 | 是否为运行时路径 |
| --- | --- | --- |
| `guiapi/app.py` | `YtDlpGUI`、Tk 控件、参数构造、下载/解析 runner、配置保存 | 是 |
| `guiapi/__main__.py` | `python -m guiapi` 的薄入口 | 是 |
| `guiapi/__init__.py` | 导出 `YtDlpGUI`、`main` 和共享常量 | 是 |
| `guiapi/constants.py` | 语言、SponsorBlock 分类、无 Tk 默认状态 | 是 |
| `guiapi/translations.py` | UI 与常见 yt-dlp 输出的翻译表 | 是 |
| `guiapi/_legacy/` | 历史 mixin 和页签实现，仅供查阅 | 否 |

不要把同一个函数同时修在 `app.py` 与 `_legacy/` 中：运行时只会执行 `app.py` 的实现。

### Tk 线程边界

Tk 控件和 `StringVar`/`BooleanVar` 必须由主线程读写。下载、格式查询、信息提取和播放列表预解析在后台线程中等待子进程，结果通过两种方式回到主线程：

- 日志放入 `log_queue`，由 `_start_log_watcher()` 定时消费；
- 控件或状态更新使用 `root.after(...)` 排入 Tk 事件循环。

后台线程不能直接调用 `widget.config()`、`Treeview.item()` 或 `StringVar.set()`。窗口关闭时 `_closing` 会变为真，后台线程必须跳过新的 `root.after` 回调。

### 主要状态转换

下载和解析共用顶部 Download/Stop 控件，但状态字段不同：

```text
空闲
  ├─ start_download()       -> _download_running=True -> run_ytdlp()
  ├─ list_formats/info      -> _download_running=True, _runner_kind=inspect
  └─ parse_playlist()       -> _parse_running=True, generation=n

Stop/Esc
  ├─ 下载/inspect            -> _download_cancel=True，终止 current_process
  └─ 播放列表解析            -> _parse_cancel=True，generation++，终止 _parse_process

窗口关闭
  -> _closing=True -> 取消所有 worker -> 终止进程组 -> 保存配置 -> destroy()
```

解析线程在主请求和每个分页请求开始前都登记 `_parse_process`，并使用 120 秒 `communicate(timeout=120)` 上限。URL 改变、Stop 和关闭窗口都会递增 `_parse_generation`；旧线程即使返回，也不能更新树或触发自动下载。

### 配置文件格式

默认配置位置是 `~/.yt-dlp-gui-config.json`。顶层配置保存语言偏好和版本，控件状态集中在 `gui_state`：

```json
{
  "config_version": 1,
  "language": "auto",
  "language_initialized": true,
  "gui_state": {
    "url_entry": "https://example.invalid/video",
    "format": "bv*[height<=1080]+ba",
    "bulk_urls": [],
    "bulk_playlists": []
  }
}
```

`password`、`video_password`、`twofactor`、应用密码和客户端证书密码不会写入配置。加载旧配置时，`apply_config()` 会迁移已移除的重复控件（例如旧的速率/请求等待字段），并为缺失字段填充 `GUI_DEFAULT_STATE`。

保存行为需要注意两点：

1. 批量页是动态行，空池也必须保存为空数组，不能让旧 URL 在下一次启动时复活。
2. `language: "auto"` 是用户偏好，不要把它替换成当前会话检测出的具体语言。

### 参数构造与命令复制

`build_command_args()` 返回参数列表，内部执行使用 `subprocess.Popen(list)`，不经过 shell。Advanced 页的 Generated command 只是复制到终端的文本：

- macOS/Linux 使用 `shlex.join()`；
- Windows 使用 `subprocess.list2cmdline()`。

不要使用“只给含空格的参数加双引号”的简化拼接；格式选择器中的 `<`、`>` 和 URL 查询参数中的 `&` 都必须保留在同一个 shell 参数中。

### 调试与验证清单

修改 GUI 后，在项目虚拟环境中运行：

```bash
.venv/bin/python -m compileall -q guiapi yt-dlp-gui.py guiapi-run.py
.venv/bin/pytest -q test/test_all_urls.py
git diff --check
```

手动冒烟时至少覆盖：

- Parse Playlist 后修改 URL，旧结果不会重新填充文件列表；
- 解析期间按 Stop 或 Esc，状态回到 Ready 且没有残留 `yt_dlp`/ffmpeg 子进程；
- 关闭下载中的窗口，子进程组随窗口结束；
- Generated command 对带 `&` 的 URL 和 `bv*[height<=1080]+ba` 格式可直接复制执行；
- 批量池清空、重新启动后不会恢复旧行。

日志文件（如 `*.log`、`*.pid`）属于本机运行产物，已由仓库根目录 `.gitignore` 忽略，不要提交到 Git。
