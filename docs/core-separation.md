# GUI 外挂与 yt-dlp 核心的独立项目边界

GUI 已从 yt-dlp 核心仓库的 `gui/` 子树拆分到同级目录 `/Users/x/code/yt-dlp-gui`，与核心仓库 `/Users/x/code/yt-dlp` 各自使用独立 Git 历史和版本。迁移测试通过后，核心仓库中的旧 `gui/` 才会移除。

必须保持以下边界：

1. GUI 不导入 `yt_dlp` 私有 Python 模块；所有核心操作通过独立子进程运行 `python -m yt_dlp`。
2. GUI 不在核心目录创建、编辑或删除文件。
3. 默认从 GUI 同级目录 `../yt-dlp` 定位核心；也可设置 `YT_DLP_CORE_DIR` 指向任意包含 `yt_dlp/__init__.py` 的源码检出。
4. GUI 版本、依赖、测试、文档与发布都由 `yt-dlp-gui` 仓库独立维护。
5. 更新核心时运行 GUI 的命令组装与核心路径兼容测试；不向核心重放 GUI 补丁。

## 当前目录结构

```text
/Users/x/code/
├── yt-dlp/       # yt-dlp 核心源码仓库
└── yt-dlp-gui/   # 独立 GUI 项目
```

## 绑定核心

同级布局下直接运行 `./run_gui.sh` 即可。使用其它核心检出时：

```bash
YT_DLP_CORE_DIR=/absolute/path/to/yt-dlp ./run_gui.sh
```

`guiapi.core` 会验证 `yt_dlp/__init__.py` 存在，并仅为 GUI 创建的子进程注入核心目录到 `PYTHONPATH`。

## 上游更新流程

```bash
cd /Users/x/code/yt-dlp
git fetch upstream
git merge upstream/master

cd /Users/x/code/yt-dlp-gui
.venv/bin/python -m pytest
```

核心升级后应确认 GUI 测试通过，并通过核心 CLI 的版本/提取器冒烟；GUI 界面手工验收与自动测试分开记录。
