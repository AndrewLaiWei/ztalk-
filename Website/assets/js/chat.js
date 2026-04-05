/**
 * ============================================
 * chat.js - AI 对话逻辑和页面渲染
 * 包含：话术库、实战、洞察、黑话等模块
 * ============================================
 */

// ========== DATA ==========
const VIBRATION_CODES = [
  { id: 'agree', name: '同意', icon: '✅', pattern: '· ·', emoji: '✅', color: '#10B981' },
  { id: 'refuse', name: '拒绝', icon: '❌', pattern: '— —', emoji: '❌', color: '#EF4444' },
  { id: 'question', name: '反问', icon: '🔄', pattern: '· — ·', emoji: '🔄', color: '#6C3AE8' },
  { id: 'delay', name: '拖延', icon: '⏳', pattern: '— · ·', emoji: '⏳', color: '#F59E0B' },
  { id: 'praise', name: '夸赞', icon: '🌟', pattern: '· · · ·', emoji: '🌟', color: '#8B5CF6' },
  { id: 'nuke', name: '放大招', icon: '💥', pattern: '— · — ·', emoji: '💥', color: '#F97316' },
  { id: 'escape', name: '转移话题', icon: '🌀', pattern: '· — —', emoji: '🌀', color: '#06B6D4' },
  { id: 'buy', name: '争取时间', icon: '🎯', pattern: '— — ·', emoji: '🎯', color: '#EC4899' }
];

const PHRASES = [
  { id: 1, scene: '职场', type: '拒绝', text: '这个需求不在原始范围内，我们需要重新评估工期和资源。', vib: 'refuse' },
  { id: 2, scene: '职场', type: '拖延', text: '这个我需要再确认一下，明天给你回复可以吗？', vib: 'delay' },
  { id: 3, scene: '职场', type: '反问', text: '你觉得这件事的优先级和上周说的那个相比，哪个更重要？', vib: 'question' },
  { id: 4, scene: '职场', type: '放大招', text: '我理解你的想法，但这样做会违反公司的XXX规定，建议我们走正式流程。', vib: 'nuke' },
  { id: 5, scene: '职场', type: '拒绝', text: '抱歉，我今天的排期已经满了，我们看看能不能找人协助？', vib: 'refuse' },
  { id: 6, scene: '职场', type: '争取时间', text: '这个问题很好，让我想一秒钟。', vib: 'buy' },
  { id: 7, scene: '职场', type: '转移话题', text: '先把眼前的这个处理完，我们再讨论后续的方向？', vib: 'escape' },
  { id: 8, scene: '职场', type: '夸赞', text: '你这个角度我没想到，确实是个好思路。', vib: 'praise' },
  { id: 9, scene: '职场', type: '拒绝', text: '这不是我职责范围内的工作，建议同步给XX来负责。', vib: 'refuse' },
  { id: 10, scene: '职场', type: '反问', text: '你希望这件事最终达成什么结果？', vib: 'question' },
  { id: 11, scene: '职场', type: '同意', text: '没问题，我来推进，有进展及时同步给你。', vib: 'agree' },
  { id: 12, scene: '职场', type: '放大招', text: '我先把目前遇到的问题整理一下，发邮件对齐，避免后续扯皮。', vib: 'nuke' },
  { id: 13, scene: '恋爱', type: '反问', text: '你希望我怎么做才会让你觉得被重视？', vib: 'question' },
  { id: 14, scene: '恋爱', type: '拖延', text: '这个话题比较重要，我们找个好好说话的时间聊好吗？', vib: 'delay' },
  { id: 15, scene: '恋爱', type: '转移话题', text: '我知道你现在情绪不太好，要不要先去吃点东西？', vib: 'escape' },
  { id: 16, scene: '恋爱', type: '夸赞', text: '你今天做这件事真的让我觉得你很厉害。', vib: 'praise' },
  { id: 17, scene: '恋爱', type: '放大招', text: '我觉得我们需要认真谈谈，因为这个问题已经影响到了我们。', vib: 'nuke' },
  { id: 18, scene: '恋爱', type: '拒绝', text: '这件事我没办法答应你，但我可以告诉你我的顾虑。', vib: 'refuse' },
  { id: 19, scene: '家庭', type: '拖延', text: '这件事我了解了，让我考虑一下，咱们周末再聊？', vib: 'delay' },
  { id: 20, scene: '家庭', type: '拒绝', text: '爸妈，我理解你们的好意，但这件事我需要自己做决定。', vib: 'refuse' },
  { id: 21, scene: '家庭', type: '反问', text: '你觉得这样做对我来说是最好的选择吗？', vib: 'question' },
  { id: 22, scene: '家庭', type: '放大招', text: '我现在的状态很好，如果一直催促我反而会有压力，能不能给我一些空间？', vib: 'nuke' },
  { id: 23, scene: '家庭', type: '转移话题', text: '先吃饭，饭后我们再聊这个，好吗？', vib: 'escape' },
  { id: 24, scene: '社交', type: '拒绝', text: '那天我有安排，下次吧！', vib: 'refuse' },
  { id: 25, scene: '社交', type: '争取时间', text: '我看一下我的日程，稍后告诉你。', vib: 'buy' },
  { id: 26, scene: '社交', type: '转移话题', text: '哎说到这个，你最近那件事怎么样了？', vib: 'escape' },
  { id: 27, scene: '社交', type: '夸赞', text: '你真的很懂这个，改天详细跟我讲讲？', vib: 'praise' },
  { id: 28, scene: '社交', type: '拒绝', text: '这种事我一般不参与的，但你们玩得开心！', vib: 'refuse' },
  { id: 29, scene: '消费维权', type: '放大招', text: '我已经对此次事件进行了全程记录，如果协商无果我会向消费者协会投诉。', vib: 'nuke' },
  { id: 30, scene: '消费维权', type: '反问', text: '请问这个问题是否在你们的服务承诺范围内？', vib: 'question' },
  { id: 31, scene: '消费维权', type: '拖延', text: '好的，请你们出具书面处理方案，我收到后再决定是否接受。', vib: 'delay' },
  { id: 32, scene: '消费维权', type: '争取时间', text: '我需要咨询一下，稍后给你回复。', vib: 'buy' },
  { id: 33, scene: '日常', type: '拒绝', text: '不好意思，我今天不太方便。', vib: 'refuse' },
  { id: 34, scene: '日常', type: '转移话题', text: '说到这里让我想起另一件事……', vib: 'escape' },
  { id: 35, scene: '日常', type: '夸赞', text: '你这个主意太妙了！', vib: 'praise' },
  { id: 36, scene: '日常', type: '同意', text: '行，就这么定了。', vib: 'agree' }
];

