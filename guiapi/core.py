"""定位相邻的 yt-dlp 核心源码树。

GUI 通过独立子进程调用核心，不导入核心内部模块，也不修改核心目录。

冻结（PyInstaller）打包后，``yt_dlp`` 源码被作为数据一起打包，子进程命令
改为调用打包在同一 bundle 内的独立可执行文件（见 :func:`core_launcher`）。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

_GUI_ROOT = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    """判断当前是否运行在 PyInstaller 打包后的环境中。"""
    return bool(getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))


def _is_core_checkout(candidate: Path) -> bool:
    """判断路径是否包含可运行的 yt-dlp 源码包。"""
    return (candidate / 'yt_dlp' / '__init__.py').is_file()


def find_core_checkout() -> Path | None:
    """查找可用的 yt-dlp 源码目录；未找到时返回 None 而非抛出异常。"""
    configured = os.environ.get('YT_DLP_CORE_DIR')
    if configured:
        p = Path(configured).expanduser().resolve()
        return p if _is_core_checkout(p) else None

    for candidate in (_GUI_ROOT.parent / 'yt-dlp', _GUI_ROOT.parent):
        candidate = candidate.resolve()
        if _is_core_checkout(candidate):
            return candidate

    return None


def core_dir() -> Path:
    """解析指定核心目录，默认查找同级仓库并兼容旧嵌套目录。"""
    configured = os.environ.get('YT_DLP_CORE_DIR')
    if configured:
        p = Path(configured).expanduser().resolve()
        if _is_core_checkout(p):
            return p
        raise RuntimeError(
            'yt-dlp core checkout not found. Set YT_DLP_CORE_DIR to a directory '
            'that contains yt_dlp/__init__.py, or configure YT_DLP_EXECUTABLE.')

    found = find_core_checkout()
    if found is not None:
        return found

    raise RuntimeError(
        'yt-dlp core checkout not found. Set YT_DLP_CORE_DIR to a directory '
        'that contains yt_dlp/__init__.py, or configure YT_DLP_EXECUTABLE.')


def core_launcher() -> list[str]:
    """返回调用 yt-dlp 核心 CLI 的命令前缀（不含具体任务参数）。

    优先级：
    1. 冻结（PyInstaller）打包环境：调用内置独立可执行文件 ``yt-dlp-cli``；
    2. 显式环境变量 ``YT_DLP_EXECUTABLE``：调用指定路径的可执行文件；
    3. 源码检出目录（同级仓库或 ``YT_DLP_CORE_DIR``）：使用当前 Python 解释器 + 模块启动；
    4. 系统 PATH 中存在的 ``yt-dlp`` 二进制；
    5. 回退到 ``python -m yt_dlp``。
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

    explicit_exe = os.environ.get('YT_DLP_EXECUTABLE')
    if explicit_exe:
        exe_path = Path(explicit_exe).expanduser().resolve()
        if exe_path.is_file():
            return [str(exe_path)]
        raise RuntimeError(f'Configured YT_DLP_EXECUTABLE not found: {explicit_exe}')

    if find_core_checkout() is not None:
        return [sys.executable, '-m', 'yt_dlp']

    system_exe = shutil.which('yt-dlp')
    if system_exe:
        return [system_exe]

    return [sys.executable, '-m', 'yt_dlp']


def core_env() -> dict[str, str]:
    """为 GUI 子进程设置核心源码路径，不修改父进程环境。

    冻结模式与显式可执行文件模式下无需注入 ``PYTHONPATH``；
    源码模式下自动将找到的 core checkout 目录加入 ``PYTHONPATH``。
    """
    env = os.environ.copy()
    if is_frozen() or os.environ.get('YT_DLP_EXECUTABLE'):
        return env

    checkout = find_core_checkout()
    if checkout is not None:
        core = str(checkout)
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = core if not existing else os.pathsep.join((core, existing))
    return env


def probe_core_info(timeout: float = 3.0) -> dict[str, Any]:
    """探测当前绑定的 yt-dlp 核心运行模式、版本与可执行位置。"""
    launcher = core_launcher()
    env = core_env()

    if is_frozen():
        mode = 'frozen'
    elif os.environ.get('YT_DLP_EXECUTABLE'):
        mode = 'executable'
    elif find_core_checkout() is not None:
        mode = 'source'
    elif launcher and shutil.which('yt-dlp') and launcher[0] == shutil.which('yt-dlp'):
        mode = 'system'
    else:
        mode = 'source'

    version = 'unknown'
    try:
        proc = subprocess.run(
            [*launcher, '--version'],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        if proc.returncode == 0:
            version = proc.stdout.strip()
    except Exception:
        pass

    location = launcher[0]
    if mode == 'source':
        checkout = find_core_checkout()
        if checkout is not None:
            location = str(checkout)

    return {
        'version': version,
        'mode': mode,
        'launcher': launcher,
        'location': location,
    }


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

