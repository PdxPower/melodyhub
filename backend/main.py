# ============================================================
# MelodyHub 后端服务 (FastAPI)
# 版本：v0.3.0 (M1 MVP — SQLite 数据持久化)
# ============================================================

from fastapi import FastAPI, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn
import httpx
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from meting_adapter import (
    search as meting_search,
    search_with_fallback,
    get_url as meting_get_url,
    get_url_with_fallback,
    get_lyric as meting_get_lyric,
    get_pic as meting_get_pic,
    health as meting_health,
    METING_BASE_URL,
)

import database as db
from mock_data import MOCK_DATA  # 仅用于歌词/播放状态等暂未入库的数据


# ============================================================
# 应用配置
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    db.close()


app = FastAPI(
    title="MelodyHub Backend",
    description="MelodyHub 个人音乐库后端服务（M1 SQLite 持久化版）",
    version="0.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


# ============================================================
# 应用生命周期：关闭时清理数据库连接
# ============================================================
# ============================================================
# 工具函数
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent
MUSIC_DIR = PROJECT_ROOT / "Music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)
COVER_DIR = PROJECT_ROOT / "Music" / "covers"
COVER_DIR.mkdir(parents=True, exist_ok=True)

# 音频文件静态服务
app.mount("/Music", StaticFiles(directory=MUSIC_DIR), name="music")


def _gradient_from_string(s: str) -> List[str]:
    gradients = [
        ["#7C3AED", "#22C55E"],
        ["#3366CC", "#CC3344"],
        ["#E6801A", "#E63366"],
        ["#4D8C50", "#1A4D99"],
        ["#8B5CF6", "#EC4899"],
        ["#0EA5E9", "#10B981"],
    ]
    idx = int(hashlib.md5(s.encode()).hexdigest(), 16) % len(gradients)
    return gradients[idx]


def _meting_result_to_frontend(item: Dict[str, Any]) -> Dict[str, Any]:
    """将 Meting 搜索结果转换为前端格式。"""
    artists = item.get("artist", [])
    artist_str = ", ".join(artists) if isinstance(artists, list) else str(artists)
    return {
        "id": str(item.get("id", "")),
        "name": item.get("name", "Unknown"),
        "artist": artist_str,
        "duration": "00:00",
        "durationSec": 0,
        "coverGradient": _gradient_from_string(item.get("name", "") + artist_str),
        "liked": False,
        "_url_id": str(item.get("url_id", item.get("id", ""))),
        "_lyric_id": str(item.get("lyric_id", item.get("id", ""))),
        "_pic_id": str(item.get("pic_id", item.get("id", ""))),
        "_source": item.get("source", "netease"),
        "_album": item.get("album", "")
    }


# ============================================================
# Meting 健康检查
# ============================================================
@app.get("/api/meting/health")
async def meting_health_check():
    return await meting_health()


# ============================================================
# API 端点 — 音乐库
# ============================================================
@app.get("/api/library")
async def get_library():
    """音乐库歌曲列表（SQLite）。"""
    songs = db.get_all_songs()
    return {"songs": songs}


# ============================================================
# API 端点 — 搜索
# ============================================================
@app.get("/api/search")
async def search(
    q: str = Query(default="", description="搜索关键词"),
    source: str = Query(default="netease"),
    fallback: bool = Query(default=True)
):
    if not q.strip():
        return {"defaultQuery": "", "results": db.get_all_songs()}

    try:
        if fallback:
            raw_results = await search_with_fallback(
                q, sources=[source, "netease", "tencent", "kugou", "kuwo", "baidu"], limit=10
            )
        else:
            raw_results = await meting_search(q, source=source, limit=10)
        results = [_meting_result_to_frontend(item) for item in raw_results]
        return {"defaultQuery": q, "results": results}
    except Exception as e:
        print(f"⚠️ Meting search failed: {e}, fallback to library")
        return {"defaultQuery": q, "results": db.get_all_songs()}


# ============================================================
# API 端点 — 播放状态（暂用模拟数据）
# ============================================================
@app.get("/api/player/state")
async def get_player_state():
    last = db.get_setting("last_song_id", "")
    song = db.get_song_by_id(last) if last else None
    initial = 0.0
    try:
        initial = float(db.get_setting("last_position", "0"))
    except (ValueError, TypeError):
        initial = 0.0
    return {
        "lastSong": song,
        "lastPosition": initial,
        "initialProgress": initial,
        "initialVolume": 0.75
    }


class SavePlayerStateRequest(BaseModel):
    songId: str = ""
    position: float = 0


@app.post("/api/player/last")
async def save_player_last(req: SavePlayerStateRequest):
    db.set_setting("last_song_id", req.songId)
    db.set_setting("last_position", str(req.position))
    return {"success": True}


# ============================================================
# API 端点 — 收藏
# ============================================================
@app.get("/api/favorites")
async def get_favorites():
    songs = db.get_liked_songs()
    return {
        "totalLabel": f"{len(songs)}首",
        "items": songs
    }


class FavoriteToggleRequest(BaseModel):
    songId: str
    name: str = ""
    artist: str = ""
    coverGradient: Optional[List[str]] = None
    picId: str = ""


@app.post("/api/favorites/toggle")
async def toggle_favorite(req: FavoriteToggleRequest):
    # 如果歌曲不在库中，先创建一条最小记录
    existing = db.get_song_by_id(req.songId)
    if not existing:
        import json
        db.add_song({
            "id": req.songId,
            "name": req.name or req.songId,
            "artist": req.artist or "",
            "coverGradient": req.coverGradient or ["#7C3AED", "#22C55E"],
            "_pic_id": req.picId,
        })

    new_liked = db.toggle_liked(req.songId)
    return {"success": True, "songId": req.songId, "liked": new_liked}


# ============================================================
# API 端点 — 歌单
# ============================================================
@app.get("/api/playlists")
async def get_playlists():
    items = db.get_all_playlists()
    return {"items": items}


@app.get("/api/playlists/{playlist_id}")
async def get_playlist_detail(playlist_id: str):
    playlists = db.get_all_playlists()
    pl = next((p for p in playlists if p["id"] == playlist_id), None)
    if not pl:
        return {"detail": "Playlist not found"}
    songs = db.get_playlist_songs(playlist_id)
    pl["songs"] = songs
    return pl


class CreatePlaylistRequest(BaseModel):
    name: str = Field(description="歌单名称")


@app.post("/api/playlists")
async def create_playlist(req: CreatePlaylistRequest):
    pl = db.add_playlist(req.name)
    return {"success": True, "playlist": pl}


@app.delete("/api/playlists/{playlist_id}")
async def delete_playlist(playlist_id: str):
    db.delete_playlist(playlist_id)
    return {"success": True}


class RenamePlaylistRequest(BaseModel):
    name: str


@app.put("/api/playlists/{playlist_id}")
async def rename_playlist(playlist_id: str, req: RenamePlaylistRequest):
    db.rename_playlist(playlist_id, req.name)
    return {"success": True}


class AddSongToPlaylistRequest(BaseModel):
    songId: str
    songName: str = ""
    songArtist: str = ""


@app.post("/api/playlists/{playlist_id}/songs")
async def add_song_to_playlist(playlist_id: str, req: AddSongToPlaylistRequest):
    """将歌曲加入指定歌单，同时确保歌曲已入库"""
    # 确保歌曲在库中
    existing = db.get_song_by_id(req.songId)
    if not existing:
        db.add_song({
            "id": req.songId,
            "name": req.songName or req.songId,
            "artist": req.songArtist or "",
        })
    ok = db.add_song_to_playlist(playlist_id, req.songId)
    return {"success": ok, "already_added": not ok}


@app.delete("/api/playlists/{playlist_id}/songs/{song_id}")
async def remove_song_from_playlist(playlist_id: str, song_id: str):
    db.remove_song_from_playlist(playlist_id, song_id)
    return {"success": True}


# ============================================================
# API 端点 — 歌词（暂用模拟数据，真实优先）
# ============================================================
class ReorderSongsRequest(BaseModel):
    songIds: list[str]

@app.put("/api/playlists/{playlist_id}/reorder")
async def reorder_playlist_songs(playlist_id: str, req: ReorderSongsRequest):
    db.reorder_playlist_songs(playlist_id, req.songIds)
    return {"success": True}


@app.get("/api/lyrics")
async def get_lyrics(songId: str = Query(default="s1")):
    if songId.isdigit():
        try:
            lyric_data = await meting_get_lyric(songId)
            lyric_text = lyric_data.get("lyric", "")
            lines = []
            for line in lyric_text.split("\n"):
                line = line.strip()
                if not line.startswith("[") or "]" not in line:
                    continue
                parts = line.split("]", 1)
                ts_str = parts[0][1:]  # remove '['
                text = parts[1] if len(parts) > 1 else ""
                if not text:
                    continue
                # 解析时间戳 [mm:ss.xx] 转为秒数
                try:
                    parts_ts = ts_str.split(":")
                    minutes = float(parts_ts[0])
                    seconds = float(parts_ts[1])
                    time_sec = minutes * 60 + seconds
                except (ValueError, IndexError):
                    time_sec = 0
                lines.append({"text": text, "state": "future", "time": time_sec})
            if lines:
                return {"songName": "", "artist": "", "lines": lines}
        except Exception as e:
            print(f"⚠️ Meting lyric failed: {e}, fallback to mock")
    return MOCK_DATA["lyrics"]


# ============================================================
# API 端点 — 下载
# ============================================================
class DownloadRequest(BaseModel):
    song_id: str = Field(description="Meting 歌曲 ID")
    source: str = Field(default="netease")
    name: str = Field(default="")
    artist: str = Field(default="")
    album: str = Field(default="")
    pic_id: str = Field(default="")


@app.post("/api/download")
async def download_song(req: DownloadRequest):
    try:
        url_info = await get_url_with_fallback(req.song_id, sources=[req.source], bitrate=320)
        audio_url = url_info.get("url")
        if not audio_url:
            return {"success": False, "error": "No audio URL returned from Meting"}

        safe_name = "".join(c for c in (req.name or req.song_id) if c not in '\\/:*?"<>|')
        safe_artist = "".join(c for c in (req.artist or "unknown") if c not in '\\/:*?"<>|')
        filename = f"{safe_name} - {safe_artist}.mp3"
        file_path = MUSIC_DIR / filename

        # 避免重复下载
        if file_path.exists():
            db.add_song({
                "id": req.song_id, "name": req.name, "artist": req.artist,
                "album": req.album, "filePath": str(file_path),
                "source": url_info.get("source", req.source),
                "externalId": req.song_id, "_pic_id": req.pic_id,
            })
            return {
                "success": True, "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "source": url_info.get("source", req.source),
                "bitrate": url_info.get("br", 0), "cached": True
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", audio_url) as response:
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        file_size = file_path.stat().st_size

        # 下载封面图（缓存到本地）
        pic_id = req.pic_id
        if pic_id:
            cover_path = COVER_DIR / f"{pic_id}.jpg"
            if not cover_path.exists():
                try:
                    proxy_url = f"{METING_BASE_URL}/pic_proxy?id={pic_id}&source={req.source}&size=500"
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        cresp = await client.get(proxy_url)
                        if cresp.status_code == 200 and len(cresp.content) > 100:
                            cover_path.write_bytes(cresp.content)
                        else:
                            pic_id = ""  # 封面无效，清空
                except Exception:
                    pic_id = ""
            # Last.fm fallback
            if not pic_id and req.artist and req.name:
                try:
                    LASTFM_KEY = "1a9a3e5ba4a5a4c3c3e44b6a8a98f2a2"
                    lfm_url = (
                        "https://ws.audioscrobbler.com/2.0/"
                        "?method=track.getInfo&api_key=" + LASTFM_KEY +
                        "&artist=" + req.artist + "&track=" + req.name + "&format=json"
                    )
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        lfm = await client.get(lfm_url)
                        lfm.raise_for_status()
                        data = lfm.json()
                        track = data.get("track") or {}
                        album = track.get("album") or {}
                        images = album.get("image") or []
                        cover_url = None
                        for img in images:
                            if img.get("#text"):
                                cover_url = img["#text"]
                        if cover_url:
                            c_resp = await client.get(cover_url)
                            if c_resp.status_code == 200 and len(c_resp.content) > 100:
                                cover_path.write_bytes(c_resp.content)
                                pic_id = pic_id or req.pic_id  # 使用原pic_id作为缓存键
                except Exception as e:
                    print(f"⚠️ Cover fallback failed: {e}")

        # 下载成功后自动入库
        db.add_song({
            "id": req.song_id,
            "name": req.name,
            "artist": req.artist,
            "album": req.album,
            "filePath": str(file_path),
            "source": url_info.get("source", req.source),
            "externalId": req.song_id,
            "_pic_id": req.pic_id,
        })

        # 写入 ID3 标签
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
            audio = MP3(file_path, ID3=ID3)
            if not audio.tags:
                audio.tags = ID3()
            audio.tags.add(TIT2(encoding=3, text=req.name))
            audio.tags.add(TPE1(encoding=3, text=req.artist))
            if req.album:
                audio.tags.add(TALB(encoding=3, text=req.album))
            pic_file = COVER_DIR / f"{req.pic_id}.jpg"
            if req.pic_id and pic_file.exists():
                audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=pic_file.read_bytes()))
            audio.save()
        except Exception as e:
            print(f"⚠️ ID3 write failed: {e}")

        return {
            "success": True,
            "file_path": str(file_path),
            "file_size": file_size,
            "source": url_info.get("source", req.source),
            "bitrate": url_info.get("br", 0)
        }
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# 封面服务：本地缓存 + Meting 拉取
# ============================================================
@app.get("/api/cover/{song_id}")
async def get_cover(
    song_id: str,
    source: str = Query(default="netease"),
    artist: str = Query(default=""),
    name: str = Query(default=""),
):
    """获取歌曲封面图，本地优先 → Meting → Last.fm"""
    cover_path = COVER_DIR / f"{song_id}.jpg"

    if cover_path.exists():
        return FileResponse(cover_path, media_type="image/jpeg")

    # 尝试从 DB 获取歌曲信息
    song_info = db.get_song_by_id(song_id)
    artist_name = artist or (song_info.get("artist", "") if song_info else "")
    song_name = name or (song_info.get("name", "") if song_info else "")

    try:
        proxy_url = f"{METING_BASE_URL}/pic_proxy?id={song_id}&source={source}&size=500"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(proxy_url)
            resp.raise_for_status()
            cover_path.write_bytes(resp.content)
        return FileResponse(cover_path, media_type="image/jpeg")
    except Exception as e:
        print(f"⚠️ Meting cover failed for {song_id}: {e}")

    # Fallback: Last.fm
    if artist_name and song_name:
        LASTFM_KEY = "1a9a3e5ba4a5a4c3c3e44b6a8a98f2a2"
        try:
            lfm_url = (
                "https://ws.audioscrobbler.com/2.0/"
                "?method=track.getInfo"
                "&api_key=" + LASTFM_KEY +
                "&artist=" + artist_name +
                "&track=" + song_name +
                "&format=json"
            )
            async with httpx.AsyncClient(timeout=10.0) as client:
                lfm = await client.get(lfm_url)
                lfm.raise_for_status()
                data = lfm.json()
                track = data.get("track") or {}
                album = track.get("album") or {}
                images = album.get("image") or []
                cover_url = None
                for img in images:
                    if img.get("#text"):
                        cover_url = img["#text"]
                if cover_url:
                    c_resp = await client.get(cover_url)
                    c_resp.raise_for_status()
                    cover_path.write_bytes(c_resp.content)
                    return FileResponse(cover_path, media_type="image/jpeg")
        except Exception as e2:
            print(f"⚠️ Last.fm cover also failed: {e2}")

    return Response(
        content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIEND\xaeB`\x82',
        media_type="image/png",
        status_code=200
    )


# ============================================================
# 本地文件导入
# ============================================================
@app.post("/api/import/file")
async def import_file(file: UploadFile = File(...)):
    """上传本地 MP3 文件到音乐库，自动提取 ID3 元数据和封面"""
    if not file.filename:
        return {"success": False, "error": "No file"}
    safe_name = file.filename.replace("\\", "/").split("/")[-1]
    dest = MUSIC_DIR / safe_name
    counter = 1
    ext = Path(safe_name).suffix or ".mp3"
    while dest.exists():
        stem = Path(safe_name).stem
        dest = MUSIC_DIR / f"{stem}_{counter}{ext}"
        counter += 1
    content = await file.read()
    dest.write_bytes(content)

    # 解析文件名
    name = Path(safe_name).stem
    artist = ""
    song_name = name
    album = ""
    pic_id = ""
    if " - " in name:
        parts = name.split(" - ", 1)
        a = parts[0].strip()
        b = parts[1].strip()
        has_cn = lambda s: any('\u4e00' <= c <= '\u9fff' for c in s)
        # 含中文 → "歌手 - 歌名"；纯英文 → "歌名 - 歌手"
        if has_cn(a) or not has_cn(b):
            artist, song_name = a, b
        else:
            song_name, artist = a, b
    if " - " in artist:
        artist = artist.split(" - ")[0].strip()

    # 尝试从 ID3/FLAC 标签提取元数据
    try:
        from mutagen import File as MutagenFile
        COVER_DIR.mkdir(parents=True, exist_ok=True)
        audio = MutagenFile(dest)
        if audio and audio.tags:
            print(f"  Tags found: {list(audio.tags.keys())[:8]}")
            tags = audio.tags
            artist = str(tags.get("artist", [artist])[0]) if "artist" in tags else artist
            song_name = str(tags.get("title", [song_name])[0]) if "title" in tags else song_name
            album = str(tags.get("album", [album])[0]) if "album" in tags else album
            # 提取封面图
            if hasattr(audio, 'pictures') and audio.pictures:
                apic = audio.pictures[0]
                cover_filename = f"{safe_name}_cover.jpg".replace("/","_").replace("\\","_")
                cover_path = COVER_DIR / cover_filename
                cover_path.write_bytes(apic.data)
                pic_id = cover_path.stem
                print(f"  Cover saved: {cover_path} ({len(apic.data)} bytes)")
            elif "APIC:" in str(list(tags.keys())):
                # MP3 ID3 APIC
                from mutagen.id3 import APIC
                for k in tags:
                    if k.startswith("APIC"):
                        apic = tags[k]
                        cover_filename = f"{safe_name}_cover.jpg".replace("/","_").replace("\\","_")
                        cover_path = COVER_DIR / cover_filename
                        cover_path.write_bytes(apic.data)
                        pic_id = cover_path.stem
                        print(f"  Cover saved from ID3: {cover_path}")
                        break
        else:
            print(f"  No tags found for {dest}")
    except Exception as e:
        import traceback
        print(f"⚠️ Tag parse failed for {safe_name}: {e}")
        traceback.print_exc()

    song_id = name
    db.add_song({
        "id": song_id,
        "name": song_name,
        "artist": artist,
        "album": album,
        "filePath": str(dest),
        "picId": pic_id,
    })
    song = db.get_song_by_id(song_id)
    return {"success": True, "song": song, "file": str(dest)}


# ============================================================
if __name__ == "__main__":
    print("🎵 MelodyHub 后端服务启动中...")
    print("👉 打开浏览器访问：http://127.0.0.1:8000")
    print(f"📁 下载目录：{MUSIC_DIR}")
    print(f"💾 数据库：{db.DB_PATH}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