const SCENARIOS = [
  { id: 's1', name: '拒绝酒桌逼酒', emoji: '🍺', desc: '领导劝酒，同事起哄', unlocked: true, badge: null, bg: '#F0FDF4' },
  { id: 's2', name: '亲戚催婚应对', emoji: '💒', desc: '"你都多大了？"', unlocked: true, badge: '🏅', bg: '#EFF6FF' },
  { id: 's3', name: '职场抢功甩锅', emoji: '🎯', desc: '背锅侠逆袭时刻', unlocked: true, badge: null, bg: '#FEF3C7' },
  { id: 's4', name: '拒绝老好人模式', emoji: '😇', desc: '别人的事都找你', unlocked: false, badge: null, bg: '#FDF2F8' },
  { id: 's5', name: '朋友借钱应对', emoji: '💸', desc: '"就当帮个忙嘛"', unlocked: false, badge: null, bg: '#F5F3FF' },
  { id: 's6', name: '文化歧视反击', emoji: '🌍', desc: '遭遇不公平对待', unlocked: false, badge: null, bg: '#ECFDF5' },
  { id: 's7', name: '消费维权实战', emoji: '🛡️', desc: '退款、索赔、投诉', unlocked: false, badge: null, bg: '#FFF7ED' },
  { id: 's8', name: '甲方无理要求', emoji: '😤', desc: '无限改稿、白嫖索赔', unlocked: false, badge: null, bg: '#F0F9FF' }
];

const BADGES = [
  { id: 'b1', emoji: '🎯', name: '首战告捷', unlocked: true },
  { id: 'b2', emoji: '🍺', name: '酒桌英雄', unlocked: true },
  { id: 'b3', emoji: '👑', name: '职场王者', unlocked: false },
  { id: 'b4', emoji: '💒', name: '催婚免疫', unlocked: true },
  { id: 'b5', emoji: '🛡️', name: '维权老手', unlocked: false },
  { id: 'b6', emoji: '🔥', name: '7日毕业', unlocked: false },
  { id: 'b7', emoji: '💥', name: '放大招达人', unlocked: true },
  { id: 'b8', emoji: '🤐', name: '沉默是金', unlocked: true }
];

const SLANG_DATA = [
  { id: 's1', word: '赋能', category: '职场', trans: 'Empower / Enablement', plain: '给下属或团队提供资源和权力，让他们干得更爽', example: '老板用法', exampleText: '"我给你们赋能，你们放手去干"', translation: '= "活儿你们干，锅我甩"' },
  { id: 's2', word: '拉齐', category: '职场', trans: 'Align / Sync', plain: '让所有人的认知和信息保持一致', example: '老板用法', exampleText: '"我们先拉齐一下认知"', translation: '= "我要重新讲一遍确保你们别搞错"' },
  { id: 's3', word: '对齐颗粒度', category: '职场', trans: 'Get aligned on details', plain: '把讨论的细节级别统一一下', example: '老板用法', exampleText: '"我们先对齐一下颗粒度"', translation: '= "你说的太粗了，给我细说"' },
  { id: 's4', word: '闭环', category: '职场', trans: 'Close the loop', plain: '从开始到结束完整做一件事并确认结果', example: '老板用法', exampleText: '"这个需求要形成闭环"', translation: '= "你得干完还要汇报，别干一半跑了"' },
  { id: 's5', word: '抓手', category: '职场', trans: 'Leverage point / Handle', plain: '做事的关键切入点或着力点', example: '老板用法', exampleText: '"找到业务的抓手"', translation: '= "找个能突破的关键点"' },
  { id: 's6', word: '打透', category: '职场', trans: 'Drill down / Penetrate', plain: '把事情做深入、做透彻', example: '老板用法', exampleText: '"这个点要打透"', translation: '= "别蜻蜓点水，给我往深里搞"' },
  { id: 's7', word: '你是个好人', category: '恋爱', trans: 'You are a nice guy', plain: '经典的拒绝方式，意思是"我们不合适"', example: '女生用法', exampleText: '"你是个好人，但我们不合适"', translation: '= "我不想伤害你但真的没感觉"' },
  { id: 's8', word: '想静静', category: '恋爱', trans: 'Need space', plain: '需要独处的时间，可能是在考虑关系', example: '对方用法', exampleText: '"我最近想静静"', translation: '= "我需要时间想清楚我们的关系"' },
  { id: 's9', word: '我们还是做朋友吧', category: '恋爱', trans: "Let's just be friends", plain: '委婉拒绝进一步发展的方式', example: '对方用法', exampleText: '"我们还是做朋友吧"', translation: '= "我不想伤害你但我不会和你在一起"' },
  { id: 's10', word: '我干了，你随意', category: '酒桌', trans: 'Cheers - I finish mine', plain: '表示豪爽，把选择权给对方', example: '领导用法', exampleText: '"来来来，我干了，你随意！"', translation: '= "我喝了这么多，你好意思不干？"' },
  { id: 's11', word: '感情深一口闷', category: '酒桌', trans: 'Deep feelings = bottoms up', plain: '用感情绑架逼人干杯', example: '领导用法', exampleText: '"感情深一口闷！"', translation: '= "不干就是不给面子"' },
  { id: 's12', word: '都在酒里', category: '酒桌', trans: "It's all in the drink", plain: '一切尽在不言中，用酒表达', example: '对方用法', exampleText: '"都在酒里了"', translation: '= "我啥也不说了，都在酒里了"' },
  { id: 's13', word: '风口', category: '金融', trans: 'Trend / Opportunity', plain: '某个行业或领域的快速成长期', example: '投资人用法', exampleText: '"这是下一个风口"', translation: '= "这个赛道正在高速增长"' },
  { id: 's14', word: '赛道', category: '金融', trans: 'Industry / Sector', plain: '某个特定的商业领域', example: '投资人用法', exampleText: '"这个赛道很有潜力"', translation: '= "这个行业/领域值得关注"' },
  { id: 's15', word: '底层逻辑', category: '金融', trans: 'Fundamental logic', plain: '最根本的商业本质和规律', example: '大佬用法', exampleText: '"要理解这件事的底层逻辑"', translation: '= "搞清楚本质再说话"' },
  { id: 's16', word: '内卷', category: '网络', trans: 'Involution / Rat race', plain: '在资源有限的情况下过度竞争', example: '网友用法', exampleText: '"996是内卷"', translation: '= "大家都在拼命但整体没进步"' },
  { id: 's17', word: '躺平', category: '网络', trans: 'Lie flat / Check out', plain: '放弃过度竞争，选择低欲望生活', example: '网友用法', exampleText: '"我选择躺平"', translation: '= "不卷了，活着就行"' },
  { id: 's18', word: '社死', category: '网络', trans: 'Social death', plain: '社会性死亡，丢脸到没脸见人', example: '网友用法', exampleText: '"这波操作导致社死"', translation: '= "丢人丢到没脸见人"' },
  { id: 's19', word: '绝绝子', category: '网络', trans: 'Amazing / Awesome', plain: '表示非常厉害、非常好', example: '网友用法', exampleText: '"这个操作绝绝子"', translation: '= "太牛了！"' }
];

