/**
 * Lawsker Professional Icon Upgrade System
 * 专业图标升级系统 - 将现有图标替换为Heroicons专业图标
 */

class IconUpgradeSystem {
  constructor() {
    this.iconMappings = {
      // 用户相关图标映射
      '👤': 'user',
      '👥': 'user-group', 
      '👨‍💼': 'user-circle',
      '🧑‍💼': 'briefcase',
      
      // 法律相关图标映射
      '⚖️': 'scale',
      '📄': 'document-text',
      '📋': 'document-text',
      '📝': 'document-text',
      '💼': 'briefcase',
      
      // 金融支付图标映射
      '💳': 'credit-card',
      '💰': 'banknotes',
      '💵': 'currency-dollar',
      '💎': 'currency-dollar',
      
      // 成就游戏化图标映射
      '🏆': 'trophy',
      '⭐': 'star',
      '🌟': 'star-solid',
      '🔥': 'fire',
      '💪': 'trophy',
      
      // 导航UI图标映射
      '🏠': 'home',
      '⚙️': 'cog-6-tooth',
      '🔔': 'bell',
      '📊': 'chart-bar',
      '🛡️': 'shield-check',
      
      // 操作图标映射
      '➕': 'plus',
      '➖': 'minus',
      '❌': 'x-mark',
      '✅': 'check',
      '▶️': 'chevron-right',
      '◀️': 'chevron-left',
      '🔽': 'chevron-down',
      '🔼': 'chevron-up',
      
      // 通讯图标映射
      '📧': 'envelope',
      '📞': 'phone',
      '💬': 'envelope',
      
      // 状态反馈图标映射
      '⚠️': 'exclamation-triangle',
      'ℹ️': 'information-circle',
      '✔️': 'check-circle',
      '❗': 'x-circle',
      
      // 上传文件图标映射
      '☁️': 'cloud-arrow-up',
      '📤': 'document-arrow-up',
      '📁': 'document-text',
      
      // 时间日历图标映射
      '🕐': 'clock',
      '📅': 'calendar-days',
      '⏰': 'clock',
      
      // 可见性图标映射
      '👁️': 'eye',
      '🙈': 'eye-slash'
    };
    
    this.contextualMappings = {
      // 根据上下文的智能映射
      'login': 'user-circle',
      'register': 'user-group',
      'profile': 'user',
      'lawyer': 'scale',
      'case': 'document-text',
      'payment': 'credit-card',
      'credits': 'banknotes',
      'level': 'trophy',
      'points': 'star',
      'achievement': 'trophy',
      'notification': 'bell',
      'settings': 'cog-6-tooth',
      'dashboard': 'chart-bar',
      'security': 'shield-check',
      'upload': 'cloud-arrow-up',
      'download': 'document-arrow-up',
      'time': 'clock',
      'calendar': 'calendar-days',
      'email': 'envelope',
      'phone': 'phone',
      'success': 'check-circle',
      'error': 'x-circle',
      'warning': 'exclamation-triangle',
      'info': 'information-circle'
    };
    
    this.upgradedElements = new Set();
  }

