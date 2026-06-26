# MelodyHub 后端架构设计 — AI 提示词

> 直接复制以下全部内容，粘贴给 AI 即可。已包含项目全量上下文、API 规格、数据库设计要求和架构约束。

---

## 提示词正文

请为 **MelodyHub — 个人音乐库App** 设计一套完整的后端架构方案，务必做到高可用、高性能、高并发。以下是项目全量上下文，请基于此进行架构设计。

### 一、项目定位

MelodyHub 是一款**个人本地音乐图书馆工具**（非流媒体），核心闭环为：跨平台聚合搜索 → 音频下载到本地 → 元数据自动补全 → 本地播放 → 歌单管理。定位为"个人自用工具"，不做社交/推荐/分发/商业化。

合规边界：**"个人自用可容，分发即越线"**。音频获取依赖平台逆向接口（已知结构性风险），元数据获取走合规API（MusicBrainz ODbL / Last.fm免费Key）。

### 二、技术栈约束

| 层 | 已确定方案 | 说明 |
|----|-----------|------|
| 外部数据获取层 | **Meting** (Node.js v1.6.1) | 网易云/QQ音乐/酷狗/酷我/百度 5平台聚合，搜索/下载/歌词/封面 |
| 元数据增强层 | **MusicBrainz API** + Cover Art Archive | 作词/作曲/ISRC/发行年/专辑，合规(ODbL)，限流 1 req/s |
| 封面兜底层 | **Last.fm API** | 封面兜底 + 相似艺术家(免费Key) |
| 本地数据库 | **SQLite** (WAL模式) | 轻量零配置，Python内置支持 |
| ID3标签写入 | **mutagen** (Python) | 音频元数据读写 |
| 音频播放 | **pygame.mixer** 或 **vlc-python** | 后台稳定播放 ≥2小时 |
| HTTP请求 | **httpx** (Python, 异步) | 外部API调用，支持并发 |
| 后端服务框架 | **FastAPI** (Python) | 异步高性能，自带OpenAPI文档 |

### 三、前端已定义的 API 接口规格

前端原型 `melodyhub.html` 已通过 `api` 服务层定义了以下 7 个后端接口，架构设计必须精确覆盖这些端点的请求/响应格式：

| # | 方法 | 路径 | 功能 | 前端调用方式 | 响应数据结构 |
|---|------|------|------|-------------|-------------|
| 1 | GET | `/api/library` | 用户音乐库歌曲列表 | `api.getLibrarySongs()` | `{ songs: [{ id, name, artist, duration, durationSec, coverGradient, liked }] }` |
| 2 | GET | `/api/search?q={keyword}` | 跨平台搜索歌曲 | `api.getSearchResults(query)` | `{ results: [{ id, name, artist, duration, coverGradient, liked }] }` |
| 3 | GET | `/api/player/state` | 当前播放状态 | `api.getPlayerState()` | `{ currentSongId, initialProgress, initialVolume }` |
| 4 | GET | `/api/favorites` | 用户收藏列表 | `api.getFavorites()` | `{ totalLabel, items: [{ songId, name, artist, duration, coverGradient }] }` |
| 5 | GET | `/api/playlists` | 用户歌单列表 | `api.getPlaylists()` | `{ items: [{ id, name, songCount, durationLabel, coverGradient }] }` |
| 6 | GET | `/api/lyrics?songId={id}` | 获取歌词 | `api.getLyrics(songId)` | `{ songName, artist, lines: [{ text, state }] }` |
| 7 | POST | `/api/favorites/toggle` | 切换收藏状态 | `api.toggleFavorite(songId)` | `{ success: true }` 请求体: `{ songId }` |

**架构设计要求**：以上 7 个端点是 MVP 必须100%覆盖的。P1/P2 阶段需额外扩展以下端点（请在架构中预留接口设计）：

