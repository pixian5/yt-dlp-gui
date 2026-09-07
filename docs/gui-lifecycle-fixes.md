# GUI 生命周期与解析并发说明

本文记录 `guiapi/app.py` 中下载、播放列表解析和窗口关闭的生命周期约定。GUI 使用 Tk 主线程负责控件更新，使用后台线程等待 yt-dlp 子进程；后续修改必须保持这两个边界。

## 1. 状态字段

| 字段 | 所有者 | 含义 |
| --- | --- | --- |
| `current_process` | 下载/信息查询线程 | 当前下载或 inspect 子进程。Stop 和关闭窗口通过它终止进程组。 |
| `_parse_process` | 播放列表解析线程 | 主解析请求或当前分页请求的子进程。任意时刻只登记一个进程。 |
| `_download_running` | 下载/inspect | 防止重复启动下载任务。 |
| `_parse_running` | 播放列表解析 | 解析期间占用 Download/Stop 控件，并阻止下载和 inspect 并发运行。 |
| `_download_cancel` | 下载线程 | 防止当前任务结束后继续启动下一个下载任务。 |
| `_parse_cancel` | 解析线程 | 使当前解析请求失效；线程会在收到结果或开始下一页前检查。 |
| `_parse_generation` | GUI 主线程 | 每次 URL 变化、开始新解析、取消或关闭窗口都会递增。旧 generation 的结果不能更新树或触发自动下载。 |
| `_closing` | GUI 主线程 | 关闭闩锁。设置后后台线程不得再调用 `root.after` 或更新 Tk 控件。 |

## 2. 下载生命周期

1. `start_download()` 构造任务列表，设置 `_download_running=True`，然后启动 `run_ytdlp()`。
2. 非 Windows 使用 `start_new_session=True`，Windows 使用 `CREATE_NEW_PROCESS_GROUP`。这样 Stop/关闭窗口可以对整个进程组操作，包含 ffmpeg 等子进程。
3. `stop_download()` 先设置 `_download_cancel=True`，再终止当前进程；线程退出后不会启动后续任务。
4. `run_ytdlp()` 的 `finally` 清理进程指针和运行状态。若 `_closing=True`，不再排入任何 Tk 回调。

## 3. 播放列表解析生命周期

解析按钮会生成新的 `generation`，并将 `_parse_running=True`。解析主请求和每个分页请求都登记到 `_parse_process`，使用 120 秒 `communicate(timeout=120)` 上限。

每个可能写入 GUI 的路径都必须先调用 `_parse_request_is_current(generation)`。该检查同时验证：

- GUI 没有进入关闭流程；
- 当前请求没有被取消；
- generation 仍是最新请求。

解析成功后，线程先结束 `_parse_running`，再通过 `root.after` 显示播放列表树。自动下载回调还会再次检查 generation，避免用户修改 URL 后启动旧请求的下载。

## 4. 取消与 URL 变化

Stop 按钮和 Esc 键共用 `stop_download()`。当 `_parse_running=True` 时，它会：

1. 取消自动下载标志；
2. 递增 `_parse_generation` 并设置 `_parse_cancel`；
3. 终止 `_parse_process` 进程组；
4. 恢复按钮和状态栏。

用户编辑 URL 会走 `on_url_changed()`。除了清理旧播放列表树，还会立即终止正在运行的解析子进程并使旧 generation 失效。旧线程即使稍后返回，也只能结束自身，不能覆盖新 URL 的状态。

## 5. 关闭窗口

`on_window_close()` 的顺序是：设置 `_closing`、取消下载和解析、递增 generation、终止 `current_process` 与 `_parse_process`、保存配置，最后销毁 Tk 根窗口。不要在销毁根窗口后等待后台线程调用 Tk API；后台线程应通过 `_closing` 判断跳过回调。

进程终止由 `_terminate_process()` 统一处理：先发送进程组终止信号并等待 2 秒，仍未退出时发送强制终止信号，再等待回收。异常只在进程已经消失或无法回收时被抑制。

## 6. 生成命令

GUI 内部执行始终使用参数列表，不经过 shell。仅“生成/复制命令”功能需要转换成 shell 文本：

- macOS/Linux 使用 `shlex.join()`；
- Windows 使用 `subprocess.list2cmdline()`。

不要恢复按空格判断是否加双引号的实现。yt-dlp 格式选择器中的 `<`、`>`，以及 URL 查询参数中的 `&`，都必须作为单一参数保留。

## 7. 播放列表标题语言

文件列表中的 `entry.title` 会直接进入勾选下载的文件名，因此预解析的语言必须与下载路径一致。`get_metadata_language()` 统一解析 GUI 语言或「Metadata language」下拉框的选项；下载和 `_parse_playlist_only()` 都传入 `--extractor-args youtube:lang=<locale>`。

不要只发送 `Accept-Language` HTTP 头：YouTube 的 Innertube 返回可能不会据此本地化播放列表条目。`youtube:lang` 是 yt-dlp 支持的、大小写敏感的 YouTube UI/API 语言代码；例如简体中文为 `zh-CN`。

## 8. 已知边界

- 批量标题预取使用独立的 `subprocess.run()`，已有 15/45 秒超时，但不会被播放列表主解析的 Stop 状态复用。
- 执行日志目前仍记录调试命令文本；命令中可能包含认证参数。若扩大日志范围，应先实现敏感参数脱敏。
- `root.after` 只能从后台线程排入回调，不能直接操作 Tk 控件；新增异步路径必须遵循这一约定。

## 9. 验证清单

在修改生命周期逻辑后执行：

```bash
.venv/bin/python -m compileall -q guiapi yt-dlp-gui.py guiapi-run.py
.venv/bin/pytest -q test/test_all_urls.py
git diff --check
```

还应手动确认：解析期间按 Stop/Esc 能返回 Ready；修改 URL 会取消旧解析；关闭窗口后没有残留 `yt_dlp`/ffmpeg 子进程；复制的命令能保留带特殊字符的 URL 和格式参数。
