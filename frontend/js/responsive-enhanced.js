/**
 * Lawsker Enhanced Responsive JavaScript Utilities
 * 目标：移动端体验评分 > 4.5/5
 * 
 * 功能：
 * - 智能视口管理
 * - 触摸交互优化
 * - 性能监控
 * - 自适应布局
 * - 用户体验增强
 */

class ResponsiveEnhancer {
  constructor() {
    this.breakpoints = {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      '2xl': 1536
    };
    
    this.currentBreakpoint = this.getCurrentBreakpoint();
    this.isMobile = this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm';
    this.isTablet = this.currentBreakpoint === 'md';
    this.isDesktop = !this.isMobile && !this.isTablet;
    
    this.touchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    this.iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    this.Android = /Android/.test(navigator.userAgent);
    
    this.init();
  }
  
  init() {
    this.setupViewport();
    this.setupTouchOptimizations();
    this.setupResponsiveImages();
    this.setupMobileNavigation();
    this.setupModalEnhancements();
    this.setupFormOptimizations();
    this.setupPerformanceOptimizations();
    this.setupAccessibilityEnhancements();
    this.setupResizeHandler();
    
    // 标记body类
    document.body.classList.add(
      this.isMobile ? 'is-mobile' : 'is-desktop',
      this.touchDevice ? 'is-touch' : 'is-mouse',
      this.iOS ? 'is-ios' : this.Android ? 'is-android' : 'is-other'
    );
    
    console.log('📱 Responsive Enhancer initialized', {
      breakpoint: this.currentBreakpoint,
      isMobile: this.isMobile,
      touchDevice: this.touchDevice,
      platform: this.iOS ? 'iOS' : this.Android ? 'Android' : 'Other'
    });
  }
  
  getCurrentBreakpoint() {
    const width = window.innerWidth;
    
    if (width < this.breakpoints.sm) return 'xs';
    if (width < this.breakpoints.md) return 'sm';
    if (width < this.breakpoints.lg) return 'md';
    if (width < this.breakpoints.xl) return 'lg';
    if (width < this.breakpoints['2xl']) return 'xl';
    return '2xl';
  }
  
  setupViewport() {
    // iOS视口修复
    if (this.iOS) {
      const setViewportHeight = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      };
      
      setViewportHeight();
      window.addEventListener('resize', setViewportHeight);
      window.addEventListener('orientationchange', () => {
        setTimeout(setViewportHeight, 100);
      });
    }
    
