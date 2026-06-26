# MelodyHub FastAPI 后端 M0 实现概述

## 完成内容

已实现一个可本地运行的 Python 后端，并接入真实的 Meting 数据源，完成 M0 技术验证的核心目标。

## 新增/更新文件

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 后端入口，提供 7 个 MVP API 端点 + 真实搜索/下载 |
| `backend/mock_data.py` | 从 `test_data.js` 提取的内存数据 |
| `backend/meting_server.mjs` | 封装 `@meting/core` 的 Node.js 微服务 |
| `backend/meting_adapter.py` | Python 调用 Meting 的 HTTP 客户端 |
| `backend/launcher.py` | 服务启动器：启动 Meting + FastAPI + 自动打开浏览器 + Ctrl+C 统一停止 |
| `backend/prepare_static.py` | 将 `melodyhub.html` 转换为后端模式 |
| `backend/static/index.html` | 改造后的前端页面（关闭 mock、移除 test_data.js） |
| `backend/static/data.js` | 前端静态配置（复制） |
| `backend/README.md` | 安装/启动/接口文档 |
| `backend/OVERVIEW.md` | 本概述文件 |
| `start_backend.bat` | 双击调用 `backend/launcher.py` 启动全部服务 |
| `Music/Faded - Alan Walker.mp3` | M0 下载验证文件 |

## 启动方式

双击项目根目录的 `start_backend.bat`，会自动启动：
- Meting Node.js 服务（`http://127.0.0.1:3000`）
- Python FastAPI 服务（`http://127.0.0.1:8000`）

然后浏览器打开 **http://127.0.0.1:8000**

## 验证结果

- Meting Node.js 服务可正常搜索网易云音乐
- Python 后端 `/api/search` 成功返回真实搜索结果（含 Faded 多版本）
- 下载接口成功下载 `Faded - Alan Walker.mp3` 到 `Music/` 目录
- 文件可解析：45s / 128kbps / 44100Hz（免费试听片段）
- 前端搜索页面成功渲染真实数据，浏览器控制台无错误
- 验证截图：`backend/static/render-search-check.png`

## 关键修复

1. `data.js` 路径问题：前端请求 `/data.js`，但后端静态文件挂载在 `/static`。通过 `prepare_static.py` 将路径改为 `static/data.js` 解决。
2. `test_data.js` 残留：原始 HTML 使用 CRLF 换行，简单字符串替换失败。改用正则兼容 CRLF/LF 彻底移除。
3. 下载目录权限问题：首次使用 `~/MelodyHub/Music` 被沙箱拦截，改为项目根目录 `Music/`。
4. 端口占用问题：旧 Python 进程未释放 8000，通过 `taskkill` 清理。
5. `start_backend.bat` 不可靠：旧脚本用 `start` 命令开新窗口启动 Meting，失败时窗口一闪而过难以排查；且未检测环境/端口/自动打开浏览器。改为调用 `backend/launcher.py`，统一在同一个窗口启动、检查端口、自动打开浏览器、Ctrl+C 统一停止，并把 Meting 日志写入 `backend/logs/meting.log`。
6. **编码问题**：重写的 batch 文件为 UTF-8 无 BOM，在中文 Windows（默认代码页 936/GBK）下被错误解析为乱码，命令拆散导致无法运行。最终改为 **纯 ASCII 批处理** + `chcp 65001` + `set PYTHONUTF8=1`，中文提示全部下沉到 Python 启动器，避免编码问题。

## 后续步骤

- 用 SQLite 持久化歌曲/收藏/歌单数据
- 实现下载时自动写入封面、歌词等元数据（mutagen 已安装）
- 前端增加下载按钮，调用 `/api/download`
- 集成 MusicBrainz 深度元数据补全
- 接入 Last.fm 封面兜底