const insightCourses = [
  { id: 1, level: '初级', title: '👁️ 肢体语言 · 一眼看穿对方底牌', desc: '从站姿、手势、手臂交叉到脚尖朝向，学习最直观的非语言信号。', videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ', points: ['手臂交叉 → 防御或紧张', '身体前倾 → 兴趣或攻击', '脚尖朝向 → 真实关注方向', '模仿动作 → 共情信号'], quiz: { q: '对方说话时频繁摸鼻子，通常表示？', options: ['过敏', '撒谎/紧张', '思考', '鼻子痒'], answer: '撒谎/紧张' } },
  { id: 2, level: '初级', title: '😲 微表情 · 0.2秒的真实情绪', desc: '面部肌肉的瞬间抽搐——愤怒、恐惧、轻蔑无所遁形。', videoUrl: 'https://www.youtube.com/embed/sT_5Uo6Gj7E', points: ['单侧耸肩 → 怀疑', '嘴角单侧上提 → 轻蔑', '眼睑收紧 → 愤怒', '假笑只有嘴动'], quiz: { q: '真正的微笑与假笑的最大区别？', options: ['露牙齿', '眼睛周围皱纹', '持续时间', '嘴巴形状'], answer: '眼睛周围皱纹' } },
  { id: 3, level: '中级', title: '🎙️ 语调分析 · 声音里的魔鬼', desc: '音高、语速、停顿、重音——对方每句话都藏着情绪密码。', videoUrl: 'https://www.youtube.com/embed/4JkIsZsL2sI', points: ['语速突然加快 → 焦虑', '音调升高 → 激动或撒谎', '停顿延长 → 编造内容', '音量变小 → 不自信'], quiz: { q: '谈判中对方突然压低音量且语速变慢，最可能？', options: ['困了', '故作镇定/施加压力', '感冒', '无所谓'], answer: '故作镇定/施加压力' } },
  { id: 4, level: '中级', title: '💬 沟通风格 · DISC与色彩人格', desc: '识别支配型、影响型、稳健型、谨慎型，针对性反击。', videoUrl: 'https://www.youtube.com/embed/p0gU8iX6j6Y', points: ['D型(支配)：直接打断，用事实怼', 'I型(影响)：热情但跑题，拉回主线', 'S型(稳健)：回避冲突，鼓励表达', 'C型(谨慎)：摆数据，逻辑碾压'], quiz: { q: '同事总爱说"我觉得""可能吧"，属于哪种风格？', options: ['D支配型', 'C谨慎型', 'S稳健型', 'I影响型'], answer: 'S稳健型' } },
  { id: 5, level: '高级', title: '🏠 环境分析 · 空间与物品暴露本性', desc: '办公桌、车内装饰、家庭照片——环境是性格的延伸。', videoUrl: 'https://www.youtube.com/embed/z9Uz1icjwrM', points: ['杂乱桌面 → 创造力高但条理性差', '家庭照片 → 重视归属感', '奖杯证书 → 需要认可', '极端整洁 → 控制欲强'], quiz: { q: '对方办公室挂满团队合照和个人奖牌，说明？', options: ['炫耀', '重视成就和认可', '热爱工作', '强迫症'], answer: '重视成就和认可' } },
  { id: 6, level: '高级', title: '👔 外表分析 · 衣着配饰透露社会信号', desc: '发型、手表、鞋、纹身——外在符号背后的阶层与价值观。', videoUrl: 'https://www.youtube.com/embed/7X8Y9Z0A1B2', points: ['定制西装 → 追求细节与权力', '运动手表 → 实用主义', '夸张首饰 → 渴望关注', '纹身位置 → 叛逆或纪念'], quiz: { q: '商务场合对方戴金戒指配玉扳指，暗示？', options: ['传统权威/财富展示', '时尚', '宗教信仰', '随便戴'], answer: '传统权威/财富展示' } }
];

const QUIZ_QUESTIONS = [
  { pattern: '· ·', answer: '同意', options: ['同意', '拒绝', '放大招', '转移话题'] },
  { pattern: '— —', answer: '拒绝', options: ['同意', '拒绝', '争取时间', '夸赞'] },
  { pattern: '· — ·', answer: '反问', options: ['反问', '拖延', '拒绝', '放大招'] },
  { pattern: '— · ·', answer: '拖延', options: ['同意', '夸赞', '拖延', '反问'] },
  { pattern: '· · · ·', answer: '夸赞', options: ['放大招', '夸赞', '争取时间', '同意'] }
];

// ========== STATE ==========
let currentScene = '职场';
let currentType = 'all';
let favorites = new Set([1, 4, 7]);
let currentBattleId = null;
let battlePhase = 0;
let quizIndex = 0;
let currentSlangCat = 'all';
let slangSearchQuery = '';
let currentTrainingMode = 'create';

// ========== INIT ==========
function startApp() {
  renderPhrases();
  renderVibrationCodes();
  renderScenarios();
  renderBadgeWall();
  renderFavorites();
  renderVibTypeSelect();
  renderVibTestList();
  renderInsight();
  renderSlangList();
  renderDailySlang();
  setupDragDrop();
}

// ========== TAB NAVIGATION ==========
function switchTab(tab) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
  
  const page = document.getElementById('page-' + tab);
  const tabBtn = document.getElementById('tab-' + tab);
  
  if (page) page.classList.add('active');
  if (tabBtn) tabBtn.classList.add('active');
  
  // Tab-specific renders
  if (tab === 'favorites') renderFavorites();
  if (tab === 'insight') {
    renderInsight();
    setTimeout(attachQuizEvents, 120);
  }
  if (tab === 'battle') {
    document.getElementById('scenario-list-view').style.display = 'flex';
    document.getElementById('battle-view').style.display = 'none';
  }
  if (tab === 'slang') {
    renderSlangList();
    renderDailySlang();
  }
  if (tab === 'phrases') renderPhraseList();
  if (tab === 'profile') renderProfile();
}

