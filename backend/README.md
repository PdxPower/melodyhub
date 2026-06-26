# MelodyHub 后端服务 (M0)

> 版本：v0.2.0
> 功能：
> 1. 把 `test_data.js` 的模拟数据通过 REST API 发送给前端
> 2. 接入真实 Meting Node.js 服务，实现跨平台音乐搜索、下载、歌词、封面
> 暂未使用数据库，收藏/搜索 fallback 等状态存在内存中。

---

## 快速启动

### 最简单：双击启动

项目根目录 `start_backend.bat` —— 双击即可同时启动：
- Meting Node.js 服务（端口 3000）
- Python FastAPI 服务（端口 8000）

启动后浏览器打开 **http://127.0.0.1:8000**

---

### 手动启动（排查问题时用）

#### 1. 安装依赖（首次）

```powershell
C:\Users\86136\.workbuddy\binaries\python\versions\3.13.12\python.exe -m venv C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub
C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub\Scripts\pip.exe install fastapi uvicorn httpx mutagen
```

```powershell
cd D:\WorkBuddy\music_player
C:\Users\86136\.workbuddy\binaries\node\versions\22.22.2\node.exe C:\Users\86136\.workbuddy\binaries\node\versions\22.22.2\node_modules\npm\bin\npm-cli.js install @meting/core
```

#### 2. 生成前端静态文件

```powershell
C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub\Scripts\python.exe backend\prepare_static.py
```

> 把 `melodyhub.html` 转换成后端版 `backend/static/index.html`，并复制 `data.js`。

#### 3. 启动两个服务

先开 Meting（端口 3000）：

```powershell
C:\Users\86136\.workbuddy\binaries\node\versions\22.22.2\node.exe backend\meting_server.mjs
```

再开 Python 后端（端口 8000），在新终端执行：

```powershell
C:\Users\86136\.workbuddy\binaries\python\envs\melodyhub\Scripts\python.exe backend\main.py
```

---

## 文件说明

| 文件 | 作用 |
|------|------|
| `backend/main.py` | FastAPI 后端入口，提供 7 个 MVP 端点 + 真实搜索/下载 |
| `backend/mock_data.py` | 从 `test_data.js` 提取的内存模拟数据 |
| `backend/meting_server.mjs` | Node.js 微服务，封装 `@meting/core` |
| `backend/meting_adapter.py` | Python 调用 Meting 服务的 HTTP 客户端 |
| `backend/launcher.py` | 一键启动器：启动 Meting + FastAPI + 自动打开浏览器 |
| `backend/prepare_static.py` | 将前端页面转换为「后端模式」并复制到 `backend/static/` |
| `backend/static/index.html` | 改造后的前端页面，已关闭 mock 模式 |
| `backend/static/data.js` | 前端静态配置（复制） |
| `start_backend.bat` | Windows 一键启动脚本，调用 `backend/launcher.py` |

---

## 提供的 API 端点

### 7 个 MVP 端点（前端已对接）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回前端页面 |
| GET | `/api/library` | 音乐库歌曲列表，返回 `{ songs: [...] }` |
| GET | `/api/search?q=...` | 真实搜索，失败回退模拟数据 |
| GET | `/api/player/state` | 当前播放状态 |
| GET | `/api/favorites` | 收藏列表 |
| GET | `/api/playlists` | 歌单列表 |
| GET | `/api/lyrics?songId=...` | 歌词（真实优先，失败回退模拟） |
| POST | `/api/favorites/toggle` | 切换收藏状态，请求体 `{ songId }` |

### M0 新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/meting/health` | 检查 Meting Node.js 服务是否可用 |
| POST | `/api/download` | 下载歌曲到本地 `Music/` 目录 |

#### `/api/download` 请求体示例

```json
{
  "song_id": "36990266",
  "source": "netease",
  "name": "Faded",
  "artist": "Alan Walker"
}
```

---

## 开发提示

- 搜索接口 `fallback=true` 时，会在当前平台失败时自动尝试 `netease/tencent/kugou/kuwo/baidu`。
- 下载目录默认在项目根目录 `Music/`，可在 `backend/main.py` 顶部修改 `MUSIC_DIR`。
- 后端已开启 CORS，支持 `http://127.0.0.1:8000` 和 `file://` 两种打开方式。
- 后续接数据库时，把 `mock_data.py` 中的 `MOCK_DATA` 替换为 SQLite 查询即可。
