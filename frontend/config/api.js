/**
 * API 配置文件
 * 
 * 开发环境: 使用本地后端
 * 生产环境: 使用你的服务器地址
 * 
 * 请将 API_BASE_URL 替换为你的后端服务器地址
 */

const API_CONFIG = {
  // 开发环境 (localhost)
  dev: {
    BASE_URL: 'http://localhost:8000',
    WS_URL: 'ws://localhost:8000'
  },
  
  // 生产环境 - 请替换为你的服务器地址
  prod: {
    // ⚠️ 重要: 替换为你部署后端服务器的地址
    // 例如: 'https://api.yourdomain.com' 或 'http://your-server-ip:8000'
    BASE_URL: 'https://your-backend-server.com',
    WS_URL: 'wss://your-backend-server.com'
  },
  
  // 获取当前环境的配置
  getConfig() {
    // 检测是否在 Vercel 生产环境
    if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return this.prod;
    }
    return this.dev;
  },
  
  // API 端点
  endpoints: {
    upload: '/api/upload',
    analyze: '/api/analyze/',
    status: '/api/status/',
    result: '/api/result/',
    websocket: '/ws/'
  },
  
  // 获取完整的 API URL
  getUrl(endpoint) {
    const config = this.getConfig();
    return config.BASE_URL + endpoint;
  },
  
  // 获取 WebSocket URL
  getWsUrl(endpoint) {
    const config = this.getConfig();
    return config.WS_URL + endpoint;
  }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API_CONFIG;
}
