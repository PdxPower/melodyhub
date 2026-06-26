#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MelodyHub 后端服务启动器

功能：
- 启动 Meting Node.js 服务（端口 3000）
- 启动 Python FastAPI 服务（端口 8000）
- 等待服务就绪后自动打开浏览器
- Ctrl+C 时停止所有子进程

用法：直接双击项目根目录的 start_backend.bat
"""

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ============================================================
# 路径配置（根据当前环境）
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

NODE_EXE = Path(r"C:\Users\86136\.workbuddy\binaries\node\versions\22.22.2\node.exe")
PYTHON_EXE = Path(r"C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub\Scripts\python.exe")

METING_PORT = 3000
BACKEND_PORT = 8000

METING_SCRIPT = BACKEND_DIR / "meting_server.mjs"
BACKEND_SCRIPT = BACKEND_DIR / "main.py"


# ============================================================
# 工具函数
# ============================================================
def say(*args, **kwargs):
    """立即刷新输出，避免在管道/子进程混合时显示异常。"""
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def is_port_open(port: int, timeout: float = 1.0) -> bool:
    """检查端口是否已可连接。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    """等待端口在指定时间内就绪。"""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port):
            return True
        time.sleep(0.5)
    return False


def preflight_check() -> bool:
    """启动前检查可执行文件和脚本是否存在。"""
    ok = True
    for label, path in [("Node.js", NODE_EXE), ("Python", PYTHON_EXE)]:
        if not path.exists():
            say(f"[错误] 找不到 {label}：{path}")
            say("        请确认运行时已正确安装。")
            ok = False
    for label, path in [("Meting 脚本", METING_SCRIPT), ("后端入口", BACKEND_SCRIPT)]:
        if not path.exists():
            say(f"[错误] 找不到 {label}：{path}")
            ok = False
    return ok


def terminate_process(process: subprocess.Popen | None, label: str) -> None:
    """安全终止子进程。"""
    if process is None or process.poll() is not None:
        return
    say(f"[..] 正在停止 {label} (PID {process.pid})...")
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        say(f"[警告] {label} 未正常退出，强制结束。")
        process.kill()
        process.wait(timeout=5)
    except Exception as e:
        say(f"[警告] 停止 {label} 时出错：{e}")


# ============================================================
# 主流程
# ============================================================
def main() -> int:
    say("=" * 48)
    say("  MelodyHub 后端启动器")
    say("=" * 48)
    say(f"  项目目录：{PROJECT_ROOT}")
    say("")

    if not preflight_check():
        input("按回车键退出...")
        return 1

    meting_process: subprocess.Popen | None = None
    backend_process: subprocess.Popen | None = None

    try:
        # ---------- 启动 Meting ----------
        if is_port_open(METING_PORT):
            say(f"[警告] 端口 {METING_PORT} 已被占用，跳过 Meting 启动。")
        else:
            say(f"[..] 启动 Meting 服务，端口 {METING_PORT}...")
            meting_log = open(LOG_DIR / "meting.log", "w", encoding="utf-8", errors="ignore")
            meting_process = subprocess.Popen(
                [str(NODE_EXE), str(METING_SCRIPT)],
                cwd=PROJECT_ROOT,
                stdout=meting_log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            if not wait_for_port(METING_PORT, timeout=10):
                say(f"[错误] Meting 服务未能在 10 秒内就绪，请检查 backend/logs/meting.log。")
                return 1
            say(f"[OK] Meting 服务已启动 (PID {meting_process.pid})。")

        say("")

        # ---------- 启动 Python 后端 ----------
        if is_port_open(BACKEND_PORT):
            say(f"[警告] 端口 {BACKEND_PORT} 已被占用，跳过 Python 后端启动。")
        else:
            say(f"[..] 启动 Python 后端，端口 {BACKEND_PORT}...")
            backend_process = subprocess.Popen(
                [str(PYTHON_EXE), str(BACKEND_SCRIPT)],
                cwd=PROJECT_ROOT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            if not wait_for_port(BACKEND_PORT, timeout=10):
                say(f"[错误] Python 后端未能在 10 秒内就绪。")
                return 1
            say(f"[OK] Python 后端已启动 (PID {backend_process.pid})。")

        say("")
        say("[OK] 全部服务已就绪。")
        say(f"     正在打开浏览器：http://127.0.0.1:{BACKEND_PORT}")
        try:
            webbrowser.open(f"http://127.0.0.1:{BACKEND_PORT}")
        except Exception as e:
            say(f"[警告] 自动打开浏览器失败：{e}")

        say("")
        say("按 Ctrl+C 停止所有服务。")

        # 保持运行，直到用户按 Ctrl+C
        while True:
            time.sleep(1)
            # 如果子进程意外退出，提示用户
            if meting_process and meting_process.poll() is not None:
                say("[警告] Meting 服务已退出。")
                meting_process = None
            if backend_process and backend_process.poll() is not None:
                say("[警告] Python 后端已退出。")
                backend_process = None

    except KeyboardInterrupt:
        say("\n[..] 收到停止信号，正在关闭服务...")
    finally:
        terminate_process(backend_process, "Python 后端")
        terminate_process(meting_process, "Meting 服务")
        say("[OK] 所有服务已停止。")
        input("按回车键关闭窗口...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