// ========== PHRASES ==========
function getPhrases() {
  let list = PHRASES.filter(p => {
    const sceneMatch = p.scene === currentScene;
    const typeMatch = currentType === 'all' || p.type === currentType;
    return sceneMatch && typeMatch;
  });
  
  const q = document.getElementById('phrase-search')?.value?.trim() || '';
  if (q) {
    list = PHRASES.filter(p => p.text.includes(q));
  }
  
  return list;
}

function renderPhraseList() {
  const container = document.getElementById('phrase-list-container');
  if (!container) return;
  
  const list = getPhrases();
  
  if (!list.length) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">暂无相关话术</div></div>';
    return;
  }
  
  const vib = Object.fromEntries(VIBRATION_CODES.map(v => [v.id, v]));
  
  container.innerHTML = list.map(p => {
    const v = vib[p.vib] || {};
    const faved = favorites.has(p.id);
    
    return `<div class="phrase-item" onclick="copyAndVibrate(${p.id})">
      <div class="vibration-dot" style="border-color:${v.color || 'var(--primary)'};color:${v.color || 'var(--primary-light)'};">${v.emoji || '•'}</div>
      <div style="flex:1;min-width:0;">
        <div class="phrase-text">${p.text}</div>
        <div class="phrase-meta">
          <span class="badge badge-purple">${p.type}</span>
          <span style="margin-left:6px;font-size:11px;color:var(--text3);">${v.pattern || ''}</span>
        </div>
      </div>
      <div class="phrase-actions">
        <button class="action-btn ${faved ? 'favorited' : ''}" onclick="event.stopPropagation();toggleFavorite(${p.id})">${faved ? '❤️' : '🤍'}</button>
        <button class="action-btn" onclick="event.stopPropagation();triggerVibrate('${p.vib}')">📳</button>
      </div>
    </div>`;
  }).join('');
  
  // Update stats
  const statTotal = document.getElementById('stat-total');
  if (statTotal) {
    statTotal.textContent = PHRASES.filter(p => p.scene === currentScene).length;
  }
}

// Alias for compatibility
const renderPhrases = renderPhraseList;

