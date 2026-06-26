import re
from pathlib import Path


def prepare_static_files():
    """将前端页面转换为后端模式：使用真实 API，不再加载 test_data.js"""

    project_root = Path(__file__).parent.parent
    backend_dir = Path(__file__).parent
    static_dir = backend_dir / "static"
    static_dir.mkdir(exist_ok=True)

    # 1. 复制 data.js
    src_data = project_root / "data.js"
    dst_data = static_dir / "data.js"
    if src_data.exists():
        dst_data.write_text(src_data.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Copied: {src_data} -> {dst_data}")
    else:
        print(f"Warning: {src_data} not found")

    # 2. 读取 melodyhub.html 并打补丁
    src_html = project_root / "melodyhub.html"
    dst_html = static_dir / "index.html"

    if not src_html.exists():
        raise FileNotFoundError(f"Source HTML not found: {src_html}")

    content = src_html.read_text(encoding="utf-8")

    # 移除 test_data.js 引用及其注释（兼容 LF/CRLF 换行）
    content = re.sub(
        r'<!-- 后端模拟数据 — 歌曲/搜索/收藏/歌单/歌词等，后端开发完成后删除此文件 -->\r?\n<script src="test_data\.js"></script>\r?\n?',
        '',
        content
    )

    # 修改 data.js 路径：从后端 static 目录加载
    content = content.replace(
        '<script src="data.js"></script>',
        '<script src="static/data.js"></script>'
    )

    # 切换到真实 API 模式
    content = content.replace(
        'var USE_MOCK = true;',
        'var USE_MOCK = false;'
    )

    # 修改 getLibrarySongs：后端返回 { songs: [...] }，前端提取 .songs
    content = content.replace(
        "    return fetch('/api/library').then(r => r.json());",
        "    return fetch('/api/library').then(r => r.json()).then(data => data.songs);"
    )

    dst_html.write_text(content, encoding="utf-8")
    print(f"Generated: {dst_html}")
    print("Static files prepared. Run: python backend/main.py")


if __name__ == "__main__":
    prepare_static_files()