| 扩展端点 | 功能 | 优先级 |
|---------|------|--------|
| POST `/api/download` | 触发音频下载任务 | P0 |
| GET `/api/download/{taskId}/status` | 查询下载进度 | P0 |
| POST `/api/playlists` | 创建歌单 | P0 |
| PUT `/api/playlists/{id}` | 编辑歌单(重命名/排序) | P1 |
| DELETE `/api/playlists/{id}` | 删除歌单 | P1 |
| POST `/api/playlists/{id}/songs` | 向歌单添加歌曲 | P0 |
| DELETE `/api/playlists/{id}/songs/{songId}` | 从歌单移除歌曲 | P0 |
| GET `/api/library?sort={field}&order={asc|desc}&filter={field}:{value}` | 库搜索排序筛选 | P1 |
| PUT `/api/player/state` | 更新播放状态(进度/音量/模式) | P1 |
| GET `/api/metadata/enrich?songId={id}` | MusicBrainz深度元数据补全 | P1 |

### 四、数据库设计要求

基于 PRD 中描述的 SQLite 库索引结构，设计完整的数据库 schema：

**核心表**：
- `songs`：文件路径/标题/艺术家/专辑/ISRC/作词/作曲/时长/封面路径/歌词路径/收藏标记/下载时间/来源平台
- `playlists`：歌单名/创建时间/更新时间
- `playlist_songs`：歌单-歌曲关联(多对多，含排序序号)
- `download_tasks`：下载任务ID/歌曲信息/来源平台/状态/进度/创建时间
- `metadata_cache`：外部API响应缓存(Meting/MusicBrainz/Last.fm)，含过期时间

**性能要求**：
- 所有查询响应时间 < 20ms（本地SQLite完全可达）
- 为高频查询字段建立合适索引（歌名、艺术家、收藏标记、歌单关联）
- 使用 WAL 模式支持读写并发
- 外部API响应必须本地缓存，避免重复请求

### 五、"三高"架构设计核心要求

#### 5.1 高可用

1. **多源 fallback 机制**：Meting 5平台任何单一平台接口失效时，自动切换到下一个平台，确保搜索/下载不因单点故障中断
2. **元数据兜底链路**：封面获取遵循 Meting → Last.fm → Cover Art Archive → 默认占位 的四级降级链；深度元数据遵循 MusicBrainz → Meting基础信息 → 仅文件名 的三级降级
3. **本地优先策略**：所有数据先查本地SQLite缓存，缓存命中则不调用外部API；缓存过期才触发外部请求
4. **进程级容错**：Meting Node.js服务作为独立进程运行，Python后端通过子进程/HTTP桥接；Meting崩溃时自动重启，不影响主进程
5. **数据持久化保障**：SQLite WAL模式 + 定期checkpoint；下载任务状态持久化，支持断点续传

#### 5.2 高性能

1. **异步并发架构**：后端使用 FastAPI (async) + httpx 异步HTTP客户端；搜索时并行调用多个Meting平台，元数据获取时并行调用 MusicBrainz + Last.fm
2. **本地缓存体系**：SQLite metadata_cache 表缓存所有外部API响应；封面图片本地文件缓存；LRU淘汰策略，命中率目标 ≥ 80%
3. **数据库性能**：SQLite WAL模式 + 合理索引 + 预编译语句(prepared statements)；批量写入使用事务(batch INSERT)
4. **连接池管理**：httpx 连接池复用TCP连接，避免重复握手；连接池大小根据并发需求动态调整
5. **懒加载 + 分页**：音乐库列表支持分页加载(默认50首/页)；封面图按需加载，不在列表接口中返回大图

#### 5.3 高并发

1. **异步事件循环**：FastAPI 基于 uvicorn + asyncio，单进程即可处理数百并发请求（个人App足够）
2. **外部API限流遵守**：MusicBrainz 严格 1 req/s 限流（令牌桶算法）；Last.fm 遵守其Rate Limit；Meting无官方限流但需自我保护(每平台5 req/s上限)
3. **并发下载队列**：最多3个并发下载任务，超过排队；下载任务状态通过WebSocket或轮询端点实时推送
4. **非阻塞播放器控制**：播放器操作(播放/暂停/切歌)通过独立线程/进程，不阻塞API请求处理
5. **读写分离设计**：SQLite WAL模式下读不阻塞写；高频读操作(库浏览/收藏列表)走缓存，写操作(下载/收藏切换)走事务