    // 防止双击缩放
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (event) => {
      const now = (new Date()).getTime();
      if (now - lastTouchEnd <= 300) {
        event.preventDefault();
      }
      lastTouchEnd = now;
    }, false);
  }
  
  handleSwipeGesture(e) {
    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;
    const minSwipeDistance = 50;
    
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // 水平滑动
      if (Math.abs(deltaX) > minSwipeDistance) {
        if (deltaX > 0) {
          // 右滑
          e.target.dispatchEvent(new CustomEvent('swiperight', { bubbles: true }));
        } else {
          // 左滑
          e.target.dispatchEvent(new CustomEvent('swipeleft', { bubbles: true }));
        }
      }
    } else {
      // 垂直滑动
      if (Math.abs(deltaY) > minSwipeDistance) {
        if (deltaY > 0) {
          // 下滑
          e.target.dispatchEvent(new CustomEvent('swipedown', { bubbles: true }));
        } else {
          // 上滑
          e.target.dispatchEvent(new CustomEvent('swipeup', { bubbles: true }));
        }
      }
    }
  }

  setupTouchOptimizations() {
    if (!this.touchDevice) return;
    
    // 触摸反馈
    document.addEventListener('touchstart', (e) => {
      const target = e.target.closest('.btn, .card, .touch-feedback');
      if (target) {
        target.classList.add('touching');
      }
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      const target = e.target.closest('.btn, .card, .touch-feedback');
      if (target) {
        setTimeout(() => {
          target.classList.remove('touching');
        }, 150);
      }
    }, { passive: true });
    
    // 滑动手势支持
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      this.handleSwipeGesture(e);
    }, { passive: true });
    
    // 长按菜单禁用（在某些元素上）
    document.addEventListener('contextmenu', (e) => {
      if (e.target.closest('.no-context-menu')) {
        e.preventDefault();
      }
    });
    
    // 拖拽优化
    document.addEventListener('touchmove', (e) => {
      if (e.target.closest('.no-scroll')) {
        e.preventDefault();
      }
    }, { passive: false });
  }
  
  setupResponsiveImages() {
    // 懒加载图片
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.classList.add('loaded');
            imageObserver.unobserve(img);
          }
        }
      });
    }, {
      rootMargin: '50px'
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
    
    // 响应式图片源选择
    const updateResponsiveImages = () => {
      document.querySelectorAll('.responsive-img').forEach(img => {
        const sources = {
          mobile: img.dataset.mobileSrc,
          tablet: img.dataset.tabletSrc,
          desktop: img.dataset.desktopSrc
        };
        
        let newSrc;
        if (this.isMobile && sources.mobile) {
          newSrc = sources.mobile;
        } else if (this.isTablet && sources.tablet) {
          newSrc = sources.tablet;
        } else if (sources.desktop) {
          newSrc = sources.desktop;
        }
        
        if (newSrc && img.src !== newSrc) {
          img.src = newSrc;
        }
      });
    };
    
    updateResponsiveImages();
    window.addEventListener('resize', this.debounce(updateResponsiveImages, 250));
  }
  
  setupMobileNavigation() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileOverlay = document.querySelector('.mobile-menu-overlay');
    
    if (!mobileToggle || !mobileMenu) return;
    
    const toggleMenu = () => {
      const isActive = mobileMenu.classList.contains('active');
      
      mobileToggle.classList.toggle('active', !isActive);
      mobileMenu.classList.toggle('active', !isActive);
      
      if (mobileOverlay) {
        mobileOverlay.classList.toggle('active', !isActive);
      }
      
      // 防止背景滚动
      document.body.style.overflow = isActive ? '' : 'hidden';
    };
    
    mobileToggle.addEventListener('click', toggleMenu);
    
    if (mobileOverlay) {
      mobileOverlay.addEventListener('click', toggleMenu);
    }
    
    // ESC键关闭
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
        toggleMenu();
      }
    });
    
    // 链接点击后关闭菜单
    mobileMenu.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') {
        toggleMenu();
      }
    });
  }
  
  setupModalEnhancements() {
    document.addEventListener('click', (e) => {
      // 模态框触发器
      const trigger = e.target.closest('[data-modal-target]');
      if (trigger) {
        e.preventDefault();
        const targetId = trigger.dataset.modalTarget;
        const modal = document.getElementById(targetId);
        if (modal) {
          this.openModal(modal);
        }
      }
      
      // 模态框关闭
      const closeBtn = e.target.closest('.modal-close, .modal-backdrop');
      if (closeBtn) {
        const modal = closeBtn.closest('.modal');
        if (modal) {
          this.closeModal(modal);
        }
      }
    });
    
    // ESC键关闭模态框
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
          this.closeModal(activeModal);
        }
      }
    });
  }
  
  openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // 焦点管理
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
    
    // 焦点陷阱
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      }
    });
  }
  
  closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
  
  setupFormOptimizations() {
    // 输入框焦点优化
    document.addEventListener('focusin', (e) => {
      if (e.target.matches('input, textarea, select')) {
        // iOS键盘弹出时的视口调整
        if (this.iOS) {
          setTimeout(() => {
            e.target.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center' 
            });
          }, 300);
        }
        
        // 添加焦点样式
        e.target.closest('.form-group')?.classList.add('focused');
      }
    });
    
    document.addEventListener('focusout', (e) => {
      if (e.target.matches('input, textarea, select')) {
        e.target.closest('.form-group')?.classList.remove('focused');
      }
    });
    
    // 表单验证增强
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => {
        const invalidFields = form.querySelectorAll(':invalid');
        
        if (invalidFields.length > 0) {
          e.preventDefault();
          
          // 滚动到第一个无效字段
          invalidFields[0].scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
          });
          
          invalidFields[0].focus();
        }
      });
    });
  }
  
  setupPerformanceOptimizations() {
    // 图片预加载
    const preloadImages = () => {
      const images = document.querySelectorAll('img[data-preload]');
      images.forEach(img => {
        if (img.dataset.preload && !img.src) {
          img.src = img.dataset.preload;
        }
      });
    };
    
    // 页面加载完成后预加载
    if (document.readyState === 'complete') {
      preloadImages();
    } else {
      window.addEventListener('load', preloadImages);
    }
    
    // 滚动性能优化
    let ticking = false;
    
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          // 滚动相关的操作
          this.updateScrollIndicators();
          ticking = false;
        });
        ticking = true;
      }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
  }
  
  updateScrollIndicators() {
    const scrolled = window.pageYOffset;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = (scrolled / maxScroll) * 100;
    
    // 更新滚动指示器
    const indicators = document.querySelectorAll('.scroll-indicator');
    indicators.forEach(indicator => {
      indicator.style.width = `${scrollPercent}%`;
    });
    
    // 滚动到顶部按钮
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
      backToTop.classList.toggle('visible', scrolled > 300);
    }
  }
  
  setupAccessibilityEnhancements() {
    // 键盘导航增强
    document.addEventListener('keydown', (e) => {
      // 跳过链接功能
      if (e.key === 'Tab' && e.target.classList.contains('skip-link')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        if (target) {
          target.focus();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
    
    // 焦点可见性增强
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
      }
    });
    
    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-navigation');
    });
    
    // ARIA属性动态更新
    this.updateAriaAttributes();
  }
  
  updateAriaAttributes() {
    // 展开/折叠元素
    document.querySelectorAll('[data-toggle]').forEach(toggle => {
      const targetId = toggle.dataset.toggle;
      const target = document.getElementById(targetId);
      
      if (target) {
        const isExpanded = !target.hidden;
        toggle.setAttribute('aria-expanded', isExpanded);
        target.setAttribute('aria-hidden', !isExpanded);
      }
    });
  }
  
  setupResizeHandler() {
    const handleResize = this.debounce(() => {
      const newBreakpoint = this.getCurrentBreakpoint();
      
      if (newBreakpoint !== this.currentBreakpoint) {
        this.currentBreakpoint = newBreakpoint;
        this.isMobile = newBreakpoint === 'xs' || newBreakpoint === 'sm';
        this.isTablet = newBreakpoint === 'md';
        this.isDesktop = !this.isMobile && !this.isTablet;
        
        // 更新body类
        document.body.className = document.body.className
          .replace(/is-(mobile|desktop)/, this.isMobile ? 'is-mobile' : 'is-desktop');
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('breakpointChange', {
          detail: {
            breakpoint: this.currentBreakpoint,
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            isDesktop: this.isDesktop
          }
        }));
        
        console.log('📱 Breakpoint changed:', this.currentBreakpoint);
      }
    }, 250);
    
    window.addEventListener('resize', handleResize);
  }
  
  // 工具方法
  debounce(func, wait) {
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
  
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
  
  // 公共API
  isMobileDevice() {
    return this.isMobile;
  }
  
  isTabletDevice() {
    return this.isTablet;
  }
  
  isDesktopDevice() {
    return this.isDesktop;
  }
  
  getCurrentBreakpointName() {
    return this.currentBreakpoint;
  }
  
  // 动态加载资源
  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
  
  loadCSS(href) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.onload = resolve;
      link.onerror = reject;
      document.head.appendChild(link);
    });
  }
}