  /**
   * 初始化图标升级系统
   */
  init() {
    console.log('🎨 启动专业图标升级系统...');
    
    // 等待DOM加载完成
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.performUpgrade());
    } else {
      this.performUpgrade();
    }
    
    // 监听动态内容变化
    this.observeChanges();
  }

  /**
   * 执行图标升级
   */
  performUpgrade() {
    console.log('🔄 开始执行图标升级...');
    
    // 1. 升级emoji图标
    this.upgradeEmojiIcons();
    
    // 2. 升级基于类名的图标
    this.upgradeClassBasedIcons();
    
    // 3. 升级基于data属性的图标
    this.upgradeDataAttributeIcons();
    
    // 4. 升级文本内容中的图标
    this.upgradeTextIcons();
    
    // 5. 添加专业图标样式
    this.applyProfessionalStyles();
    
    console.log(`✅ 图标升级完成，共升级 ${this.upgradedElements.size} 个图标`);
  }

  /**
   * 升级emoji图标
   */
  upgradeEmojiIcons() {
    const textNodes = this.getTextNodes(document.body);
    
    textNodes.forEach(node => {
      let text = node.textContent;
      let hasChanges = false;
      
      // 替换emoji为专业图标
      Object.entries(this.iconMappings).forEach(([emoji, iconName]) => {
        if (text.includes(emoji)) {
          const iconHtml = window.IconSystem.getIcon(iconName, {
            size: '20',
            className: 'professional-icon inline-icon'
          });
          
          // 创建包装元素
          const wrapper = document.createElement('span');
          wrapper.innerHTML = text.replace(new RegExp(emoji, 'g'), iconHtml);
          
          // 替换原节点
          node.parentNode.replaceChild(wrapper, node);
          this.upgradedElements.add(wrapper);
          hasChanges = true;
        }
      });
    });
  }

  /**
   * 升级基于类名的图标
   */
  upgradeClassBasedIcons() {
    // 查找可能包含图标的类名
    const iconSelectors = [
      '.icon', '.fa', '.glyphicon', '.material-icons',
      '[class*="icon-"]', '[class*="fa-"]'
    ];
    
    iconSelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        const iconName = this.detectIconFromElement(element);
        if (iconName) {
          this.replaceWithProfessionalIcon(element, iconName);
        }
      });
    });
  }

  /**
   * 升级基于data属性的图标
   */
  upgradeDataAttributeIcons() {
    // 查找data-icon属性
    const elements = document.querySelectorAll('[data-icon]');
    elements.forEach(element => {
      const iconName = element.getAttribute('data-icon');
      if (iconName && window.IconSystem.icons[iconName]) {
        const size = element.getAttribute('data-icon-size') || '24';
        const className = element.getAttribute('data-icon-class') || 'professional-icon';
        
        window.IconSystem.replaceWithIcon(element, iconName, {
          size,
          className: `${className} ${element.className}`.trim()
        });
        
        this.upgradedElements.add(element);
      }
    });
  }

  /**
   * 升级文本内容中的图标
   */
  upgradeTextIcons() {
    // 查找包含图标关键词的元素
    const elements = document.querySelectorAll('button, a, span, div');
    
    elements.forEach(element => {
      const text = element.textContent.toLowerCase().trim();
      
      // 根据上下文映射图标
      Object.entries(this.contextualMappings).forEach(([keyword, iconName]) => {
        if (text.includes(keyword) && !element.querySelector('.professional-icon')) {
          this.addIconToElement(element, iconName, 'prepend');
        }
      });
    });
  }

  /**
   * 从元素检测图标名称
   */
  detectIconFromElement(element) {
    const classList = Array.from(element.classList);
    const text = element.textContent.toLowerCase();
    
    // 检测FontAwesome类名
    const faClass = classList.find(cls => cls.startsWith('fa-'));
    if (faClass) {
      return this.mapFontAwesomeToHeroicon(faClass);
    }
    
    // 检测Material Icons
    if (classList.includes('material-icons')) {
      return this.mapMaterialIconToHeroicon(text);
    }
    
    // 检测自定义图标类名
    const iconClass = classList.find(cls => cls.includes('icon'));
    if (iconClass) {
      return this.mapCustomIconToHeroicon(iconClass);
    }
    
    return null;
  }

  /**
   * FontAwesome到Heroicon的映射
   */
  mapFontAwesomeToHeroicon(faClass) {
    const mappings = {
      'fa-user': 'user',
      'fa-users': 'user-group',
      'fa-home': 'home',
      'fa-cog': 'cog-6-tooth',
      'fa-bell': 'bell',
      'fa-chart-bar': 'chart-bar',
      'fa-shield': 'shield-check',
      'fa-plus': 'plus',
      'fa-minus': 'minus',
      'fa-times': 'x-mark',
      'fa-check': 'check',
      'fa-envelope': 'envelope',
      'fa-phone': 'phone',
      'fa-star': 'star',
      'fa-trophy': 'trophy',
      'fa-credit-card': 'credit-card',
      'fa-dollar-sign': 'currency-dollar',
      'fa-file-text': 'document-text',
      'fa-briefcase': 'briefcase',
      'fa-balance-scale': 'scale'
    };
    
    return mappings[faClass] || null;
  }

  /**
   * Material Icons到Heroicon的映射
   */
  mapMaterialIconToHeroicon(iconText) {
    const mappings = {
      'person': 'user',
      'group': 'user-group',
      'home': 'home',
      'settings': 'cog-6-tooth',
      'notifications': 'bell',
      'bar_chart': 'chart-bar',
      'security': 'shield-check',
      'add': 'plus',
      'remove': 'minus',
      'close': 'x-mark',
      'check': 'check',
      'email': 'envelope',
      'phone': 'phone',
      'star': 'star',
      'trophy': 'trophy',
      'credit_card': 'credit-card',
      'attach_money': 'currency-dollar',
      'description': 'document-text',
      'work': 'briefcase'
    };
    
    return mappings[iconText] || null;
  }

  /**
   * 自定义图标类名到Heroicon的映射
   */
  mapCustomIconToHeroicon(iconClass) {
    // 简单的关键词匹配
    if (iconClass.includes('user')) return 'user';
    if (iconClass.includes('home')) return 'home';
    if (iconClass.includes('setting')) return 'cog-6-tooth';
    if (iconClass.includes('bell') || iconClass.includes('notification')) return 'bell';
    if (iconClass.includes('chart') || iconClass.includes('stats')) return 'chart-bar';
    if (iconClass.includes('security') || iconClass.includes('shield')) return 'shield-check';
    if (iconClass.includes('plus') || iconClass.includes('add')) return 'plus';
    if (iconClass.includes('minus') || iconClass.includes('remove')) return 'minus';
    if (iconClass.includes('close') || iconClass.includes('times')) return 'x-mark';
    if (iconClass.includes('check') || iconClass.includes('tick')) return 'check';
    if (iconClass.includes('mail') || iconClass.includes('envelope')) return 'envelope';
    if (iconClass.includes('phone') || iconClass.includes('call')) return 'phone';
    if (iconClass.includes('star') || iconClass.includes('favorite')) return 'star';
    if (iconClass.includes('trophy') || iconClass.includes('award')) return 'trophy';
    if (iconClass.includes('card') || iconClass.includes('payment')) return 'credit-card';
    if (iconClass.includes('dollar') || iconClass.includes('money')) return 'currency-dollar';
    if (iconClass.includes('document') || iconClass.includes('file')) return 'document-text';
    if (iconClass.includes('briefcase') || iconClass.includes('work')) return 'briefcase';
    if (iconClass.includes('scale') || iconClass.includes('legal')) return 'scale';
    
    return null;
  }

  /**
   * 替换为专业图标
   */
  replaceWithProfessionalIcon(element, iconName) {
    const size = this.getElementSize(element);
    const className = `professional-icon ${element.className}`.trim();
    
    window.IconSystem.replaceWithIcon(element, iconName, {
      size: size.toString(),
      className
    });
    
    this.upgradedElements.add(element);
  }

  /**
   * 为元素添加图标
   */
  addIconToElement(element, iconName, position = 'prepend') {
    const icon = window.IconSystem.createElement(iconName, {
      size: '16',
      className: 'professional-icon contextual-icon'
    });
    
    if (position === 'prepend') {
      element.insertBefore(icon, element.firstChild);
    } else {
      element.appendChild(icon);
    }
    
    this.upgradedElements.add(icon);
  }

  /**
   * 获取元素尺寸
   */
  getElementSize(element) {
    const computedStyle = window.getComputedStyle(element);
    const fontSize = parseInt(computedStyle.fontSize);
    
    if (fontSize <= 12) return 12;
    if (fontSize <= 16) return 16;
    if (fontSize <= 20) return 20;
    if (fontSize <= 24) return 24;
    if (fontSize <= 32) return 32;
    return 24; // 默认尺寸
  }

  /**
   * 获取所有文本节点
   */
  getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // 跳过脚本和样式标签
          const parent = node.parentElement;
          if (parent && (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE')) {
            return NodeFilter.FILTER_REJECT;
          }
          // 只处理包含emoji的文本节点
          return /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(node.textContent) 
            ? NodeFilter.FILTER_ACCEPT 
            : NodeFilter.FILTER_REJECT;
        }
      }
    );
    
    let node;
    while (node = walker.nextNode()) {
      textNodes.push(node);
    }
    
    return textNodes;
  }

  /**
   * 应用专业图标样式
   */
  applyProfessionalStyles() {
    // 如果样式还未添加，则添加
    if (!document.getElementById('professional-icon-styles')) {
      const style = document.createElement('style');
      style.id = 'professional-icon-styles';
      style.textContent = `
        .professional-icon {
          display: inline-block;
          vertical-align: middle;
          flex-shrink: 0;
          transition: all 0.2s ease-in-out;
        }
        
        .inline-icon {
          margin: 0 4px;
        }
        
        .contextual-icon {
          margin-right: 8px;
        }
        
        .professional-icon:hover {
          transform: scale(1.1);
        }
        
        /* 不同尺寸的图标样式 */
        .professional-icon[width="12"] { width: 12px; height: 12px; }
        .professional-icon[width="16"] { width: 16px; height: 16px; }
        .professional-icon[width="20"] { width: 20px; height: 20px; }
        .professional-icon[width="24"] { width: 24px; height: 24px; }
        .professional-icon[width="32"] { width: 32px; height: 32px; }
        
        /* 颜色主题 */
        .icon-primary { color: var(--color-primary, #2563eb); }
        .icon-secondary { color: var(--color-secondary, #7c3aed); }
        .icon-success { color: var(--color-success, #059669); }
        .icon-warning { color: var(--color-warning, #d97706); }
        .icon-error { color: var(--color-error, #dc2626); }
        .icon-muted { color: var(--text-muted, #9ca3af); }
      `;
      document.head.appendChild(style);
    }
  }

  /**
   * 监听DOM变化
   */
  observeChanges() {
    const observer = new MutationObserver((mutations) => {
      let shouldUpgrade = false;
      
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          shouldUpgrade = true;
        }
      });
      
      if (shouldUpgrade) {
        // 延迟执行，避免频繁升级
        setTimeout(() => this.performUpgrade(), 100);
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  /**
   * 手动升级指定元素
   */
  upgradeElement(element) {
    if (element.querySelector) {
      // 升级子元素中的图标
      this.upgradeEmojiIcons();
      this.upgradeClassBasedIcons();
      this.upgradeDataAttributeIcons();
    }
  }

  /**
   * 获取升级统计
   */
  getUpgradeStats() {
    return {
      totalUpgraded: this.upgradedElements.size,
      availableIcons: Object.keys(window.IconSystem.icons).length,
      mappings: Object.keys(this.iconMappings).length
    };
  }
}

// 创建全局实例
window.IconUpgradeSystem = new IconUpgradeSystem();

// 自动初始化
window.IconUpgradeSystem.init();

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = IconUpgradeSystem;
}