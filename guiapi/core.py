"""定位相邻的 yt-dlp 核心源码树。

GUI 通过独立子进程调用核心，不导入核心内部模块，也不修改核心目录。

冻结（PyInstaller）打包后，``yt_dlp`` 源码被作为数据一起打包，子进程命令
改为调用打包在同一 bundle 内的独立可执行文件（见 :func:`core_launcher`）。
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    """判断当前是否运行在 PyInstaller 打包后的环境中。"""
    return bool(getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))


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


def core_launcher() -> list[str]:
    """返回调用 yt-dlp 核心 CLI 的命令前缀（不含具体任务参数）。

    开发（源码）模式沿用 ``python -m yt_dlp``，核心源码目录通过
    ``PYTHONPATH`` 注入。冻结打包后，直接调用与 GUI 一同打包的独立可执行
    文件 ``yt-dlp-cli``（内部调用 ``yt_dlp.main()``），无需解释器或
    ``PYTHONPATH``。
    """
    if is_frozen():
        # macOS .app：可执行文件在 Contents/MacOS/，helper 与其同级。
        cli = Path(sys.executable).resolve().parent / 'yt-dlp-cli'
        if cli.is_file():
            return [str(cli)]
        # 兜底：_MEIPASS 下的 helper（单文件模式）。
        cli = Path(sys._MEIPASS) / 'yt-dlp-cli'
        if cli.is_file():
            return [str(cli)]
        raise RuntimeError(
            'Bundled yt-dlp-cli executable not found next to the frozen GUI.')
    return [sys.executable, '-m', 'yt_dlp']


def core_env() -> dict[str, str]:
    """为 GUI 子进程设置核心源码路径，不修改父进程环境。

    冻结模式下核心与 helper 一同打包，helper 自带解释器与依赖，无需注入
    ``PYTHONPATH``，因此直接返回当前环境副本。
    """
    env = os.environ.copy()
    if is_frozen():
        return env
    core = str(core_dir())
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = core if not existing else os.pathsep.join((core, existing))
    return env


_SENSITIVE_FLAGS = {
    '--password',
    '-p',
    '--video-password',
    '--ap-password',
    '--twofactor',
    '--token',
    '--client-certificate-password',
}

_PROXY_CRED_RE = re.compile(r'(://[^:]+):[^@]+@')


def _is_sensitive_flag(flag: str) -> bool:
    normalized = flag.lower().strip()
    return normalized in _SENSITIVE_FLAGS or (
        normalized.startswith('--')
        and any(s in normalized for s in ('password', 'twofactor', 'secret'))
    )


def sanitize_command(cmd: list[str]) -> list[str]:
    """返回对敏感凭据（如密码、Token、Proxy 认证等）进行掩码后的命令行参数列表。

    用于日志打印、界面状态展示与文件落盘，防止用户敏感认证信息明文泄漏。
    """
    sanitized: list[str] = []
    skip_next = False

    for i, arg in enumerate(cmd):
        if skip_next:
            sanitized.append('***')
            skip_next = False
            continue

        if '=' in arg and arg.startswith('-'):
            flag, val = arg.split('=', 1)
            if _is_sensitive_flag(flag):
                sanitized.append(f'{flag}=***')
                continue
            if 'proxy' in flag.lower():
                val = _PROXY_CRED_RE.sub(r'\1:***@', val)
                sanitized.append(f'{flag}={val}')
                continue

        if _is_sensitive_flag(arg):
            sanitized.append(arg)
            if i + 1 < len(cmd):
                skip_next = True
            continue

        if i > 0 and cmd[i - 1].lower() in ('--proxy',):
            arg = _PROXY_CRED_RE.sub(r'\1:***@', arg)

        sanitized.append(arg)

    return sanitized

