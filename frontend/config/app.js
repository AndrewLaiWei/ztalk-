/**
 * 嘴替 ZTalk - 全局配置文件
 * 应用配置、API地址、主题设置等
 */

const AppConfig = {
  // 应用信息
  app: {
    name: '嘴替 ZTalk',
    version: '1.0.0',
    slogan: '你语言的边界，就是你生活的边界'
  },

  // 主题颜色 (CodeDesign.ai 风格)
  theme: {
    primary: '#1a202c',
    primaryLight: '#2d3748',
    accent: '#10B981',
    accent2: '#EF4444',
    success: '#10B981',
    bg: '#FFFFFF',
    bg2: '#F8FAFC',
    bg3: '#F1F5F9',
    text: '#1a202c',
    text2: '#64748B',
    text3: '#94A3B8',
    border: '#E2E8F0'
  },

  // API 配置
  api: {
    baseUrl: '/api',
    endpoints: {
      battle: '/api/battle',
      generate: '/api/generate'
    },
    timeout: 10000
  },

  // 功能开关
  features: {
    enableAI: true,
    enableVibration: true,
    enableBattle: true,
    enableVideoAnalysis: true,
    enableSlangTraining: true
  },

  // 数据存储键名
  storage: {
    favorites: 'ztalk_favorites',
    settings: 'ztalk_settings',
    progress: 'ztalk_progress'
  },

  // 限制配置
  limits: {
    freePhrases: 5,
    freeDaily: 10,
    maxVideoSize: 500 * 1024 * 1024 // 500MB
  },

  // 支持的视频域名
  videoDomains: [
    'youtube.com',
    'youtu.be',
    'bilibili.com',
    'b23.tv',
    'v.douyin.com',
    'douyin.com'
  ],

  // 震动模式配置
  vibration: {
    patterns: {
      agree: [200, 100, 200],
      refuse: [300, 100, 300],
      question: [100, 100, 200, 100, 100],
      delay: [200, 100, 100, 100, 100],
      praise: [100, 100, 100, 100, 100],
      nuke: [200, 100, 200, 100, 200]
    }
  }
};

// 震动编码表
const VIBRATION_CODES = [
  {id: 'agree', name: '同意', icon: '✅', pattern: '· ·', emoji: '✅', color: '#10B981'},
  {id: 'refuse', name: '拒绝', icon: '❌', pattern: '— —', emoji: '❌', color: '#EF4444'},
  {id: 'question', name: '反问', icon: '🔄', pattern: '· — ·', emoji: '🔄', color: '#6C3AE8'},
  {id: 'delay', name: '拖延', icon: '⏳', pattern: '— · ·', emoji: '⏳', color: '#F59E0B'},
  {id: 'praise', name: '夸赞', icon: '🌟', pattern: '· · · ·', emoji: '🌟', color: '#8B5CF6'},
  {id: 'nuke', name: '放大招', icon: '💥', pattern: '— · — ·', emoji: '💥', color: '#F97316'},
  {id: 'escape', name: '转移话题', icon: '🌀', pattern: '· — —', emoji: '🌀', color: '#06B6D4'},
  {id: 'buy', name: '争取时间', icon: '🎯', pattern: '— — ·', emoji: '🎯', color: '#EC4899'}
];

// 场景列表
const SCENARIOS = [
  {id: 's1', name: '拒绝酒桌逼酒', emoji: '🍺', desc: '领导劝酒，同事起哄', unlocked: true, badge: null, bg: '#F0FDF4'},
  {id: 's2', name: '亲戚催婚应对', emoji: '💒', desc: '"你都多大了？"', unlocked: true, badge: '🏅', bg: '#EFF6FF'},
  {id: 's3', name: '职场抢功甩锅', emoji: '🎯', desc: '背锅侠逆袭时刻', unlocked: true, badge: null, bg: '#FEF3C7'},
  {id: 's4', name: '拒绝老好人模式', emoji: '😇', desc: '别人的事都找你', unlocked: false, badge: null, bg: '#FDF2F8'},
  {id: 's5', name: '朋友借钱应对', emoji: '💸', desc: '"就当帮个忙嘛"', unlocked: false, badge: null, bg: '#F5F3FF'},
  {id: 's6', name: '文化歧视反击', emoji: '🌍', desc: '遭遇不公平对待', unlocked: false, badge: null, bg: '#ECFDF5'},
  {id: 's7', name: '消费维权实战', emoji: '🛡️', desc: '退款、索赔、投诉', unlocked: false, badge: null, bg: '#FFF7ED'},
  {id: 's8', name: '甲方无理要求', emoji: '😤', desc: '无限改稿、白嫖索赔', unlocked: false, badge: null, bg: '#F0F9FF'}
];

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AppConfig, VIBRATION_CODES, SCENARIOS };
}
