/**
 * ============================================
 * utils.js - 工具函数
 * 包含：Toast、Modal、Storage、通用工具
 * ============================================
 */

// ========== Toast ==========
let toastTimer;

function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.classList.remove('show');
  }, 2200);
}

// ========== Modal ==========
function showModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
  }
}

// 通用点击遮罩关闭
document.addEventListener('click', function(e) {
  const modals = ['modal-upgrade', 'modal-custom-phrase', 'modal-vib-test'];
  modals.forEach(id => {
    const m = document.getElementById(id);
    if (m && e.target === m) {
      closeModal(id);
    }
  });
});

// ========== Storage ==========
const Storage = {
  // 获取数据
  get(key, defaultValue = null) {
    try {
      const value = localStorage.getItem(key);
      return value ? JSON.parse(value) : defaultValue;
    } catch (e) {
      console.error('Storage get error:', e);
      return defaultValue;
    }
  },

  // 设置数据
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.error('Storage set error:', e);
      return false;
    }
  },

  // 删除数据
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      console.error('Storage remove error:', e);
      return false;
    }
  },

  // 清空数据
  clear() {
    try {
      localStorage.clear();
      return true;
    } catch (e) {
      console.error('Storage clear error:', e);
      return false;
    }
  }
};

// ========== Copy to Clipboard ==========
async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    return true;
  } catch (e) {
    console.error('Copy failed:', e);
    return false;
  }
}

// ========== HTML Escape ==========
function escapeHtml(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/[&<>]/g, function(m) {
    if (m === '&') return '&amp;';
    if (m === '<') return '&lt;';
    if (m === '>') return '&gt;';
    return m;
  });
}

// ========== Debounce ==========
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ========== Throttle ==========
function throttle(func, limit) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// ========== Format Date ==========
function formatDate(date, format = 'YYYY-MM-DD') {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

// ========== Random ==========
function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// ========== 震动 API ==========
const Vibrate = {
  // 震动反馈
  trigger(pattern, label) {
    const overlay = document.getElementById('vibration-overlay');
    if (!overlay) return;
    
    const vibLabel = document.getElementById('vib-label');
    if (vibLabel) {
      vibLabel.textContent = label + ' 震动中...';
    }
    
    overlay.classList.add('show');
    
    if (navigator.vibrate) {
      navigator.vibrate([200, 100, 200]);
    }
    
    setTimeout(() => {
      overlay.classList.remove('show');
    }, 1200);
  },

  // 震动模式映射
  patterns: {
    'agree': { name: '同意', pattern: [200] },
    'refuse': { name: '拒绝', pattern: [300, 100, 300] },
    'question': { name: '反问', pattern: [150, 100, 300, 100, 150] },
    'delay': { name: '拖延', pattern: [300, 100, 100, 100] },
    'praise': { name: '夸赞', pattern: [100, 100, 100, 100, 100] },
    'nuke': { name: '放大招', pattern: [400, 100, 200, 100, 400] },
    'escape': { name: '转移话题', pattern: [150, 100, 300, 100] },
    'buy': { name: '争取时间', pattern: [300, 100, 300, 100] }
  },

  // 执行震动
  execute(vibId, label) {
    const pattern = this.patterns[vibId];
    if (pattern) {
      if (navigator.vibrate) {
        navigator.vibrate(pattern.pattern);
      }
      showToast(`📳 ${pattern.name}`);
    }
  }
};

// ========== Completion ==========
function showCompletion(emoji, title, sub) {
  const overlay = document.getElementById('completion-overlay');
  if (!overlay) return;
  
  const emojiEl = document.getElementById('comp-emoji');
  const titleEl = document.getElementById('comp-title');
  const subEl = document.getElementById('comp-sub');
  
  if (emojiEl) emojiEl.textContent = emoji;
  if (titleEl) titleEl.textContent = title;
  if (subEl) subEl.textContent = sub;
  
  overlay.classList.add('show');
}

function closeCompletion() {
  const overlay = document.getElementById('completion-overlay');
  if (overlay) {
    overlay.classList.remove('show');
  }
}

// ========== Export ==========
window.utils = {
  showToast,
  showModal,
  closeModal,
  Storage,
  copyToClipboard,
  escapeHtml,
  debounce,
  throttle,
  formatDate,
  randomInt,
  randomItem,
  Vibrate,
  showCompletion,
  closeCompletion
};
