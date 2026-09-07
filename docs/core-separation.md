# 核心与 GUI 的隔离约定

`gui/` 是 `yt-dlp` 仓库内的独立外挂目录，`yt-dlp` 的其它文件仍是未修改的上游核心。两者必须始终保持以下边界：

1. GUI 项目可以读取核心路径并在子进程中导入 `yt_dlp`，但不得在核心目录创建、编辑或删除文件。
2. GUI 不得修改 `yt_dlp/`、`pyproject.toml`、核心版本文件、核心 CLI 入口或核心 `.gitignore`。
3. 除 `gui/` 外，核心仓库不得保留任何自定义补丁。上游更新只会影响上游文件，`git pull upstream master` 可自动合并，不需要手工处理 GUI 冲突。
4. GUI 功能、启动器、GUI 文档和 GUI 配置只在 `gui/` 内维护和提交。

## 绑定核心

默认核心路径是外挂目录的父目录 `..`。若使用其他 checkout，在启动时设置：

```bash
YT_DLP_CORE_DIR=/absolute/path/to/yt-dlp ./run_gui.sh
```

`guiapi.core` 会验证 `yt_dlp/__init__.py` 存在，并只为 GUI 创建的 `python -m yt_dlp` 子进程注入该路径到 `PYTHONPATH`。这既保留了原版 yt-dlp 的升级能力，也避免在 GUI 中复制或补丁核心代码。

## 更新流程

```bash
# 同步官方上游；只要上游不创建 gui/，不会与外挂冲突
cd /Users/x/code/yt-dlp
git pull upstream master

# GUI：只在外挂目录维护
cd /Users/x/code/yt-dlp/gui
./run_gui.sh
```

核心升级后应进行一次 GUI 冒烟检查：确认 `YT_DLP_CORE_DIR` 能被解析，并使用 GUI 的 List Formats 或 Extract Info 验证子进程能导入新核心。
