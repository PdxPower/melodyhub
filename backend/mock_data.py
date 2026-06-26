# ============================================================
# MelodyHub 后端模拟数据
# 从 test_data.js 的 MOCK_DATA 提取，供后端开发阶段使用
# 暂不使用数据库，所有数据存在内存中
# ============================================================

MOCK_DATA = {

    # ---- 音乐库歌曲（后端接口：GET /api/library）----
    "library": {
        "songs": [
            {"id": "s1", "name": "Faded",         "artist": "Alan Walker",  "duration": "03:32", "durationSec": 212, "coverGradient": ["#7C3AED", "#22C55E"], "liked": True  },
            {"id": "s2", "name": "晴天",           "artist": "周杰伦",       "duration": "04:29", "durationSec": 269, "coverGradient": ["#3366CC", "#CC3344"], "liked": True  },
            {"id": "s3", "name": "Lemon",          "artist": "米津玄师",     "duration": "04:16", "durationSec": 256, "coverGradient": ["#E6801A", "#E63366"], "liked": True  },
            {"id": "s4", "name": "Shape of You",   "artist": "Ed Sheeran",   "duration": "03:54", "durationSec": 234, "coverGradient": ["#4D8C50", "#1A4D99"], "liked": True  }
        ]
    },

    # ---- 搜索结果（后端接口：GET /api/search?q=Faded）----
    "search": {
        "defaultQuery": "Faded",
        "results": [
            {"id": "r1", "name": "Faded",               "artist": "Alan Walker", "duration": "03:32", "coverGradient": ["#7C3AED", "#22C55E"], "liked": False },
            {"id": "r2", "name": "Faded (Restrung)",     "artist": "Alan Walker", "duration": "04:12", "coverGradient": ["#3366CC", "#CC3344"], "liked": True  },
            {"id": "r3", "name": "Faded (Tiesto Remix)", "artist": "Alan Walker", "duration": "03:50", "coverGradient": ["#E6801A", "#E63366"], "liked": False },
            {"id": "r4", "name": "Faded (Acoustic)",     "artist": "Alan Walker", "duration": "03:18", "coverGradient": ["#4D8C50", "#1A4D99"], "liked": True  }
        ]
    },

    # ---- 播放状态（后端接口：GET /api/player/state）----
    "player": {
        "currentSongId": "s1",
        "initialProgress": 0.40,
        "initialVolume": 0.55
    },

    # ---- 收藏列表（后端接口：GET /api/favorites）----
    "favorites": {
        "totalLabel": "12首",
        "items": [
            {"songId": "s1", "name": "Faded",         "artist": "Alan Walker", "duration": "03:32", "coverGradient": ["#7C3AED", "#22C55E"]},
            {"songId": "s2", "name": "晴天",           "artist": "周杰伦",       "duration": "04:29", "coverGradient": ["#3366CC", "#CC3344"]},
            {"songId": "s3", "name": "Lemon",          "artist": "米津玄师",     "duration": "04:16", "coverGradient": ["#E6801A", "#E63366"]},
            {"songId": "s4", "name": "Shape of You",   "artist": "Ed Sheeran",   "duration": "03:54", "coverGradient": ["#4D8C50", "#1A4D99"]}
        ]
    },

    # ---- 歌单列表（后端接口：GET /api/playlists）----
    "playlists": {
        "items": [
            {"id": "p1", "name": "学习BGM", "songCount": 8,  "durationLabel": "32分钟", "coverGradient": ["#7C3AED", "#22C55E"]},
            {"id": "p2", "name": "华语经典", "songCount": 15, "durationLabel": "58分钟", "coverGradient": ["#3366CC", "#CC3344"]},
            {"id": "p3", "name": "欧美流行", "songCount": 6,  "durationLabel": "24分钟", "coverGradient": ["#E6801A", "#E63366"]},
            {"id": "p4", "name": "日语精选", "songCount": 4,  "durationLabel": "18分钟", "coverGradient": ["#4D8C50", "#1A4D99"]}
        ]
    },

    # ---- 歌词（后端接口：GET /api/lyrics?songId=s1）----
    "lyrics": {
        "songName": "Faded",
        "artist": "Alan Walker",
        "lines": [
            {"text": "You were the shadow to my light",  "state": "past"    },
            {"text": "Did you feel us",                   "state": "past"    },
            {"text": "Another star, you fade away",        "state": "past"    },
            {"text": "Afraid our aim is out of sight",    "state": "future" },
            {"text": "Where are you now",                  "state": "active" },
            {"text": "Was it all in my fantasy",           "state": "future" },
            {"text": "Where are you now",                  "state": "future" },
            {"text": "Were you only imaginary",            "state": "future" },
            {"text": "Atlantis, under the sea",            "state": "future" }
        ]
    }
}


# 内存中的收藏状态（无数据库持久化，仅演示状态变更）
LIKED_STATE = {song["id"]: song["liked"] for song in MOCK_DATA["library"]["songs"]}