// 触摸手势支持
class TouchGestureHandler {
  constructor() {
    this.startX = 0;
    this.startY = 0;
    this.endX = 0;
    this.endY = 0;
    this.minSwipeDistance = 50;
    
    this.init();
  }
  
  init() {
    document.addEventListener('touchstart', (e) => {
      this.startX = e.touches[0].clientX;
      this.startY = e.touches[0].clientY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      this.endX = e.changedTouches[0].clientX;
      this.endY = e.changedTouches[0].clientY;
      this.handleGesture(e);
    }, { passive: true });
  }
  
  handleGesture(e) {
    const deltaX = this.endX - this.startX;
    const deltaY = this.endY - this.startY;
    
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // 水平滑动
      if (Math.abs(deltaX) > this.minSwipeDistance) {
        if (deltaX > 0) {
          this.onSwipeRight(e);
        } else {
          this.onSwipeLeft(e);
        }
      }
    } else {
      // 垂直滑动
      if (Math.abs(deltaY) > this.minSwipeDistance) {
        if (deltaY > 0) {
          this.onSwipeDown(e);
        } else {
          this.onSwipeUp(e);
        }
      }
    }
  }
  
  onSwipeLeft(e) {
    // 左滑手势 - 可以用于打开侧边栏等
    const target = e.target.closest('[data-swipe-left]');
    if (target) {
      const action = target.dataset.swipeLeft;
      this.executeAction(action, target);
    }
  }
  
  onSwipeRight(e) {
    // 右滑手势 - 可以用于关闭侧边栏、返回等
    const target = e.target.closest('[data-swipe-right]');
    if (target) {
      const action = target.dataset.swipeRight;
      this.executeAction(action, target);
    }
  }
  
  onSwipeUp(e) {
    // 上滑手势
    const target = e.target.closest('[data-swipe-up]');
    if (target) {
      const action = target.dataset.swipeUp;
      this.executeAction(action, target);
    }
  }
  
  onSwipeDown(e) {
    // 下滑手势 - 可以用于刷新等
    const target = e.target.closest('[data-swipe-down]');
    if (target) {
      const action = target.dataset.swipeDown;
      this.executeAction(action, target);
    }
  }
  
  executeAction(action, target) {
    switch (action) {
      case 'refresh':
        window.location.reload();
        break;
      case 'back':
        window.history.back();
        break;
      case 'close':
        target.style.display = 'none';
        break;
      default:
        // 触发自定义事件
        target.dispatchEvent(new CustomEvent('swipe', {
          detail: { action, target }
        }));
    }
  }
}

