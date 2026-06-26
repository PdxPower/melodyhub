// ============================================================
//  MelodyHub 后端模拟数据
//  存放需要后端 API 返回的数据 — 歌曲列表、搜索结果、
//  收藏、歌单、歌词、播放状态等
//
//  ⚠️ 后端 API 开发完成后，此文件可删除
//  在 HTML 中设置 USE_MOCK = false 即切换为真实 API
// ============================================================

var MOCK_DATA = {

  // ---- 音乐库歌曲（后端接口：GET /api/library）----
  library: {
    songs: [
      { id: "s1", name: "Faded",         artist: "Alan Walker",  duration: "03:32", durationSec: 212, coverGradient: ["#7C3AED", "#22C55E"], liked: true  },
      { id: "s2", name: "晴天",           artist: "周杰伦",       duration: "04:29", durationSec: 269, coverGradient: ["#3366CC", "#CC3344"], liked: true  },
      { id: "s3", name: "Lemon",          artist: "米津玄师",     duration: "04:16", durationSec: 256, coverGradient: ["#E6801A", "#E63366"], liked: true  },
      { id: "s4", name: "Shape of You",   artist: "Ed Sheeran",   duration: "03:54", durationSec: 234, coverGradient: ["#4D8C50", "#1A4D99"], liked: true  }
    ]
  },

  // ---- 搜索结果（后端接口：GET /api/search?q=Faded）----
  search: {
    defaultQuery: "Faded",
    results: [
      { id: "r1", name: "Faded",               artist: "Alan Walker", duration: "03:32", coverGradient: ["#7C3AED", "#22C55E"], liked: false },
      { id: "r2", name: "Faded (Restrung)",     artist: "Alan Walker", duration: "04:12", coverGradient: ["#3366CC", "#CC3344"], liked: true  },
      { id: "r3", name: "Faded (Tiesto Remix)", artist: "Alan Walker", duration: "03:50", coverGradient: ["#E6801A", "#E63366"], liked: false },
      { id: "r4", name: "Faded (Acoustic)",     artist: "Alan Walker", duration: "03:18", coverGradient: ["#4D8C50", "#1A4D99"], liked: true  }
    ]
  },

  // ---- 播放状态（后端接口：GET /api/player/state）----
  player: {
    currentSongId: "s1",
    initialProgress: 0.40,
    initialVolume: 0.55
  },

  // ---- 收藏列表（后端接口：GET /api/favorites）----
  favorites: {
    totalLabel: "12首",
    items: [
      { id: "s1", songId: "s1", name: "Faded",         artist: "Alan Walker", duration: "03:32", coverGradient: ["#7C3AED", "#22C55E"] },
      { id: "s2", songId: "s2", name: "晴天",           artist: "周杰伦",       duration: "04:29", coverGradient: ["#3366CC", "#CC3344"] },
      { id: "s3", songId: "s3", name: "Lemon",          artist: "米津玄师",     duration: "04:16", coverGradient: ["#E6801A", "#E63366"] },
      { id: "s4", songId: "s4", name: "Shape of You",   artist: "Ed Sheeran",   duration: "03:54", coverGradient: ["#4D8C50", "#1A4D99"] }
    ]
  },

  // ---- 歌单列表（后端接口：GET /api/playlists）----
  playlists: {
    items: [
      { id: "p1", name: "学习BGM", songCount: 8,  durationLabel: "32分钟", coverGradient: ["#7C3AED", "#22C55E"] },
      { id: "p2", name: "华语经典", songCount: 15, durationLabel: "58分钟", coverGradient: ["#3366CC", "#CC3344"] },
      { id: "p3", name: "欧美流行", songCount: 6,  durationLabel: "24分钟", coverGradient: ["#E6801A", "#E63366"] },
      { id: "p4", name: "日语精选", songCount: 4,  durationLabel: "18分钟", coverGradient: ["#4D8C50", "#1A4D99"] }
    ]
  },

  // ---- 歌单详情（后端接口：GET /api/playlists/{id}）----
  playlistDetail: {
    id: "p1",
    name: "学习BGM",
    songCount: 6,
    durationLabel: "24分钟",
    coverGradient: ["#7C3AED", "#22C55E"],
    songs: [
      { id: "pd1", name: "Faded",         artist: "Alan Walker",         duration: "3:32", coverGradient: ["#7C3AED", "#22C55E"] },
      { id: "pd2", name: "晴天",           artist: "周杰伦",               duration: "4:29", coverGradient: ["#3366CC", "#CC3344"] },
      { id: "pd3", name: "Lemon",          artist: "米津玄师",             duration: "4:16", coverGradient: ["#E6801A", "#E63366"] },
      { id: "pd4", name: "Shape of You",   artist: "Ed Sheeran",           duration: "3:54", coverGradient: ["#4D8C50", "#1A4D99"] },
      { id: "pd5", name: "夜曲",           artist: "周杰伦",               duration: "3:45", coverGradient: ["#334466", "#AA3344"] },
      { id: "pd6", name: "Unravel",        artist: "TK from 凛として時雨", duration: "3:18", coverGradient: ["#663399", "#CC3366"] }
    ]
  },

  // ---- 歌词（后端接口：GET /api/lyrics?songId=s1）----
  lyrics: {
    songName: "Faded",
    artist: "Alan Walker",
    lines: [
      { text: "You were the shadow to my light",  state: "past"    },
      { text: "Did you feel us",                   state: "past"    },
      { text: "Another star, you fade away",        state: "past"    },
      { text: "Afraid our aim is out of sight",    state: "future" },
      { text: "Where are you now",                  state: "active" },
      { text: "Was it all in my fantasy",           state: "future" },
      { text: "Where are you now",                  state: "future" },
      { text: "Were you only imaginary",            state: "future" },
      { text: "Atlantis, under the sea",            state: "future" }
    ]
  }
};
