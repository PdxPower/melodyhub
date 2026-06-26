// ============================================================
//  MelodyHub 前端配置文件
//  存放应用级静态配置 — 导航结构、UI文案、控件符号等
//  这些数据不依赖后端，后端开发完成后也不需要改动
// ============================================================

var APP_CONFIG = {
  // 应用名
  appName: "MelodyHub",

  // 状态栏时间（仅原型展示用，真实应用会取系统时间）
  statusBarTime: "9:41",

  // 底部导航栏结构
  tabs: [
    { screenIndex: 0, icon: "♫", iconSize: 16, label: "音乐库" },
    { screenIndex: 1, icon: "⌕", iconSize: 20, label: "搜索" },
    { screenIndex: 3, icon: "♥", iconSize: 16, label: "收藏" },
    { screenIndex: 4, icon: "○", iconSize: 18, label: "我的" }
  ],

  // 音乐库页 — 分类标签 & 区段标题
  library: {
    categories: ["全部", "最近添加", "艺术家", "专辑"],
    sectionTitle: "最近播放"
  },

  // 搜索页 — 占位文案 & 平台分类标签
  search: {
    placeholder: "搜索歌曲、艺术家...",
    categories: ["全部", "网易云", "QQ", "酷狗"]
  },

  // 播放页 — 返回标签 & 控件符号
  player: {
    backLabel: "← 音乐库",
    controls: {
      shuffle: "↻",
      prev: "◀",
      next: "▶",
      repeat: "↺"
    }
  },

  // 收藏页 — 标题 & 图标
  favorites: {
    title: "我喜欢",
    heartIcon: "♥"
  },

  // 歌单页 — 标题 & 新建图标
  playlists: {
    title: "我的歌单",
    addIcon: "+"
  },

  // 歌词页 — 返回标签 & 页面标签
  lyrics: {
    backLabel: "← 正在播放",
    pageLabel: "歌词"
  }
};