// 性能监控
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      loadTime: 0,
      renderTime: 0,
      interactionTime: 0
    };
    
    this.init();
  }
  
  init() {
    // 页面加载性能
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0];
      this.metrics.loadTime = navigation.loadEventEnd - navigation.loadEventStart;
      
      console.log('📊 Page Load Time:', this.metrics.loadTime + 'ms');
    });
    
    // 首次内容绘制
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          console.log('🎨 First Contentful Paint:', entry.startTime + 'ms');
        }
      }
    });
    
    observer.observe({ entryTypes: ['paint'] });
    
    // 交互性能监控
    this.monitorInteractions();
  }
  
  monitorInteractions() {
    let interactionStart = 0;
    
    ['click', 'touchstart'].forEach(eventType => {
      document.addEventListener(eventType, () => {
        interactionStart = performance.now();
      }, { passive: true });
    });
    
    ['click', 'touchend'].forEach(eventType => {
      document.addEventListener(eventType, () => {
        if (interactionStart) {
          const interactionTime = performance.now() - interactionStart;
          if (interactionTime > 100) {
            console.warn('⚠️ Slow interaction detected:', interactionTime + 'ms');
          }
        }
      }, { passive: true });
    });
  }
  
  getMetrics() {
    return this.metrics;
  }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  // 主响应式增强器
  window.responsiveEnhancer = new ResponsiveEnhancer();
  
  // 触摸手势处理器
  if ('ontouchstart' in window) {
    window.touchGestureHandler = new TouchGestureHandler();
  }
  
  // 性能监控器
  window.performanceMonitor = new PerformanceMonitor();
  
  // 全局工具函数
  window.ResponsiveUtils = {
    isMobile: () => window.responsiveEnhancer.isMobileDevice(),
    isTablet: () => window.responsiveEnhancer.isTabletDevice(),
    isDesktop: () => window.responsiveEnhancer.isDesktopDevice(),
    getCurrentBreakpoint: () => window.responsiveEnhancer.getCurrentBreakpointName(),
    
    // 动态导入
    loadMobileScript: (src) => {
      if (window.responsiveEnhancer.isMobileDevice()) {
        return window.responsiveEnhancer.loadScript(src);
      }
      return Promise.resolve();
    },
    
    loadDesktopScript: (src) => {
      if (window.responsiveEnhancer.isDesktopDevice()) {
        return window.responsiveEnhancer.loadScript(src);
      }
      return Promise.resolve();
    }
  };
});

