# ============================================================
# MelodyHub Meting 适配器
# 通过 HTTP 调用本地 Node.js Meting 服务（@meting/core）
# 端口默认 3000，可通过环境变量 METING_PORT 修改
# ============================================================

import os
import httpx
import asyncio
from typing import Optional, List, Dict, Any

METING_HOST = os.getenv("METING_HOST", "127.0.0.1")
METING_PORT = int(os.getenv("METING_PORT", "3000"))
METING_BASE_URL = f"http://{METING_HOST}:{METING_PORT}"

# 平台优先级：网易云优先，QQ次之
DEFAULT_SOURCES = ["netease", "tencent", "kugou", "kuwo", "baidu"]


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


async def search(keyword: str, source: str = "netease", limit: int = 10) -> List[Dict[str, Any]]:
    """在指定平台搜索歌曲"""
    async with _client() as client:
        resp = await client.get(
            f"{METING_BASE_URL}/search",
            params={"keyword": keyword, "source": source, "limit": limit}
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"Meting search error: {data['error']}")
        return data


async def search_with_fallback(keyword: str, sources: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """多平台搜索，失败自动 fallback"""
    sources = sources or DEFAULT_SOURCES
    last_error = None
    for source in sources:
        try:
            results = await search(keyword, source=source, limit=limit)
            if results:
                # 标记来源平台
                for item in results:
                    item["source"] = source
                return results
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All sources failed for '{keyword}'. Last error: {last_error}")


async def get_url(song_id: str, source: str = "netease", bitrate: int = 320) -> Dict[str, Any]:
    """获取歌曲播放/下载链接"""
    async with _client() as client:
        resp = await client.get(
            f"{METING_BASE_URL}/url",
            params={"id": song_id, "source": source, "bitrate": bitrate}
        )
        resp.raise_for_status()
        return resp.json()


async def get_url_with_fallback(song_id: str, sources: Optional[List[str]] = None, bitrate: int = 320) -> Dict[str, Any]:
    """多平台获取 URL，失败自动 fallback"""
    sources = sources or DEFAULT_SOURCES
    last_error = None
    for source in sources:
        try:
            result = await get_url(song_id, source=source, bitrate=bitrate)
            if result and result.get("url"):
                result["source"] = source
                return result
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All sources failed for URL of {song_id}. Last error: {last_error}")


async def get_lyric(song_id: str, source: str = "netease") -> Dict[str, Any]:
    """获取歌词"""
    async with _client() as client:
        resp = await client.get(
            f"{METING_BASE_URL}/lyric",
            params={"id": song_id, "source": source}
        )
        resp.raise_for_status()
        return resp.json()


async def get_pic(song_id: str, source: str = "netease", size: int = 300) -> Dict[str, Any]:
    """获取封面图"""
    async with _client() as client:
        resp = await client.get(
            f"{METING_BASE_URL}/pic",
            params={"id": song_id, "source": source, "size": size}
        )
        resp.raise_for_status()
        return resp.json()


async def health() -> Dict[str, Any]:
    """检查 Meting 服务健康状态"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{METING_BASE_URL}/health")
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
