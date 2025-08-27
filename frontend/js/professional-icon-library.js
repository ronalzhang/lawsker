/**
 * Lawsker Professional Icon Library Extension
 * 专业图标库扩展 - 添加更多业务相关的专业图标
 */

// 扩展现有的Heroicons图标库
const EXTENDED_HEROICONS = {
  // 法律专业图标
  'gavel': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" />
  </svg>`,

  'law-book': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
  </svg>`,

  'contract': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>`,

  'courthouse': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 21h19.5m-18-18v18m2.25-18v18m13.5-18v18M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h18M12 3v18" />
  </svg>`,

  // 业务流程图标
  'workflow': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
  </svg>`,

  'process': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
  </svg>`,

  'assignment': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
  </svg>`,

  // 数据分析图标
  'analytics': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
  </svg>`,

  'trending-up': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
  </svg>`,

  'trending-down': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6L9 12.75l4.286-4.286a11.948 11.948 0 014.306 6.43l.776 2.898m0 0l3.182-5.511m-3.182 5.511l-5.511-3.181" />
  </svg>`,

  // 通知和状态图标
  'notification-badge': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M9.143 17.082a24.248 24.248 0 003.844.148m-3.844-.148a23.856 23.856 0 01-5.455-1.31 8.964 8.964 0 002.3-5.542m3.155 6.852a3 3 0 005.667 1.97m1.965-2.277L21 21m-4.225-4.225a23.81 23.81 0 003.536-1.003A8.967 8.967 0 0118 9.75V9A6 6 0 006.53 6.53m10.245 10.245L6.53 6.53M3 3l3.53 3.53" />
  </svg>`,

  'status-online': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
  </svg>`,

  'status-offline': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
  </svg>`,

  // 安全和权限图标
  'key': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
  </svg>`,

  'lock-closed': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
  </svg>`,

  'lock-open': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
  </svg>`,

  // 搜索和过滤图标
  'magnifying-glass': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
  </svg>`,

  'funnel': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
  </svg>`,

  // 编辑和操作图标
  'pencil': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
  </svg>`,

  'trash': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
  </svg>`,

  'duplicate': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75" />
  </svg>`,

  // 网络和连接图标
  'wifi': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 017.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 011.06 0z" />
  </svg>`,

  'signal': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>`,

  // 媒体和内容图标
  'photo': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M18 12.75h.008v.008H18V12.75zm.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
  </svg>`,

  'video-camera': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
  </svg>`,

  'microphone': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
  </svg>`,

  // 地理位置图标
  'map-pin': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
  </svg>`,

  'globe': `<svg class="icon" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
  </svg>`
};

/**
 * Professional Icon Library Class
 * 专业图标库类
 */
class ProfessionalIconLibrary {
  constructor() {
    this.extendedIcons = EXTENDED_HEROICONS;
    this.categories = {
      legal: ['scale', 'gavel', 'law-book', 'contract', 'courthouse'],
      business: ['briefcase', 'workflow', 'process', 'assignment'],
      analytics: ['analytics', 'trending-up', 'trending-down', 'chart-bar'],
      status: ['notification-badge', 'status-online', 'status-offline'],
      security: ['key', 'lock-closed', 'lock-open', 'shield-check'],
      search: ['magnifying-glass', 'funnel'],
      edit: ['pencil', 'trash', 'duplicate'],
      network: ['wifi', 'signal'],
      media: ['photo', 'video-camera', 'microphone'],
      location: ['map-pin', 'globe'],
      user: ['user', 'user-group', 'user-circle'],
      finance: ['credit-card', 'banknotes', 'currency-dollar'],
      achievement: ['trophy', 'star', 'star-solid', 'fire'],
      navigation: ['home', 'cog-6-tooth', 'bell'],
      actions: ['plus', 'minus', 'x-mark', 'check'],
      communication: ['envelope', 'phone'],
      feedback: ['exclamation-triangle', 'information-circle', 'check-circle', 'x-circle'],
      upload: ['cloud-arrow-up', 'document-arrow-up'],
      time: ['clock', 'calendar-days'],
      visibility: ['eye', 'eye-slash']
    };
  }

  /**
   * 初始化专业图标库
   */
  init() {
    console.log('🎨 初始化专业图标库...');
    
    // 扩展现有的IconSystem
    if (window.IconSystem) {
      // 合并扩展图标到现有图标库
      Object.assign(window.IconSystem.icons, this.extendedIcons);
      
      // 添加分类方法
      window.IconSystem.getIconsByCategory = (category) => {
        return this.getIconsByCategory(category);
      };
      
      // 添加搜索方法
      window.IconSystem.searchIcons = (query) => {
        return this.searchIcons(query);
      };
      
      // 添加随机图标方法
      window.IconSystem.getRandomIcon = (category) => {
        return this.getRandomIcon(category);
      };
      
      console.log(`✅ 专业图标库初始化完成，新增 ${Object.keys(this.extendedIcons).length} 个图标`);
    } else {
      console.warn('⚠️ IconSystem 未找到，请先加载 icon-system.js');
    }
  }

  /**
   * 根据分类获取图标
   */
  getIconsByCategory(category) {
    if (!this.categories[category]) {
      console.warn(`分类 "${category}" 不存在`);
      return [];
    }
    
    return this.categories[category].map(iconName => ({
      name: iconName,
      svg: window.IconSystem.getIcon(iconName),
      category: category
    }));
  }

  /**
   * 搜索图标
   */
  searchIcons(query) {
    const results = [];
    const searchTerm = query.toLowerCase();
    
    // 搜索图标名称
    Object.keys(window.IconSystem.icons).forEach(iconName => {
      if (iconName.toLowerCase().includes(searchTerm)) {
        results.push({
          name: iconName,
          svg: window.IconSystem.getIcon(iconName),
          matchType: 'name'
        });
      }
    });
    
    // 搜索分类
    Object.entries(this.categories).forEach(([categoryName, icons]) => {
      if (categoryName.toLowerCase().includes(searchTerm)) {
        icons.forEach(iconName => {
          if (!results.find(r => r.name === iconName)) {
            results.push({
              name: iconName,
              svg: window.IconSystem.getIcon(iconName),
              matchType: 'category',
              category: categoryName
            });
          }
        });
      }
    });
    
    return results;
  }

  /**
   * 获取随机图标
   */
  getRandomIcon(category = null) {
    let iconNames;
    
    if (category && this.categories[category]) {
      iconNames = this.categories[category];
    } else {
      iconNames = Object.keys(window.IconSystem.icons);
    }
    
    const randomName = iconNames[Math.floor(Math.random() * iconNames.length)];
    return {
      name: randomName,
      svg: window.IconSystem.getIcon(randomName)
    };
  }

  /**
   * 获取所有分类
   */
  getAllCategories() {
    return Object.keys(this.categories);
  }

  /**
   * 获取图标统计信息
   */
  getStats() {
    const totalIcons = Object.keys(window.IconSystem.icons).length;
    const extendedIcons = Object.keys(this.extendedIcons).length;
    const categories = Object.keys(this.categories).length;
    
    return {
      totalIcons,
      extendedIcons,
      categories,
      categorizedIcons: Object.values(this.categories).flat().length
    };
  }

  /**
   * 创建图标选择器组件
   */
  createIconPicker(container, options = {}) {
    const {
      onSelect = () => {},
      showSearch = true,
      showCategories = true,
      size = '24'
    } = options;
    
    const pickerHtml = `
      <div class="icon-picker">
        ${showSearch ? `
          <div class="icon-search">
            <input type="text" placeholder="搜索图标..." class="icon-search-input">
          </div>
        ` : ''}
        
        ${showCategories ? `
          <div class="icon-categories">
            <button class="category-btn active" data-category="all">全部</button>
            ${this.getAllCategories().map(cat => 
              `<button class="category-btn" data-category="${cat}">${cat}</button>`
            ).join('')}
          </div>
        ` : ''}
        
        <div class="icon-grid"></div>
      </div>
    `;
    
    container.innerHTML = pickerHtml;
    
    // 添加样式
    this.addPickerStyles();
    
    // 绑定事件
    this.bindPickerEvents(container, onSelect, size);
    
    // 显示所有图标
    this.showIconsInPicker(container, Object.keys(window.IconSystem.icons), size);
  }

  /**
   * 添加图标选择器样式
   */
  addPickerStyles() {
    if (document.getElementById('icon-picker-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'icon-picker-styles';
    style.textContent = `
      .icon-picker {
        max-width: 600px;
        border: 1px solid var(--gray-300, #d1d5db);
        border-radius: 8px;
        background: white;
        padding: 16px;
      }
      
      .icon-search {
        margin-bottom: 16px;
      }
      
      .icon-search-input {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid var(--gray-300, #d1d5db);
        border-radius: 6px;
        font-size: 14px;
      }
      
      .icon-categories {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
      }
      
      .category-btn {
        padding: 6px 12px;
        border: 1px solid var(--gray-300, #d1d5db);
        border-radius: 4px;
        background: white;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .category-btn:hover {
        background: var(--gray-100, #f3f4f6);
      }
      
      .category-btn.active {
        background: var(--primary-600, #2563eb);
        color: white;
        border-color: var(--primary-600, #2563eb);
      }
      
      .icon-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
        gap: 8px;
        max-height: 300px;
        overflow-y: auto;
      }
      
      .icon-item {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border: 1px solid var(--gray-200, #e5e7eb);
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        background: white;
      }
      
      .icon-item:hover {
        border-color: var(--primary-600, #2563eb);
        background: var(--primary-50, #eff6ff);
      }
      
      .icon-item.selected {
        border-color: var(--primary-600, #2563eb);
        background: var(--primary-100, #dbeafe);
      }
    `;
    
    document.head.appendChild(style);
  }

  /**
   * 绑定图标选择器事件
   */
  bindPickerEvents(container, onSelect, size) {
    const searchInput = container.querySelector('.icon-search-input');
    const categoryBtns = container.querySelectorAll('.category-btn');
    
    // 搜索事件
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        if (query) {
          const results = this.searchIcons(query);
          this.showIconsInPicker(container, results.map(r => r.name), size);
        } else {
          this.showIconsInPicker(container, Object.keys(window.IconSystem.icons), size);
        }
      });
    }
    
    // 分类事件
    categoryBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        categoryBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const category = btn.dataset.category;
        let iconNames;
        
        if (category === 'all') {
          iconNames = Object.keys(window.IconSystem.icons);
        } else {
          iconNames = this.categories[category] || [];
        }
        
        this.showIconsInPicker(container, iconNames, size);
      });
    });
  }

  /**
   * 在选择器中显示图标
   */
  showIconsInPicker(container, iconNames, size) {
    const grid = container.querySelector('.icon-grid');
    
    grid.innerHTML = iconNames.map(iconName => `
      <div class="icon-item" data-icon="${iconName}" title="${iconName}">
        ${window.IconSystem.getIcon(iconName, { size, className: 'picker-icon' })}
      </div>
    `).join('');
    
    // 绑定选择事件
    grid.querySelectorAll('.icon-item').forEach(item => {
      item.addEventListener('click', () => {
        // 移除其他选中状态
        grid.querySelectorAll('.icon-item').forEach(i => i.classList.remove('selected'));
        // 添加选中状态
        item.classList.add('selected');
        
        // 触发选择回调
        const iconName = item.dataset.icon;
        if (typeof onSelect === 'function') {
          onSelect(iconName, window.IconSystem.getIcon(iconName));
        }
      });
    });
  }
}

// 创建全局实例
window.ProfessionalIconLibrary = new ProfessionalIconLibrary();

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  window.ProfessionalIconLibrary.init();
});

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProfessionalIconLibrary;
}