# ============================================================
# MelodyHub SQLite 数据库层
# ============================================================
"""
SQLite 数据库模块：管理歌曲、收藏、歌单的持久化。

表结构：
  songs           — 本地音乐库（已下载/已收藏的歌曲）
  playlists       — 歌单
  playlist_songs  — 歌单-歌曲多对多关联

特性：
  - WAL 模式（允许并发读写）
  - 外键约束
  - 首次启动自动建表 + 种子数据
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

# 数据库文件路径
DB_PATH = Path(__file__).parent / "melodyhub.db"

# 单例连接（模块级）
_conn: sqlite3.Connection | None = None


# ============================================================
# 数据库初始化
# ============================================================
def _get_conn() -> sqlite3.Connection:
    """获取数据库连接（自动初始化）。"""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _create_tables(_conn)
        _seed_if_empty(_conn)
    return _conn


def _create_tables(conn: sqlite3.Connection):
    """建表（IF NOT EXISTS）。"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS songs (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            artist      TEXT NOT NULL DEFAULT '',
            album       TEXT DEFAULT '',
            duration    TEXT DEFAULT '00:00',
            duration_sec INTEGER DEFAULT 0,
            cover_gradient TEXT DEFAULT '["#7C3AED","#22C55E"]',
            file_path   TEXT DEFAULT '',
            source      TEXT DEFAULT '',
            external_id TEXT DEFAULT '',
            pic_id      TEXT DEFAULT '',
            liked       INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS playlists (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            cover_gradient TEXT DEFAULT '["#7C3AED","#22C55E"]',
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id TEXT NOT NULL,
            song_id     TEXT NOT NULL,
            position    INTEGER DEFAULT 0,
            PRIMARY KEY (playlist_id, song_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_songs_liked ON songs(liked);
        CREATE INDEX IF NOT EXISTS idx_playlist_songs_pid ON playlist_songs(playlist_id);

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # 迁移：旧数据库可能没有 pic_id 列
    try:
        conn.execute("ALTER TABLE songs ADD COLUMN pic_id TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # 列已存在


def _seed_if_empty(conn: sqlite3.Connection):
    """首次启动：不做任何预置数据。"""
    pass


# ============================================================
# 辅助：Row → 前端格式 dict
# ============================================================
def _song_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 songs 表行转为前端需要的格式。"""
    grad = row["cover_gradient"] or '["#7C3AED","#22C55E"]'
    try:
        gradient = json.loads(grad)
    except (json.JSONDecodeError, TypeError):
        gradient = ["#7C3AED", "#22C55E"]

    return {
        "id": row["id"],
        "name": row["name"],
        "artist": row["artist"],
        "duration": row["duration"] or "00:00",
        "durationSec": row["duration_sec"] or 0,
        "coverGradient": gradient,
        "liked": bool(row["liked"]),
        "_album": row["album"] or "",
        "_source": row["source"] or "",
        "_external_id": row["external_id"] or "",
        "_pic_id": row["pic_id"] or "",
        "_file_path": row["file_path"] or "",
    }


def _playlist_to_dict(row: sqlite3.Row, song_count: int, duration_label: str = "") -> dict[str, Any]:
    """将 playlists 表行转为前端格式。"""
    grad = row["cover_gradient"] or '["#7C3AED","#22C55E"]'
    try:
        gradient = json.loads(grad)
    except (json.JSONDecodeError, TypeError):
        gradient = ["#7C3AED", "#22C55E"]

    return {
        "id": row["id"],
        "name": row["name"],
        "songCount": song_count,
        "durationLabel": duration_label or f"{song_count}首",
        "coverGradient": gradient,
        "firstSongId": (row["first_song_id"] if "first_song_id" in row.keys() else ""),
        "firstPicId": (row["first_pic_id"] if "first_pic_id" in row.keys() else ""),
        "firstSource": (row["first_source"] if "first_source" in row.keys() else ""),
    }


# ============================================================
# 歌曲 CRUD
# ============================================================
def get_all_songs() -> list[dict[str, Any]]:
    """返回音乐库所有歌曲。"""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM songs ORDER BY created_at DESC").fetchall()
    return [_song_to_dict(r) for r in rows]


def get_song_by_id(song_id: str) -> dict[str, Any] | None:
    """按 ID 查找一首歌曲。"""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    return _song_to_dict(row) if row else None


def add_song(data: dict[str, Any]) -> dict[str, Any]:
    """添加或更新一首歌曲（Upsert）。下载后调用此函数记录到库。"""
    conn = _get_conn()
    grad = data.get("coverGradient", ["#7C3AED", "#22C55E"])
    if isinstance(grad, list):
        grad = json.dumps(grad)

    conn.execute(
        """INSERT INTO songs (id, name, artist, album, duration, duration_sec,
           cover_gradient, file_path, source, external_id, pic_id, liked)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
           name=excluded.name, artist=excluded.artist, album=excluded.album,
           duration=excluded.duration, duration_sec=excluded.duration_sec,
           cover_gradient=excluded.cover_gradient, file_path=excluded.file_path,
           source=excluded.source, external_id=excluded.external_id,
           pic_id=excluded.pic_id""",
        (
            data.get("id", ""),
            data.get("name", ""),
            data.get("artist", ""),
            data.get("album", ""),
            data.get("duration", "00:00"),
            data.get("durationSec", 0),
            grad,
            data.get("filePath", ""),
            data.get("source", ""),
            data.get("externalId", ""),
            data.get("picId", data.get("_pic_id", "")),
            0,
        )
    )
    conn.commit()
    return get_song_by_id(data.get("id", ""))


def toggle_liked(song_id: str) -> bool:
    """切换歌曲收藏状态，返回新状态。"""
    conn = _get_conn()
    row = conn.execute("SELECT liked FROM songs WHERE id = ?", (song_id,)).fetchone()
    if not row:
        # 歌曲不在库中，忽略
        return False
    new_liked = 0 if row["liked"] else 1
    conn.execute("UPDATE songs SET liked = ? WHERE id = ?", (new_liked, song_id))
    conn.commit()
    return bool(new_liked)


def get_liked_songs() -> list[dict[str, Any]]:
    """返回所有收藏的歌曲。"""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM songs WHERE liked = 1 ORDER BY created_at DESC").fetchall()
    return [_song_to_dict(r) for r in rows]


# ============================================================
# 歌单 CRUD
# ============================================================
def get_all_playlists() -> list[dict[str, Any]]:
    """返回所有歌单及其歌曲数和第一首歌的封面信息。"""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT p.*, COUNT(ps.song_id) as song_count,
               (SELECT s.id FROM playlist_songs ps2 JOIN songs s ON ps2.song_id = s.id WHERE ps2.playlist_id = p.id ORDER BY ps2.position LIMIT 1) as first_song_id,
               (SELECT s.pic_id FROM playlist_songs ps2 JOIN songs s ON ps2.song_id = s.id WHERE ps2.playlist_id = p.id ORDER BY ps2.position LIMIT 1) as first_pic_id,
               (SELECT s.source FROM playlist_songs ps2 JOIN songs s ON ps2.song_id = s.id WHERE ps2.playlist_id = p.id ORDER BY ps2.position LIMIT 1) as first_source
        FROM playlists p
        LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    return [_playlist_to_dict(r, r["song_count"] or 0) for r in rows]


def get_playlist_songs(playlist_id: str) -> list[dict[str, Any]]:
    """返回歌单中所有歌曲。"""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT s.* FROM songs s
        JOIN playlist_songs ps ON s.id = ps.song_id
        WHERE ps.playlist_id = ?
        ORDER BY ps.position
    """, (playlist_id,)).fetchall()
    return [_song_to_dict(r) for r in rows]


def add_playlist(name: str) -> dict[str, Any]:
    """创建新歌单。"""
    import uuid
    conn = _get_conn()
    pl_id = str(uuid.uuid4())[:8]
    conn.execute("INSERT INTO playlists (id, name) VALUES (?,?)", (pl_id, name))
    conn.commit()
    return _playlist_to_dict(
        conn.execute("SELECT * FROM playlists WHERE id = ?", (pl_id,)).fetchone(),
        0, "0首"
    )


def delete_playlist(playlist_id: str) -> bool:
    """删除歌单。"""
    conn = _get_conn()
    conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    conn.commit()
    return True


def add_song_to_playlist(playlist_id: str, song_id: str) -> bool:
    """将歌曲加入歌单。同时确保歌曲已入库。"""
    conn = _get_conn()
    # 获取当前最大 position
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 as next FROM playlist_songs WHERE playlist_id = ?",
        (playlist_id,)
    ).fetchone()
    conn.execute(
        "INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id, position) VALUES (?,?,?)",
        (playlist_id, song_id, row["next"] if row else 0)
    )
    conn.commit()
    return True


def remove_song_from_playlist(playlist_id: str, song_id: str) -> bool:
    """从歌单中移除歌曲。"""
    conn = _get_conn()
    conn.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                 (playlist_id, song_id))
    conn.commit()
    return True


def reorder_playlist_songs(playlist_id: str, song_ids: list[str]) -> bool:
    """重新排序歌单中的歌曲。"""
    conn = _get_conn()
    for i, sid in enumerate(song_ids):
        conn.execute(
            "UPDATE playlist_songs SET position = ? WHERE playlist_id = ? AND song_id = ?",
            (i, playlist_id, sid))
    conn.commit()
    return True


def rename_playlist(playlist_id: str, new_name: str) -> bool:
    """重命名歌单。"""
    conn = _get_conn()
    conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id))
    conn.commit()
    return True


# ============================================================
# 设置（键值对）
# ============================================================
def set_setting(key: str, value: str):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()


def get_setting(key: str, default: str = "") -> str:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


# ============================================================
# 工具
# ============================================================
def close():
    """关闭数据库连接。"""
    global _conn
    if _conn:
        _conn.close()
        _conn = None
