/**
 * Lawsker 移动端用户体验评估工具
 * 实时评估移动端体验质量，确保评分 > 4.5/5
 */

class MobileUXEvaluator {
  constructor() {
    this.metrics = {
      performance: {},
      usability: {},
      accessibility: {},
      responsiveness: {}
    };
    
    this.weights = {
      performance: 0.3,    // 性能 30%
      usability: 0.35,     // 可用性 35%
      accessibility: 0.15, // 无障碍 15%
      responsiveness: 0.2  // 响应性 20%
    };
    
    this.init();
  }
  
  init() {
    this.evaluatePerformance();
    this.evaluateUsability();
    this.evaluateAccessibility();
    this.evaluateResponsiveness();
    
    // 定期重新评估
    setInterval(() => {
      this.evaluateAll();
    }, 30000); // 每30秒重新评估
  }
  
  evaluatePerformance() {
    console.log('📊 评估性能指标...');
    
    // 页面加载性能
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
      const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
      
      this.metrics.performance.loadTime = this.scoreLoadTime(loadTime);
      this.metrics.performance.domReady = this.scoreDOMReady(domContentLoaded);
    }
    
    // 首屏渲染
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.performance.fcp = this.scoreFCP(entry.startTime);
        }
        if (entry.name === 'largest-contentful-paint') {
          this.metrics.performance.lcp = this.scoreLCP(entry.startTime);
        }
      }
    });
    
    try {
      observer.observe({ entryTypes: ['paint', 'largest-contentful-paint'] });
    } catch (e) {
      console.warn('Performance Observer not supported');
    }
    
    // 内存使用
    if (performance.memory) {
      const memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024; // MB
      this.metrics.performance.memory = this.scoreMemoryUsage(memoryUsage);
    }
    
    // 帧率监控
    this.monitorFrameRate();
  }
  
  evaluateUsability() {
    console.log('👆 评估可用性指标...');
    
    // 触摸目标大小
    this.metrics.usability.touchTargets = this.evaluateTouchTargets();
    
    // 触摸响应时间
    this.metrics.usability.touchResponse = this.evaluateTouchResponse();
    
    // 导航易用性
    this.metrics.usability.navigation = this.evaluateNavigation();
    
    // 表单可用性
    this.metrics.usability.forms = this.evaluateForms();
    
    // 内容可读性
    this.metrics.usability.readability = this.evaluateReadability();
  }
  
  evaluateAccessibility() {
    console.log('♿ 评估无障碍指标...');
    
    // 键盘导航
    this.metrics.accessibility.keyboard = this.evaluateKeyboardNavigation();
    
    // ARIA属性
    this.metrics.accessibility.aria = this.evaluateARIA();
    
    // 颜色对比度
    this.metrics.accessibility.contrast = this.evaluateContrast();
    
    // 焦点管理
    this.metrics.accessibility.focus = this.evaluateFocusManagement();
  }
  
  evaluateResponsiveness() {
    console.log('📱 评估响应式指标...');
    
    // 断点适配
    this.metrics.responsiveness.breakpoints = this.evaluateBreakpoints();
    
    // 布局适配
    this.metrics.responsiveness.layout = this.evaluateLayout();
    
    // 字体缩放
    this.metrics.responsiveness.typography = this.evaluateTypography();
    
    // 图片适配
    this.metrics.responsiveness.images = this.evaluateImages();
  }
  
  // 性能评分方法
  scoreLoadTime(loadTime) {
    if (loadTime < 500) return 5;
    if (loadTime < 1000) return 4;
    if (loadTime < 2000) return 3;
    if (loadTime < 3000) return 2;
    return 1;
  }
  
  scoreDOMReady(domTime) {
    if (domTime < 300) return 5;
    if (domTime < 600) return 4;
    if (domTime < 1000) return 3;
    if (domTime < 1500) return 2;
    return 1;
  }
  
  scoreFCP(fcpTime) {
    if (fcpTime < 800) return 5;
    if (fcpTime < 1500) return 4;
    if (fcpTime < 2500) return 3;
    if (fcpTime < 4000) return 2;
    return 1;
  }
  
  scoreLCP(lcpTime) {
    if (lcpTime < 1200) return 5;
    if (lcpTime < 2000) return 4;
    if (lcpTime < 3000) return 3;
    if (lcpTime < 4000) return 2;
    return 1;
  }
  
  scoreMemoryUsage(memoryMB) {
    if (memoryMB < 25) return 5;
    if (memoryMB < 50) return 4;
    if (memoryMB < 75) return 3;
    if (memoryMB < 100) return 2;
    return 1;
  }
  
  monitorFrameRate() {
    let frames = 0;
    let lastTime = performance.now();
    
    const countFrames = () => {
      frames++;
      const currentTime = performance.now();
      
      if (currentTime >= lastTime + 1000) {
        const fps = frames;
        this.metrics.performance.fps = this.scoreFPS(fps);
        frames = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(countFrames);
    };
    
    requestAnimationFrame(countFrames);
  }
  
  scoreFPS(fps) {
    if (fps >= 55) return 5;
    if (fps >= 45) return 4;
    if (fps >= 35) return 3;
    if (fps >= 25) return 2;
    return 1;
  }
  
  // 可用性评估方法
  evaluateTouchTargets() {
    const buttons = document.querySelectorAll('button, .btn, a, input[type="submit"]');
    let score = 5;
    
    buttons.forEach(btn => {
      const rect = btn.getBoundingClientRect();
      const minSize = Math.min(rect.width, rect.height);
      
      if (minSize < 44) {
        score = Math.min(score, 2);
      } else if (minSize < 48) {
        score = Math.min(score, 4);
      }
    });
    
    return score;
  }
  
  evaluateTouchResponse() {
    // 通过事件监听器测量触摸响应时间
    let responseTimes = [];
    let startTime = 0;
    
    document.addEventListener('touchstart', () => {
      startTime = performance.now();
    }, { passive: true });
    
    document.addEventListener('touchend', () => {
      if (startTime) {
        const responseTime = performance.now() - startTime;
        responseTimes.push(responseTime);
        
        // 保持最近10次的记录
        if (responseTimes.length > 10) {
          responseTimes.shift();
        }
      }
    }, { passive: true });
    
    // 计算平均响应时间
    if (responseTimes.length > 0) {
      const avgResponse = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      
      if (avgResponse < 50) return 5;
      if (avgResponse < 100) return 4;
      if (avgResponse < 150) return 3;
      if (avgResponse < 200) return 2;
      return 1;
    }
    
    return 5; // 默认满分
  }
  
  evaluateNavigation() {
    const nav = document.querySelector('nav, .navbar');
    if (!nav) return 3;
    
    let score = 5;
    
    // 检查移动端导航
    const mobileMenu = document.querySelector('.mobile-menu, .mobile-nav');
    if (window.innerWidth < 768 && !mobileMenu) {
      score -= 2;
    }
    
    // 检查导航可访问性
    const navLinks = nav.querySelectorAll('a');
    navLinks.forEach(link => {
      if (!link.textContent.trim() && !link.getAttribute('aria-label')) {
        score -= 0.5;
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateForms() {
    const forms = document.querySelectorAll('form');
    if (forms.length === 0) return 5;
    
    let score = 5;
    
    forms.forEach(form => {
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach(input => {
        // 检查标签
        const label = form.querySelector(`label[for="${input.id}"]`);
        if (!label && !input.getAttribute('aria-label')) {
          score -= 0.5;
        }
        
        // 检查输入框大小
        const rect = input.getBoundingClientRect();
        if (rect.height < 44) {
          score -= 0.3;
        }
      });
    });
    
    return Math.max(1, score);
  }
  
  evaluateReadability() {
    const textElements = document.querySelectorAll('p, div, span, h1, h2, h3, h4, h5, h6');
    let score = 5;
    
    textElements.forEach(el => {
      const styles = window.getComputedStyle(el);
      const fontSize = parseFloat(styles.fontSize);
      const lineHeight = parseFloat(styles.lineHeight);
      
      // 检查字体大小
      if (fontSize < 14) {
        score -= 0.1;
      }
      
      // 检查行高
      if (lineHeight / fontSize < 1.2) {
        score -= 0.1;
      }
    });
    
    return Math.max(1, score);
  }
  
  // 无障碍评估方法
  evaluateKeyboardNavigation() {
    const focusableElements = document.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    let score = 5;
    
    focusableElements.forEach(el => {
      // 检查是否可以通过键盘访问
      if (el.tabIndex < 0 && !el.hasAttribute('tabindex')) {
        score -= 0.2;
      }
      
      // 检查焦点样式
      const styles = window.getComputedStyle(el, ':focus');
      if (!styles.outline || styles.outline === 'none') {
        score -= 0.1;
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateARIA() {
    const interactiveElements = document.querySelectorAll('button, [role], input, select, textarea');
    let score = 5;
    
    interactiveElements.forEach(el => {
      // 检查ARIA标签
      if (!el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && !el.textContent.trim()) {
        score -= 0.3;
      }
      
      // 检查ARIA状态
      if (el.hasAttribute('aria-expanded') || el.hasAttribute('aria-selected')) {
        // 这是好的实践
      } else if (el.getAttribute('role') === 'button' || el.tagName === 'BUTTON') {
        // 按钮应该有适当的ARIA属性
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateContrast() {
    // 简化的对比度检查
    const textElements = document.querySelectorAll('p, div, span, h1, h2, h3, h4, h5, h6, button, a');
    let score = 5;
    
    textElements.forEach(el => {
      const styles = window.getComputedStyle(el);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      
      // 简单的对比度检查（实际应用中需要更复杂的算法）
      if (color === backgroundColor) {
        score -= 1;
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateFocusManagement() {
    // 检查焦点管理
    let score = 5;
    
    // 检查跳过链接
    const skipLinks = document.querySelectorAll('.skip-link, [href="#main"], [href="#content"]');
    if (skipLinks.length === 0) {
      score -= 1;
    }
    
    // 检查模态框焦点管理
    const modals = document.querySelectorAll('.modal, [role="dialog"]');
    modals.forEach(modal => {
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (focusableElements.length === 0) {
        score -= 0.5;
      }
    });
    
    return Math.max(1, score);
  }
  
  // 响应式评估方法
  evaluateBreakpoints() {
    const breakpoints = [320, 640, 768, 1024, 1280];
    let score = 5;
    
    // 检查CSS媒体查询
    const stylesheets = Array.from(document.styleSheets);
    let hasMediaQueries = false;
    
    try {
      stylesheets.forEach(sheet => {
        if (sheet.cssRules) {
          Array.from(sheet.cssRules).forEach(rule => {
            if (rule.type === CSSRule.MEDIA_RULE) {
              hasMediaQueries = true;
            }
          });
        }
      });
    } catch (e) {
      // 跨域样式表无法访问
    }
    
    if (!hasMediaQueries) {
      score -= 2;
    }
    
    return Math.max(1, score);
  }
  
  evaluateLayout() {
    let score = 5;
    
    // 检查水平滚动
    if (document.body.scrollWidth > window.innerWidth) {
      score -= 2;
    }
    
    // 检查元素溢出
    const elements = document.querySelectorAll('*');
    elements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        score -= 0.1;
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateTypography() {
    let score = 5;
    
    // 检查字体大小
    const textElements = document.querySelectorAll('p, div, span');
    textElements.forEach(el => {
      const fontSize = parseFloat(window.getComputedStyle(el).fontSize);
      
      if (window.innerWidth < 768 && fontSize < 16) {
        score -= 0.1; // 移动端字体应该至少16px
      }
    });
    
    return Math.max(1, score);
  }
  
  evaluateImages() {
    const images = document.querySelectorAll('img');
    let score = 5;
    
    images.forEach(img => {
      // 检查响应式图片
      if (!img.style.maxWidth && !img.classList.contains('responsive')) {
        const rect = img.getBoundingClientRect();
        if (rect.width > window.innerWidth) {
          score -= 0.5;
        }
      }
      
      // 检查alt属性
      if (!img.alt) {
        score -= 0.2;
      }
    });
    
    return Math.max(1, score);
  }
  
  // 计算总体评分
  calculateOverallScore() {
    let totalScore = 0;
    let totalWeight = 0;
    
    // 性能评分
    const performanceMetrics = Object.values(this.metrics.performance);
    if (performanceMetrics.length > 0) {
      const performanceScore = performanceMetrics.reduce((a, b) => a + b, 0) / performanceMetrics.length;
      totalScore += performanceScore * this.weights.performance;
      totalWeight += this.weights.performance;
    }
    
    // 可用性评分
    const usabilityMetrics = Object.values(this.metrics.usability);
    if (usabilityMetrics.length > 0) {
      const usabilityScore = usabilityMetrics.reduce((a, b) => a + b, 0) / usabilityMetrics.length;
      totalScore += usabilityScore * this.weights.usability;
      totalWeight += this.weights.usability;
    }
    
    // 无障碍评分
    const accessibilityMetrics = Object.values(this.metrics.accessibility);
    if (accessibilityMetrics.length > 0) {
      const accessibilityScore = accessibilityMetrics.reduce((a, b) => a + b, 0) / accessibilityMetrics.length;
      totalScore += accessibilityScore * this.weights.accessibility;
      totalWeight += this.weights.accessibility;
    }
    
    // 响应式评分
    const responsivenessMetrics = Object.values(this.metrics.responsiveness);
    if (responsivenessMetrics.length > 0) {
      const responsivenessScore = responsivenessMetrics.reduce((a, b) => a + b, 0) / responsivenessMetrics.length;
      totalScore += responsivenessScore * this.weights.responsiveness;
      totalWeight += this.weights.responsiveness;
    }
    
    return totalWeight > 0 ? totalScore / totalWeight : 0;
  }
  
  // 获取详细报告
  getDetailedReport() {
    const overallScore = this.calculateOverallScore();
    
    return {
      overallScore: overallScore,
      targetMet: overallScore >= 4.5,
      breakdown: {
        performance: {
          score: Object.values(this.metrics.performance).reduce((a, b) => a + b, 0) / Object.values(this.metrics.performance).length || 0,
          weight: this.weights.performance,
          metrics: this.metrics.performance
        },
        usability: {
          score: Object.values(this.metrics.usability).reduce((a, b) => a + b, 0) / Object.values(this.metrics.usability).length || 0,
          weight: this.weights.usability,
          metrics: this.metrics.usability
        },
        accessibility: {
          score: Object.values(this.metrics.accessibility).reduce((a, b) => a + b, 0) / Object.values(this.metrics.accessibility).length || 0,
          weight: this.weights.accessibility,
          metrics: this.metrics.accessibility
        },
        responsiveness: {
          score: Object.values(this.metrics.responsiveness).reduce((a, b) => a + b, 0) / Object.values(this.metrics.responsiveness).length || 0,
          weight: this.weights.responsiveness,
          metrics: this.metrics.responsiveness
        }
      },
      recommendations: this.getRecommendations(overallScore)
    };
  }
  
  getRecommendations(score) {
    const recommendations = [];
    
    if (score < 4.5) {
      recommendations.push('📱 移动端体验评分未达到4.5/5目标，需要优化');
    }
    
    // 性能建议
    const performanceScore = Object.values(this.metrics.performance).reduce((a, b) => a + b, 0) / Object.values(this.metrics.performance).length || 0;
    if (performanceScore < 4) {
      recommendations.push('⚡ 优化页面加载性能，减少资源大小');
      recommendations.push('🖼️ 实施图片懒加载和压缩');
      recommendations.push('💾 优化内存使用，避免内存泄漏');
    }
    
    // 可用性建议
    const usabilityScore = Object.values(this.metrics.usability).reduce((a, b) => a + b, 0) / Object.values(this.metrics.usability).length || 0;
    if (usabilityScore < 4) {
      recommendations.push('👆 增大触摸目标至少44px');
      recommendations.push('📱 优化移动端导航体验');
      recommendations.push('📝 改善表单可用性');
    }
    
    // 无障碍建议
    const accessibilityScore = Object.values(this.metrics.accessibility).reduce((a, b) => a + b, 0) / Object.values(this.metrics.accessibility).length || 0;
    if (accessibilityScore < 4) {
      recommendations.push('♿ 添加ARIA标签和语义化标记');
      recommendations.push('⌨️ 改善键盘导航支持');
      recommendations.push('🎨 提高颜色对比度');
    }
    
    // 响应式建议
    const responsivenessScore = Object.values(this.metrics.responsiveness).reduce((a, b) => a + b, 0) / Object.values(this.metrics.responsiveness).length || 0;
    if (responsivenessScore < 4) {
      recommendations.push('📐 优化响应式布局');
      recommendations.push('🔤 调整移动端字体大小');
      recommendations.push('🖼️ 实现响应式图片');
    }
    
    if (recommendations.length === 0) {
      recommendations.push('🎉 移动端体验优秀，继续保持！');
    }
    
    return recommendations;
  }
  
  evaluateAll() {
    this.evaluatePerformance();
    this.evaluateUsability();
    this.evaluateAccessibility();
    this.evaluateResponsiveness();
  }
  
  // 实时监控
  startRealTimeMonitoring() {
    console.log('🔄 开始实时移动端体验监控...');
    
    setInterval(() => {
      const report = this.getDetailedReport();
      
      // 如果评分低于目标，发出警告
      if (report.overallScore < 4.5) {
        console.warn(`⚠️ 移动端体验评分: ${report.overallScore.toFixed(2)}/5 (目标: 4.5/5)`);
        console.log('💡 建议:', report.recommendations);
      } else {
        console.log(`✅ 移动端体验评分: ${report.overallScore.toFixed(2)}/5 (达标)`);
      }
    }, 60000); // 每分钟检查一次
  }
}

// 全局实例
window.MobileUXEvaluator = MobileUXEvaluator;

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
  if ('ontouchstart' in window || window.innerWidth < 768) {
    window.mobileUXEvaluator = new MobileUXEvaluator();
    
    // 开发模式下启动实时监控
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      window.mobileUXEvaluator.startRealTimeMonitoring();
    }
    
    // 提供全局方法
    window.getMobileUXReport = () => {
      return window.mobileUXEvaluator.getDetailedReport();
    };
    
    console.log('📱 移动端用户体验评估器已启动');
    console.log('💡 使用 getMobileUXReport() 获取详细报告');
  }
});

export { MobileUXEvaluator };