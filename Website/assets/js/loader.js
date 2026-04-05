/**
 * ============================================
 * loader.js - 组件加载核心
 * 负责异步加载 HTML 组件和页面区块
 * ============================================
 */

class ComponentLoader {
  constructor(basePath = '') {
    this.basePath = basePath;
    this.cache = new Map();
  }

  /**
   * 异步加载 HTML 文件
   * @param {string} path - 相对路径
   * @returns {Promise<string>} HTML 内容
   */
  async load(path) {
    const fullPath = this.basePath + path;
    
    // 使用缓存
    if (this.cache.has(fullPath)) {
      return this.cache.get(fullPath);
    }

    try {
      const response = await fetch(fullPath);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const html = await response.text();
      this.cache.set(fullPath, html);
      return html;
    } catch (error) {
      console.error(`Failed to load component: ${fullPath}`, error);
      return '';
    }
  }

  /**
   * 将 HTML 加载到指定容器
   * @param {string} containerId - 容器 ID
   * @param {string} path - 组件路径
   */
  async loadInto(containerId, path) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Container not found: ${containerId}`);
      return;
    }
    
    const html = await this.load(path);
    container.innerHTML = html;
    
    // 触发自定义事件，通知组件已加载
    container.dispatchEvent(new CustomEvent('componentLoaded', { 
      bubbles: true,
      detail: { path, containerId }
    }));
  }

  /**
   * 加载多个组件
   * @param {Array} components - [{containerId, path}, ...]
   */
  async loadMultiple(components) {
    const promises = components.map(c => this.loadInto(c.containerId, c.path));
    await Promise.all(promises);
  }

  /**
   * 预加载组件（仅缓存，不插入 DOM）
   * @param {string} path - 组件路径
   */
  async preload(path) {
    await this.load(path);
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * 清除指定路径缓存
   * @param {string} path - 组件路径
   */
  invalidate(path) {
    const fullPath = this.basePath + path;
    this.cache.delete(fullPath);
  }
}

// 创建全局加载器实例
const loader = new ComponentLoader();

// 便捷方法
const loadComponent = (containerId, path) => loader.loadInto(containerId, path);
const loadComponents = (components) => loader.loadMultiple(components);
const preloadComponent = (path) => loader.preload(path);