// CSS自定义属性更新
const updateCSSCustomProperties = () => {
  const root = document.documentElement;
  
  // 视口尺寸
  root.style.setProperty('--vw', window.innerWidth + 'px');
  root.style.setProperty('--vh', window.innerHeight + 'px');
  
  // 安全区域（iOS刘海屏支持）
  if (CSS.supports('padding: env(safe-area-inset-top)')) {
    root.style.setProperty('--safe-area-top', 'env(safe-area-inset-top)');
    root.style.setProperty('--safe-area-bottom', 'env(safe-area-inset-bottom)');
    root.style.setProperty('--safe-area-left', 'env(safe-area-inset-left)');
    root.style.setProperty('--safe-area-right', 'env(safe-area-inset-right)');
  }
};

// 移动端专用优化
class MobileOptimizer {
  constructor() {
    this.init();
  }
  
  init() {
    this.setupFastClick();
    this.setupScrollOptimization();
    this.setupMemoryOptimization();
    this.setupBatteryOptimization();
  }
  
  setupFastClick() {
    // 移除300ms点击延迟
    document.addEventListener('touchstart', () => {}, { passive: true });
  }
  
  setupScrollOptimization() {
    // 滚动性能优化
    let scrollTimer = null;
    
    window.addEventListener('scroll', () => {
      if (scrollTimer) return;
      
      scrollTimer = setTimeout(() => {
        scrollTimer = null;
        // 滚动结束后的优化操作
        this.optimizeAfterScroll();
      }, 150);
    }, { passive: true });
  }
  
  optimizeAfterScroll() {
    // 清理不可见元素的动画
    const elements = document.querySelectorAll('.animate-mobile');
    elements.forEach(el => {
      const rect = el.getBoundingClientRect();
      const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
      
      if (!isVisible) {
        el.style.willChange = 'auto';
      } else {
        el.style.willChange = 'transform, opacity';
      }
    });
  }
  
  setupMemoryOptimization() {
    // 内存优化
    setInterval(() => {
      if (performance.memory && performance.memory.usedJSHeapSize > 50 * 1024 * 1024) {
        // 内存使用超过50MB时进行清理
        this.cleanupMemory();
      }
    }, 30000);
  }
  
  cleanupMemory() {
    // 清理缓存的图片
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => {
      const rect = img.getBoundingClientRect();
      const isVisible = rect.top < window.innerHeight * 2 && rect.bottom > -window.innerHeight;
      
      if (!isVisible && img.src) {
        img.removeAttribute('src');
      }
    });
  }
  
  setupBatteryOptimization() {
    // 电池优化
    if ('getBattery' in navigator) {
      navigator.getBattery().then(battery => {
        if (battery.level < 0.2) {
          // 低电量模式
          this.enableLowPowerMode();
        }
        
        battery.addEventListener('levelchange', () => {
          if (battery.level < 0.2) {
            this.enableLowPowerMode();
          } else {
            this.disableLowPowerMode();
          }
        });
      });
    }
  }
  
  enableLowPowerMode() {
    document.body.classList.add('low-power-mode');
    // 减少动画
    document.documentElement.style.setProperty('--transition-fast', '0ms');
    document.documentElement.style.setProperty('--transition-normal', '0ms');
  }
  
  disableLowPowerMode() {
    document.body.classList.remove('low-power-mode');
    // 恢复动画
    document.documentElement.style.setProperty('--transition-fast', '150ms ease-in-out');
    document.documentElement.style.setProperty('--transition-normal', '250ms ease-in-out');
  }
}