### 六、架构分层设计要求

请按以下分层输出架构设计：

```
┌─────────────────────────────────────┐
│  API Gateway Layer (FastAPI)        │  ← 请求路由/鉴权/限流/日志
├─────────────────────────────────────┤
│  Service Layer                      │  ← 业务逻辑编排
│  ├ LibraryService                   │
│  ├ SearchService                    │
│  ├ DownloadService                  │
│  ├ PlayerService                    │
│  ├ MetadataOrchestrator             │  ← 多源调度/降级/合并
│  ├ FavoriteService                  │
│  └ PlaylistService                  │
├─────────────────────────────────────┤
│  Data Access Layer                  │  ← SQLite ORM/缓存管理
├─────────────────────────────────────┤
│  External API Adapter Layer         │  ← Meting/MusicBrainz/Last.fm
│  ├ MetingAdapter (Node.js桥接)      │
│  ├ MusicBrainzAdapter (限流+缓存)   │
│  └ LastFmAdapter (限流+缓存)        │
├─────────────────────────────────────┤
│  Infrastructure Layer               │  ← 进程管理/文件系统/播放引擎
└─────────────────────────────────────┘
```

### 七、安全设计要求

虽然是个人本地工具，仍需遵循安全最佳实践：

1. **本地API服务仅绑定 localhost**：FastAPI 监听 127.0.0.1:8000，不暴露到局域网
2. **外部API Key安全存储**：Last.fm API Key / MusicBrainz App Name 存入环境变量或本地加密配置文件，不硬编码
3. **下载文件路径校验**：防止路径遍历攻击，下载目标限定在 ~/MelodyHub/Music/ 内
4. **输入验证**：搜索关键词长度限制(≤200字符)；歌曲ID格式校验(UUID)；歌单名长度限制
5. **日志安全**：不记录音频URL(含临时签名token)；不记录用户搜索历史到持久日志

### 八、交付要求

请按以下结构输出完整架构设计文档：

1. **系统架构总览** — 分层架构图 + 组件关系图 + 数据流图
2. **数据库Schema** — 完整DDL(含索引/约束/触发器) + ER图
3. **API接口规格** — 所有端点的详细定义(请求/响应/错误码/限流规则)
4. **服务层设计** — 每个Service的职责/依赖/核心方法/错误处理策略
5. **外部API适配层** — Meting桥接方案/MusicBrainz限流实现/Last.fm调用封装
6. **缓存策略** — 缓存层级/失效策略/命中率目标/缓存穿透保护
7. **并发与限流** — 异步架构设计/下载队列/外部API限流实现/播放器线程模型
8. **容错与降级** — 多源fallback链路/故障检测/自动恢复/数据一致性保障
9. **安全设计** — 上述5条安全要求的实现方案
10. **部署与运维** — 本地启动流程/进程管理/日志配置/数据备份策略
11. **性能基准** — 各核心操作的目标响应时间 + 测试方案

### 九、补充约束

- 用户为初中生开发者，Python初学者水平，有CustomTkinter经验 — 架构设计需**代码可读性优先**，避免过度抽象
- 项目MVP期限：7/14–8/10（4周），架构设计需**渐进式可落地**，不要一次设计过于复杂
- Meting服务是Node.js独立进程 — Python后端与Meting的通信方式(HTTP桥接 vs 子进程pipe)需明确选择并给出理由
- SQLite是唯一数据库 — 不引入Redis/PostgreSQL等额外依赖（个人工具保持极简）
- 所有外部API调用必须**本地缓存** — MusicBrainz限流1req/s，不缓存等于放弃这个数据源