function filterScene(el) {
  document.querySelectorAll('#scene-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  currentScene = el.dataset.scene;
  renderPhraseList();
}

function filterType(el) {
  document.querySelectorAll('#type-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  currentType = el.dataset.type;
  renderPhraseList();
}

function searchPhrases() {
  renderPhraseList();
}

function copyAndVibrate(id) {
  const phrase = PHRASES.find(p => p.id === id);
  if (!phrase) return;
  
  copyToClipboard(phrase.text);
  triggerVibrate(phrase.vib, phrase.text);
}

function toggleFavorite(id) {
  if (favorites.has(id)) {
    favorites.delete(id);
    showToast('已取消收藏');
  } else {
    favorites.add(id);
    showToast('已加入收藏 ❤️');
  }
  renderPhraseList();
  renderFavorites();
}

// ========== FAVORITES ==========
function renderFavorites() {
  const container = document.getElementById('favorites-container');
  if (!container) return;
  
  const list = PHRASES.filter(p => favorites.has(p.id));
  
  if (!list.length) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">🤍</div><div class="empty-text">还没有收藏</div><div class="empty-sub">在话术库中点击 🤍 收藏</div></div>';
    return;
  }
  
  const vib = Object.fromEntries(VIBRATION_CODES.map(v => [v.id, v]));
  
  container.innerHTML = '<div style="padding-bottom:8px;">' + list.map(p => {
    const v = vib[p.vib] || {};
    return `<div class="phrase-item" onclick="copyAndVibrate(${p.id})">
      <div class="vibration-dot" style="border-color:${v.color || 'var(--primary)'};color:${v.color || 'var(--primary-light)'};">${v.emoji || '•'}</div>
      <div style="flex:1;min-width:0;">
        <div class="phrase-text">${p.text}</div>
        <div class="phrase-meta">
          <span class="badge badge-purple">${p.type}</span>
          <span class="badge badge-amber" style="margin-left:4px;">${p.scene}</span>
        </div>
      </div>
      <div class="phrase-actions">
        <button class="action-btn" onclick="event.stopPropagation();triggerVibrate('${p.vib}')">📳</button>
        <button class="action-btn favorited" onclick="event.stopPropagation();toggleFavorite(${p.id})">❤️</button>
      </div>
    </div>`;
  }).join('') + '</div>';
}

// ========== VIBRATION ==========
function renderVibrationCodes() {
  const grid = document.getElementById('vib-code-grid');
  if (!grid) return;
  
  grid.innerHTML = VIBRATION_CODES.map(v => `
    <div class="vibration-code-item" onclick="triggerVibrate('${v.id}','${v.name}')">
      <div class="vib-code-icon" style="background:${v.color}22;color:${v.color};">${v.emoji}</div>
      <div class="vib-code-info">
        <div class="vib-code-name">${v.name}</div>
        <div class="vib-code-pattern" style="color:${v.color};">${v.pattern}</div>
      </div>
    </div>
  `).join('');
}

function triggerVibrate(vibId, label) {
  const v = VIBRATION_CODES.find(c => c.id === vibId);
  Vibrate.trigger(vibId, v ? v.name : label);
}

// ========== QUIZ ==========
function startQuiz() {
  quizIndex = 0;
  const container = document.getElementById('quiz-container');
  if (container) container.style.display = 'block';
  renderQuizQuestion();
}

function endQuiz() {
  const container = document.getElementById('quiz-container');
  if (container) container.style.display = 'none';
  showToast('训练已结束，今日得分：80分 🎉');
}

function renderQuizQuestion() {
  const q = QUIZ_QUESTIONS[quizIndex];
  if (!q) return;
  
  const qNumEl = document.getElementById('q-num');
  const vibEl = document.getElementById('quiz-vibrate');
  const optsEl = document.getElementById('quiz-options');
  
  if (qNumEl) qNumEl.textContent = quizIndex + 1;
  if (vibEl) vibEl.textContent = q.pattern;
  
  if (optsEl) {
    const opts = [...q.options].sort(() => Math.random() - .5);
    optsEl.innerHTML = opts.map(o => `
      <div class="quiz-option" onclick="checkQuizAnswer(this,'${o}','${q.answer}')">
        <span>${o}</span>
      </div>
    `).join('');
  }
}

function checkQuizAnswer(el, chosen, answer) {
  const opts = document.querySelectorAll('.quiz-option');
  opts.forEach(o => o.onclick = null);
  
  if (chosen === answer) {
    el.classList.add('correct');
    el.innerHTML = '<span>✅ ' + chosen + ' — 正确！</span>';
    showToast('正确！🎉 ');
  } else {
    el.classList.add('wrong');
    opts.forEach(o => {
      if (o.querySelector('span').textContent === answer) o.classList.add('correct');
    });
    showToast('不对哦，正确答案是：' + answer);
  }
  
  setTimeout(() => {
    quizIndex++;
    if (quizIndex < QUIZ_QUESTIONS.length) {
      renderQuizQuestion();
    } else {
      const container = document.getElementById('quiz-container');
      if (container) container.style.display = 'none';
      showCompletion('🎓', '训练完成！', '今日训练得分：100分\n你已掌握所有震动编码！');
    }
  }, 1200);
}

function showVibrationTest() {
  document.getElementById('modal-vib-test').classList.add('show');
}

function renderVibTestList() {
  const list = document.getElementById('vib-test-list');
  if (!list) return;
  
  list.innerHTML = VIBRATION_CODES.map(v => `
    <div class="vibration-code-item" onclick="triggerVibrate('${v.id}','${v.name}');this.style.borderColor='${v.color}';">
      <div class="vib-code-icon" style="background:${v.color}22;color:${v.color};">${v.emoji}</div>
      <div class="vib-code-info">
        <div class="vib-code-name">${v.name}</div>
        <div class="vib-code-pattern" style="color:${v.color};">${v.pattern}</div>
      </div>
      <span style="color:var(--text3);font-size:12px;">点击测试</span>
    </div>
  `).join('');
}

// ========== SCENARIOS ==========
function renderScenarios() {
  const grid = document.getElementById('scenario-grid');
  if (!grid) return;
  
  const bgColors = ['#F0FDF4', '#EFF6FF', '#FEF3C7', '#FDF2F8', '#F5F3FF', '#ECFDF5', '#FFF7ED', '#F0F9FF'];
  
  grid.innerHTML = SCENARIOS.map((s, i) => `
    <div class="scenario-card" onclick="openScenario('${s.id}')">
      <div class="scenario-thumb" style="background:linear-gradient(135deg,${bgColors[i % bgColors.length]},#fff);">
        <span>${s.emoji}</span>
        ${!s.unlocked ? '<div class="scenario-lock">🔒</div>' : ''}
        ${s.badge ? `<div class="scenario-badge">${s.badge}</div>` : ''}
      </div>
      <div class="scenario-info">
        <div class="scenario-name">${s.name}</div>
        <div class="scenario-desc">${s.desc}</div>
      </div>
    </div>
  `).join('');
}

// Scene 映射：前端ID -> 后端场景名
const sceneMap = { 's1': 'wine', 's2': 'marry', 's3': 'work', 's4': 'rent', 's5': 'interview', 's6': 'client' };

async function openScenario(id) {
  const s = SCENARIOS.find(x => x.id === id);
  if (!s) return;
  
  if (!s.unlocked) {
    showUpgrade();
    return;
  }
  
  window.currentBattleSceneId = id;
  window.currentBattleMessages = [];
  window.currentBattleWaiting = false;
  
  // 获取AI初始台词
  const firstOpponentLine = s.name === '拒绝酒桌逼酒'
    ? '来来来，今天必须喝！不喝就是看不起我！大家说对不对？'
    : s.name === '亲戚催婚应对'
    ? '你都多大了？再不找对象就晚了！你看你表哥，孩子都上学了！'
    : s.name === '职场抢功甩锅'
    ? '这个项目成功，主要是因为我提出了核心方案，对吧小张？'
    : '对方突然向你发难...';
  
  document.getElementById('scenario-list-view').style.display = 'none';
  const bv = document.getElementById('battle-view');
  bv.style.display = 'flex';
  bv.innerHTML = `
    <div class="battle-header">
      <button class="header-btn" onclick="closeBattle()">←</button>
      <div style="flex:1;font-size:14px;font-weight:700;color:var(--text);">${s.name}</div>
      <div class="battle-phase phase-lose" id="phase-badge">⚔️ 对战进行中</div>
    </div>
    <div style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;" id="battle-chat">
      <div class="chat-bubble-wrap">
        <div class="chat-role">🤖 AI 对手</div>
        <div class="chat-bubble opponent">${firstOpponentLine}</div>
      </div>
    </div>
    <div style="padding:16px;border-top:1px solid var(--border);background:var(--bg2);">
      <div style="display:flex;gap:8px;">
        <input type="text" id="battle-user-input" placeholder="输入你的回应..." autocomplete="off" style="flex:1;background:var(--bg3);border:1px solid var(--border);border-radius:40px;padding:12px 16px;color:var(--text);outline:none;">
        <button class="btn btn-primary" id="battle-send-btn">发送</button>
      </div>
    </div>
  `;
  
  document.getElementById('battle-send-btn').onclick = () => sendBattleMessage();
  document.getElementById('battle-user-input').onkeypress = (e) => { if (e.key === 'Enter') sendBattleMessage(); };
}

async function sendBattleMessage() {
  if (window.currentBattleWaiting) { showToast('请等待AI回应...'); return; }
  
  const inputEl = document.getElementById('battle-user-input');
  const userText = inputEl.value.trim();
  if (!userText) return;
  
  inputEl.value = '';
  window.currentBattleWaiting = true;
  
  const chatDiv = document.getElementById('battle-chat');
  
  chatDiv.innerHTML += `
    <div class="chat-bubble-wrap" style="display:flex;flex-direction:column;align-items:flex-end;">
      <div class="chat-role" style="justify-content:flex-end;">你 👤</div>
      <div class="chat-bubble user-fail" style="background:rgba(239,68,68,.15);">${escapeHtml(userText)}</div>
    </div>
  `;
  chatDiv.scrollTop = chatDiv.scrollHeight;
  
  // 前端模拟评估
  const teachingPhrases = {
    's1': ['领导，感谢您的盛情，今天我开车，安全第一！我用茶代酒敬您一杯！', '我有点身体不适，医生嘱咐不能喝酒，但情谊我记在心里！'],
    's2': ['谢谢您关心，我现在事业正在关键期，等稳定了自然会考虑的！', '感情的事急不来，我相信缘分！'],
    's3': ['是啊，大家都出力了！我记得我负责了XXX模块，方案文档都在的！', '这个项目大家都很努力！各有分工，缺一不可！']
  };
  
  const isGoodResponse = userText.length > 10 && !['好', '行', '嗯', '哦', '啊'].includes(userText);
  
  if (!isGoodResponse) {
    const phrases = teachingPhrases[window.currentBattleSceneId] || ['请换一种更有力的回应方式！'];
    chatDiv.innerHTML += `
      <div class="chat-bubble-wrap">
        <div class="chat-bubble teach" style="background:rgba(245,158,11,.1);border-left:3px solid var(--accent);">
          <strong>💡 你输了，学学这些话术：</strong><br><br>
          • ${phrases[0]}<br><br>
          • ${phrases[1]}<br><br>
          <button class="btn btn-sm btn-primary" style="margin-top:8px;" onclick="retryBattle()">再试一次</button>
        </div>
      </div>
    `;
  } else {
    const nextLines = {
      's1': ['好好好，算你有理！那喝一杯意思意思？', '行吧行吧，你小子还挺有原则！'],
      's2': ['事业重要，但感情也不能耽误啊！', '缘分这东西，谁知道呢...'],
      's3': ['哦？那你说说你的贡献在哪里？', '行，那就让大家评评理！']
    };
    const lines = nextLines[window.currentBattleSceneId] || ['继续说...'];
    const nextOpponentLine = lines[Math.floor(Math.random() * lines.length)];
    
    chatDiv.innerHTML += `
      <div class="chat-bubble-wrap">
        <div class="chat-role">🤖 AI 对手</div>
        <div class="chat-bubble opponent">${escapeHtml(nextOpponentLine)}</div>
      </div>
    `;
    window.currentBattleMessages.push({ role: 'user', text: userText });
    window.currentBattleMessages.push({ role: 'opponent', text: nextOpponentLine });
  }
  
  window.currentBattleWaiting = false;
  chatDiv.scrollTop = chatDiv.scrollHeight;
}

function retryBattle() {
  showToast('请换一种更有力的回应方式！');
}

function closeBattle() {
  document.getElementById('scenario-list-view').style.display = 'flex';
  document.getElementById('battle-view').style.display = 'none';
  renderScenarios();
  window.currentBattleSceneId = null;
  window.currentBattleMessages = [];
}

// ========== PROFILE ==========
function renderBadgeWall() {
  const wall = document.getElementById('badge-wall');
  if (!wall) return;
  
  wall.innerHTML = BADGES.map(b => `
    <div class="badge-item ${b.unlocked ? '' : 'locked'}">
      <div class="badge-emoji">${b.emoji}</div>
      <div class="badge-name">${b.name}</div>
    </div>
  `).join('');
}

function renderProfile() {
  renderBadgeWall();
}

// ========== CUSTOM PHRASE ==========
function renderVibTypeSelect() {
  const container = document.getElementById('vib-type-select');
  if (!container) return;
  
  container.innerHTML = VIBRATION_CODES.map(v => `
    <div class="chip" data-vib="${v.id}" onclick="selectVibType(this)" style="border-color:${v.color}33;">
      ${v.emoji} ${v.name}
    </div>
  `).join('');
}

function selectVibType(el) {
  document.querySelectorAll('#vib-type-select .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
}

function saveCustomPhrase() {
  const text = document.getElementById('custom-phrase-text').value.trim();
  if (!text) {
    showToast('请输入话术内容！');
    return;
  }
  
  const scene = document.getElementById('custom-scene').value || '日常';
  const vibEl = document.querySelector('#vib-type-select .chip.active');
  const vibId = vibEl ? vibEl.dataset.vib : 'agree';
  const vibName = vibEl ? vibEl.textContent.trim().split(' ')[1] : '同意';
  
  const newId = Math.max(...PHRASES.map(p => p.id)) + 1;
  PHRASES.push({ id: newId, scene, type: vibName, text, vib: vibId });
  
  closeModal('modal-custom-phrase');
  showToast('✅ 话术已保存！');
  
  if (currentScene === scene) renderPhraseList();
}

// ========== MODALS ==========
function showUpgrade() {
  document.getElementById('modal-upgrade').classList.add('show');
}

function showCustomPhraseModal() {
  document.getElementById('modal-custom-phrase').classList.add('show');
}

function buyPlan(plan) {
  closeModal('modal-upgrade');
  if (plan === 'lifetime') {
    showCompletion('🎉', '终身会员开通成功！', '你将获得一枚"嘴替"实体贴纸\n（快递费到付，预计3-5天发货）');
  } else {
    showToast('月度会员开通成功！¥9.9/月 🚀');
  }
}

// ========== INSIGHT ==========
let insightRendered = false;
const insightAnswered = new Set();

function renderInsight() {
  const inner = document.getElementById('insight-inner');
  if (!inner) return;
  
  const levelColor = { '初级': '#10B981', '中级': '#F59E0B', '高级': '#EF4444' };
  
  let html = `
    <div style="background:var(--card);border-radius:12px;padding:14px;margin-bottom:18px;border:1px solid var(--border);">
      <div style="font-weight:700;font-size:14px;color:var(--text);margin-bottom:8px;">📈 学习曲线</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
        ${insightCourses.map(c => `<span class="badge" style="background:rgba(16,185,129,.1);color:#10B981;">${c.level} ${c.title.split('·')[0].trim()}</span>`).join('')}
      </div>
      <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:0%" id="insight-progress-bar"></div></div>
      <div class="text-center" style="font-size:12px;color:var(--text3);margin-top:6px;">完成所有课程解锁「分析大师」徽章 🧠</div>
    </div>
  `;
  
  insightCourses.forEach((course, idx) => {
    const lc = levelColor[course.level] || '#10B981';
    html += `
      <div class="insight-course" data-course-id="${course.id}">
        <div class="course-header">
          <span class="course-level" style="background:${lc}15;color:${lc};">${course.level}</span>
          <span style="font-size:11px;color:var(--text3);">🎓 实战案例</span>
        </div>
        <div class="course-title">${course.title}</div>
        <div class="course-desc">${course.desc}</div>
        <div class="video-placeholder" onclick="insightPlayVideo(this,'${course.videoUrl}')">
          <span>▶️ 点击播放视频教学</span>
        </div>
        <div class="course-points">
          ${course.points.map(p => `<div class="point-item">📌 ${p}</div>`).join('')}
        </div>
        <button class="btn btn-outline quiz-btn" onclick="toggleInsightQuiz(${idx})">📝 课后测验</button>
        <div class="quiz-panel" id="iquiz-${idx}" style="display:none;">
          <div class="quiz-question" style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:10px;">${course.quiz.q}</div>
          <div id="iquiz-opts-${idx}">
            ${course.quiz.options.map(opt => `
              <div class="quiz-option" data-opt="${opt}" data-correct="${course.quiz.answer}" data-idx="${idx}" onclick="handleInsightQuiz(this)">${opt}</div>
            `).join('')}
          </div>
          <div class="quiz-feedback" id="iquiz-fb-${idx}"></div>
        </div>
      </div>
    `;
  });
  
  html += `
    <div class="card" style="margin-top:4px;">
      <div class="card-inner">
        <div class="section-title">🤖 AI实时分析模拟器（Beta）</div>
        <div style="font-size:13px;color:var(--text2);margin-bottom:10px;line-height:1.6;">粘贴对话内容，AI将分析对方的情绪和人格特质。</div>
        <textarea id="insight-text" class="input-field" rows="3" placeholder="粘贴对话内容..."></textarea>
        <button class="btn btn-primary btn-full" style="margin-top:10px;" onclick="runInsightAnalysis()">🔍 AI 人格分析</button>
        <div id="insight-result" style="margin-top:12px;font-size:13px;display:flex;flex-direction:column;gap:6px;"></div>
      </div>
    </div>
    <div style="height:16px;"></div>
  `;
  
  inner.innerHTML = html;
  insightRendered = true;
}

window.insightPlayVideo = function(el, url) {
  el.innerHTML = `<iframe src="${url}?autoplay=1&modestbranding=1&rel=0" allow="autoplay;encrypted-media" allowfullscreen style="width:100%;height:100%;border:none;border-radius:10px;"></iframe>`;
  el.style.padding = '0';
};

window.toggleInsightQuiz = function(idx) {
  const panel = document.getElementById(`iquiz-${idx}`);
  if (!panel) return;
  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'block' : 'none';
};

window.handleInsightQuiz = function(el) {
  const selected = el.dataset.opt;
  const correct = el.dataset.correct;
  const idx = el.dataset.idx;
  const fbDiv = document.getElementById(`iquiz-fb-${idx}`);
  
  el.parentElement.querySelectorAll('.quiz-option').forEach(o => {
    o.style.pointerEvents = 'none';
    if (o.dataset.opt === correct) o.classList.add('correct');
  });
  
  if (selected === correct) {
    el.classList.add('correct');
    fbDiv.innerHTML = '<span style="color:var(--success);">✅ 正确！你已掌握这个知识点。</span>';
    showToast('🎉 答对了！继续下一个课程');
    updateInsightProgress();
  } else {
    el.classList.add('wrong');
    fbDiv.innerHTML = `<span style="color:var(--accent2);">❌ 错误。正确答案是：${correct}。再看一遍课程吧。</span>`;
    showToast('❌ 答错了，再学一遍');
  }
};

function updateInsightProgress() {
  insightAnswered.add(1);
  const pct = Math.round((insightAnswered.size / insightCourses.length) * 100);
  const bar = document.getElementById('insight-progress-bar');
  if (bar) bar.style.width = pct + '%';
  
  if (insightAnswered.size === insightCourses.length) {
    setTimeout(() => showCompletion('🧠', '人格分析大师！', '你已完成全部6门洞察课程\n解锁「分析大师」专属徽章！'), 400);
  }
}

window.runInsightAnalysis = function() {
  const text = document.getElementById('insight-text')?.value?.trim();
  if (!text) { showToast('请先输入对话内容'); return; }
  
  const result = document.getElementById('insight-result');
  result.innerHTML = `<div class="point-item" style="color:var(--text3);">⏳ AI分析中...</div>`;
  showToast('🤖 分析中...');
  
  const profiles = [
    { type: 'D支配型', icon: '🔴', hint: '语气强势、直接打断，建议用数据和结果回应。' },
    { type: 'S稳健型', icon: '🟢', hint: '措辞保守、回避冲突，建议鼓励其表达顾虑。' },
    { type: 'C谨慎型', icon: '🔵', hint: '逻辑缜密、细节导向，建议提供详细数据支撑。' },
    { type: 'I影响型', icon: '🟡', hint: '热情活跃、容易跑题，建议适时拉回主线。' }
  ];
  
  const picked = profiles[Math.floor(Math.random() * profiles.length)];
  
  setTimeout(() => {
    result.innerHTML = `
      <div class="point-item">🧠 <strong>初步人格判断：${picked.icon} ${picked.type}</strong></div>
      <div class="point-item">💡 应对建议：${picked.hint}</div>
      <div class="point-item">📊 情绪状态：检测到轻微防御倾向，建议保持开放式提问。</div>
      <div class="point-item">🎯 推荐话术：「你刚才提到的那点，能再具体说明一下吗？」</div>
    `;
  }, 900);
};

function attachQuizEvents() {}

// ========== VIDEO TAB ==========
function setupDragDrop() {
  const zone = document.getElementById('upload-zone');
  if (!zone) return;
  
  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('dragover');
  });
  
  zone.addEventListener('dragleave', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
  });
  
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && (files[0].type.startsWith('video/') || files[0].name.match(/\.(mp4|mov)$/i))) {
      handleVideoFile(files[0]);
    }
  });
}

