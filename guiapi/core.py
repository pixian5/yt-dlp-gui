"""定位相邻的 yt-dlp 核心源码树。

GUI 通过独立子进程调用核心，不导入核心内部模块，也不修改核心目录。
"""

from __future__ import annotations

import os
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parent.parent


def _is_core_checkout(candidate: Path) -> bool:
    """判断路径是否包含可运行的 yt-dlp 源码包。"""
    return (candidate / 'yt_dlp' / '__init__.py').is_file()


def core_dir() -> Path:
    """解析指定核心目录，默认查找同级仓库并兼容旧嵌套目录。"""
    configured = os.environ.get('YT_DLP_CORE_DIR')
    if configured:
        candidates = (Path(configured).expanduser(),)
    else:
        # 新布局：yt-dlp 与 yt-dlp-gui 是同级目录；旧布局仍允许 GUI 位于核心/gui。
        candidates = (_GUI_ROOT.parent / 'yt-dlp', _GUI_ROOT.parent)

    for candidate in candidates:
        candidate = candidate.resolve()
        if _is_core_checkout(candidate):
            return candidate

    raise RuntimeError(
        'yt-dlp core checkout not found. Set YT_DLP_CORE_DIR to a directory '
        'that contains yt_dlp/__init__.py.')


def core_env() -> dict[str, str]:
    """为 GUI 子进程设置核心源码路径，不修改父进程环境。"""
    env = os.environ.copy()
    core = str(core_dir())
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = core if not existing else os.pathsep.join((core, existing))
    return env