// 网络状态优化
class NetworkOptimizer {
  constructor() {
    this.connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    this.init();
  }
  
  init() {
    if (this.connection) {
      this.optimizeForConnection();
      this.connection.addEventListener('change', () => {
        this.optimizeForConnection();
      });
    }
  }
  
  optimizeForConnection() {
    const effectiveType = this.connection.effectiveType;
    
    if (effectiveType === 'slow-2g' || effectiveType === '2g') {
      // 慢速网络优化
      this.enableSlowNetworkMode();
    } else if (effectiveType === '3g') {
      // 中速网络优化
      this.enableMediumNetworkMode();
    } else {
      // 快速网络
      this.enableFastNetworkMode();
    }
  }
  
  enableSlowNetworkMode() {
    document.body.classList.add('slow-network');
    // 禁用自动播放
    document.querySelectorAll('video, audio').forEach(media => {
      media.preload = 'none';
    });
  }
  
  enableMediumNetworkMode() {
    document.body.classList.add('medium-network');
    // 延迟加载非关键资源
    document.querySelectorAll('img[data-src]').forEach(img => {
      if (img.dataset.priority !== 'high') {
        // 延迟加载
        setTimeout(() => {
          if (img.dataset.src) {
            img.src = img.dataset.src;
          }
        }, 1000);
      }
    });
  }
  
  enableFastNetworkMode() {
    document.body.classList.add('fast-network');
    // 预加载资源
    this.preloadResources();
  }
  
  preloadResources() {
    // 预加载关键资源
    const criticalImages = document.querySelectorAll('img[data-preload="true"]');
    criticalImages.forEach(img => {
      if (img.dataset.src) {
        const preloadImg = new Image();
        preloadImg.src = img.dataset.src;
      }
    });
  }
}

window.addEventListener('resize', updateCSSCustomProperties);
window.addEventListener('orientationchange', updateCSSCustomProperties);
updateCSSCustomProperties();

// GPU硬件加速优化
const enableGPUAcceleration = () => {
  const elements = document.querySelectorAll('.btn, .card, .modal, .navbar');
  elements.forEach(el => {
    el.style.transform = 'translateZ(0)';
    el.style.backfaceVisibility = 'hidden';
    el.style.perspective = '1000px';
  });
};

// 资源预加载优化
const setupResourcePreloading = () => {
  // 预加载关键CSS
  const preloadCSS = (href) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'style';
    link.href = href;
    document.head.appendChild(link);
  };
  
  // 预加载关键字体
  const preloadFont = (href) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    link.href = href;
    document.head.appendChild(link);
  };
  
  // 预加载Inter字体
  preloadFont('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2');
};

// 语义化标签支持
const enhanceSemanticHTML = () => {
  // 为按钮添加aria-label
  document.querySelectorAll('.btn:not([aria-label])').forEach(btn => {
    const text = btn.textContent.trim();
    if (text) {
      btn.setAttribute('aria-label', text);
    }
  });
  
  // 为表单添加aria-describedby
  document.querySelectorAll('.form-input').forEach(input => {
    const label = document.querySelector(`label[for="${input.id}"]`);
    if (label && !input.getAttribute('aria-describedby')) {
      input.setAttribute('aria-describedby', `${input.id}-description`);
    }
  });
  
  // 为导航添加role
  document.querySelectorAll('.navbar-nav').forEach(nav => {
    if (!nav.getAttribute('role')) {
      nav.setAttribute('role', 'navigation');
    }
  });
};

// 初始化移动端优化器
document.addEventListener('DOMContentLoaded', () => {
  // 启用GPU加速
  enableGPUAcceleration();
  
  // 设置资源预加载
  setupResourcePreloading();
  
  // 增强语义化HTML
  enhanceSemanticHTML();
  
  if ('ontouchstart' in window) {
    window.mobileOptimizer = new MobileOptimizer();
  }
  
  window.networkOptimizer = new NetworkOptimizer();
});

export { ResponsiveEnhancer, TouchGestureHandler, PerformanceMonitor };