function handleFileUpload(input) {
  if (input.files && input.files[0]) handleVideoFile(input.files[0]);
}

function handleVideoFile(file) {
  if (file.size > 500 * 1024 * 1024) {
    showToast('文件超过500MB限制！');
    return;
  }
  showToast('视频上传成功，正在分析... 📹');
  document.getElementById('video-analysis-result').style.display = 'block';
}

function handleLinkUpload() {
  const link = document.getElementById('video-link').value.trim();
  const btn = document.getElementById('parse-btn');
  if (!link) { showToast('请输入链接'); return; }
  
  const supportedDomains = ['youtube.com', 'youtu.be', 'bilibili.com', 'b23.tv', 'v.douyin.com', 'douyin.com'];
  const isSupported = supportedDomains.some(d => link.includes(d));
  
  if (isSupported) {
    btn.textContent = '解析中...';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    showToast('链接解析成功，正在下载视频... 🔗');
    
    setTimeout(() => {
      document.getElementById('video-analysis-result').style.display = 'block';
      btn.textContent = '解析';
      btn.disabled = false;
      btn.style.opacity = '1';
      showToast('视频分析完成！📊');
    }, 1500);
  } else {
    showToast('暂不支持该链接，请粘贴正确的链接');
  }
}

function frameBack() { showToast('后退一帧 ⏮️'); }
function frameForward() { showToast('前进一帧 ⏭️'); }
function togglePlay() { showToast('播放/暂停 ▶️'); }

function jumpToTime(time) {
  document.getElementById('time-display').textContent = time + ' / 03:45';
  showToast('跳转到 ' + time + ' ⏱️');
}

function copyComeback(btn) {
  const text = btn.closest('.comeback-card').querySelector('.comeback-text').textContent;
  copyToClipboard(text);
}

function saveToPractice() {
  showToast('已存到实战练习 💾');
  switchTab('battle');
}

// ========== SLANG TAB ==========
function renderSlangList() {
  const container = document.getElementById('slang-list-container');
  if (!container) return;
  
  let list = SLANG_DATA.filter(s => {
    const catMatch = currentSlangCat === 'all' || s.category === currentSlangCat;
    const searchMatch = !slangSearchQuery || s.word.includes(slangSearchQuery) || s.trans.toLowerCase().includes(slangSearchQuery.toLowerCase()) || s.plain.includes(slangSearchQuery);
    return catMatch && searchMatch;
  });
  
  if (!list.length) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">暂无相关黑话</div></div>';
    return;
  }
  
  container.innerHTML = list.map(s => `
    <div class="slang-item" id="slang-${s.id}" onclick="toggleSlangItem('${s.id}')">
      <div class="slang-main">
        <div class="slang-word">${s.word}</div>
        <div class="slang-trans">${s.trans}</div>
        <div class="slang-expand-icon">▼</div>
      </div>
      <div class="slang-detail">
        <div class="slang-plain">${s.plain}</div>
        <div class="slang-example">
          <div class="slang-example-label">${s.example}</div>
          <div class="slang-example-text">${s.exampleText}</div>
          <div class="slang-example-translation">大白话：${s.translation}</div>
        </div>
        <button class="btn btn-outline btn-sm slang-add-btn" onclick="event.stopPropagation();addToTraining('${s.word}')">➕ 加入训练</button>
      </div>
    </div>
  `).join('');
}

function toggleSlangItem(id) {
  const item = document.getElementById('slang-' + id);
  item.classList.toggle('expanded');
}

function filterSlangCat(el) {
  document.querySelectorAll('#slang-categories .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  currentSlangCat = el.dataset.cat;
  renderSlangList();
}

function searchSlang(q) {
  slangSearchQuery = q;
  renderSlangList();
}

function renderDailySlang() {
  const daily = SLANG_DATA[Math.floor(Math.random() * SLANG_DATA.length)];
  const wordEl = document.getElementById('daily-word');
  const transEl = document.getElementById('daily-trans');
  const exampleEl = document.getElementById('daily-example');
  
  if (wordEl) wordEl.textContent = daily.word;
  if (transEl) transEl.textContent = daily.trans;
  if (exampleEl) exampleEl.textContent = '"' + daily.exampleText.replace(/"/g, '') + '"';
}

function switchTrainingMode(el) {
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  currentTrainingMode = el.dataset.mode;
  
  const createMode = document.getElementById('training-mode-create');
  const transMode = document.getElementById('training-mode-translate');
  
  if (createMode) createMode.style.display = currentTrainingMode === 'create' ? 'block' : 'none';
  if (transMode) transMode.style.display = currentTrainingMode === 'translate' ? 'block' : 'none';
}

function usePreset(el) {
  const input = document.getElementById('slang-input');
  if (input) input.value = el.textContent;
}

function useTranslatePreset(el) {
  const input = document.getElementById('translate-input');
  if (input) input.value = el.textContent;
}

function addToTraining(word) {
  const input = document.getElementById('slang-input');
  if (input) {
    input.value = `用「${word}」造句：`;
    input.focus();
  }
  showToast(`已选择「${word}」开始训练 💪`);
}

async function getAIScore() {
  const mode = currentTrainingMode;
  const input = mode === 'create' ? document.getElementById('slang-input') : document.getElementById('translate-input');
  const text = input.value.trim();
  
  if (!text) { showToast('请先输入内容'); return; }
  
  const resultDiv = document.getElementById('ai-result');
  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<div class="ai-score"><div class="score-circle">⏳</div><div class="score-detail">AI 评分中...</div></div>';
  
  const dailyWord = document.getElementById('daily-word').innerText;
  const prompt = mode === 'create'
    ? `请评价用户用黑话「${dailyWord}」造的句子，输出格式严格为：分数/10，评语（一句话），更牛逼的例句。用户句子：${text}`
    : `请翻译以下老板黑话为白话，并给出评分（1-10分）和更好的翻译建议。黑话内容：${text}`;
  
  // 模拟AI评分（实际项目中应调用后端API）
  setTimeout(() => {
    const score = Math.floor(Math.random() * 4) + 7; // 7-10分
    const comments = ['不错，用得很地道！', '可以，再练练会更自然', '有点意思，但不够精髓', '满分答案！太牛了'];
    const examples = ['你这波操作确实绝绝子', '老板听了都得服气', '下次可以试试...', '已经很有那味了'];
    
    resultDiv.innerHTML = `
      <div class="ai-score">
        <div class="score-circle">${score}</div>
        <div class="score-detail">
          <div class="score-label">AI 评分</div>
          <div class="score-comment">${comments[score - 7]}</div>
        </div>
      </div>
      <div class="better-example">
        <div class="better-example-label">✨ 更牛逼的示范</div>
        <div class="better-example-text">${examples[score - 7]}</div>
      </div>
    `;
    
    showToast(`得分 ${score}/10`);
    triggerVibrate('agree', '评分完成');
  }, 1000);
}
