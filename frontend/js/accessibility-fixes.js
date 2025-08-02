/**
 * Lawsker系统可访问性修复脚本
 * 基于系统优化建议文档的具体要求
 */

// 自动检查和添加alt属性的脚本
function addMissingAltAttributes() {
  const images = document.querySelectorAll('img:not([alt])');
  images.forEach(img => {
    // 根据图片src或上下文生成描述性alt文本
    const altText = generateAltText(img);
    img.setAttribute('alt', altText);
    console.log(`Added alt attribute to image: ${img.src} -> ${altText}`);
  });
}

function generateAltText(img) {
  const src = img.src;
  const className = img.className;
  const parentElement = img.parentElement;
  
  // 根据图片类型生成合适的alt文本
  if (src.includes('avatar') || className.includes('avatar')) return '用户头像';
  if (src.includes('logo') || className.includes('logo')) return '公司标志';
  if (className.includes('icon')) return '功能图标';
  if (src.includes('chart') || className.includes('chart')) return '数据图表';
  if (src.includes('banner') || className.includes('banner')) return '横幅图片';
  if (src.includes('profile') || className.includes('profile')) return '个人资料图片';
  
  // 根据父元素上下文推断
  if (parentElement) {
    const parentText = parentElement.textContent.trim();
    if (parentText && parentText.length < 50) {
      return `${parentText}相关图片`;
    }
  }
  
  return '图片'; // 默认描述
}

// 增强表单可访问性
function enhanceFormAccessibility() {
  // 为没有label的input添加aria-label
  const inputs = document.querySelectorAll('input:not([aria-label]):not([id])');
  inputs.forEach(input => {
    const placeholder = input.getAttribute('placeholder');
    const type = input.getAttribute('type');
    
    if (placeholder) {
      input.setAttribute('aria-label', placeholder);
    } else {
      // 根据类型设置默认标签
      const defaultLabels = {
        'text': '文本输入',
        'email': '邮箱地址',
        'password': '密码',
        'tel': '电话号码',
        'search': '搜索',
        'url': '网址'
      };
      input.setAttribute('aria-label', defaultLabels[type] || '输入框');
    }
  });
  
  // 为表单添加必填字段标识
  const requiredInputs = document.querySelectorAll('input[required], textarea[required], select[required]');
  requiredInputs.forEach(input => {
    input.setAttribute('aria-required', 'true');
    
    // 如果有对应的label，添加必填标识
    const label = document.querySelector(`label[for="${input.id}"]`);
    if (label && !label.querySelector('.required-indicator')) {
      const requiredSpan = document.createElement('span');
      requiredSpan.className = 'required-indicator';
      requiredSpan.setAttribute('aria-label', '必填');
      requiredSpan.textContent = ' *';
      requiredSpan.style.color = '#e74c3c';
      label.appendChild(requiredSpan);
    }
  });
  
  // 为表单错误添加aria-describedby
  const errorMessages = document.querySelectorAll('.error-message, .form-error');
  errorMessages.forEach(error => {
    const inputId = error.getAttribute('data-for');
    if (inputId) {
      const input = document.getElementById(inputId);
      if (input) {
        error.id = error.id || `${inputId}-error`;
        input.setAttribute('aria-describedby', error.id);
        input.setAttribute('aria-invalid', 'true');
      }
    }
  });
}

// 添加跳转到主内容的链接
function addSkipToContentLink() {
  // 检查是否已存在跳转链接
  if (document.querySelector('.skip-to-content')) {
    return;
  }
  
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.className = 'skip-to-content';
  skipLink.textContent = '跳转到主内容';
  skipLink.style.cssText = `
    position: absolute;
    top: -40px;
    left: 6px;
    background: #007bff;
    color: white;
    padding: 8px;
    text-decoration: none;
    border-radius: 4px;
    z-index: 10000;
    transition: top 0.3s ease;
  `;
  
  // 焦点时显示
  skipLink.addEventListener('focus', () => {
    skipLink.style.top = '6px';
  });
  
  skipLink.addEventListener('blur', () => {
    skipLink.style.top = '-40px';
  });
  
  document.body.insertBefore(skipLink, document.body.firstChild);
  
  // 确保主内容区域有id
  let mainContent = document.querySelector('main, #main-content, .main-content');
  if (!mainContent) {
    // 如果没有找到main元素，尝试找到主要内容区域
    mainContent = document.querySelector('.container, .content, .page-content');
  }
  
  if (mainContent && !mainContent.id) {
    mainContent.id = 'main-content';
  }
}

// 增强语义化HTML结构
function enhanceSemanticHTML() {
  // 为没有role的导航添加role
  const navElements = document.querySelectorAll('nav:not([role])');
  navElements.forEach(nav => {
    nav.setAttribute('role', 'navigation');
    if (!nav.getAttribute('aria-label')) {
      nav.setAttribute('aria-label', '导航菜单');
    }
  });
  
  // 为没有role的header添加role
  const headerElements = document.querySelectorAll('header:not([role])');
  headerElements.forEach(header => {
    header.setAttribute('role', 'banner');
  });
  
  // 为没有role的footer添加role
  const footerElements = document.querySelectorAll('footer:not([role])');
  footerElements.forEach(footer => {
    footer.setAttribute('role', 'contentinfo');
  });
  
  // 为没有role的main添加role
  const mainElements = document.querySelectorAll('main:not([role])');
  mainElements.forEach(main => {
    main.setAttribute('role', 'main');
  });
  
  // 为section添加aria-labelledby
  const sections = document.querySelectorAll('section:not([aria-labelledby]):not([aria-label])');
  sections.forEach(section => {
    const heading = section.querySelector('h1, h2, h3, h4, h5, h6');
    if (heading) {
      if (!heading.id) {
        heading.id = `heading-${Math.random().toString(36).substr(2, 9)}`;
      }
      section.setAttribute('aria-labelledby', heading.id);
    }
  });
}

// 键盘导航支持
function enhanceKeyboardNavigation() {
  // 为可点击元素添加tabindex
  const clickableElements = document.querySelectorAll('.clickable, [onclick]:not(button):not(a):not(input):not(textarea):not(select)');
  clickableElements.forEach(element => {
    if (!element.hasAttribute('tabindex')) {
      element.setAttribute('tabindex', '0');
    }
    
    // 添加键盘事件监听
    element.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        element.click();
      }
    });
  });
  
  // 为模态框添加焦点管理
  const modals = document.querySelectorAll('.modal, [role="dialog"]');
  modals.forEach(modal => {
    modal.addEventListener('shown', () => {
      // 将焦点移到模态框的第一个可聚焦元素
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    });
    
    // 捕获Tab键，实现焦点循环
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
      
      // ESC键关闭模态框
      if (e.key === 'Escape') {
        const closeButton = modal.querySelector('.close, [data-dismiss="modal"]');
        if (closeButton) {
          closeButton.click();
        }
      }
    });
  });
}

// 添加焦点指示器样式
function addFocusIndicators() {
  const style = document.createElement('style');
  style.textContent = `
    /* 焦点指示器样式 */
    *:focus {
      outline: 2px solid #007bff !important;
      outline-offset: 2px !important;
    }
    
    /* 为不同元素定制焦点样式 */
    button:focus, .btn:focus {
      outline: 2px solid #007bff !important;
      outline-offset: 2px !important;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25) !important;
    }
    
    input:focus, textarea:focus, select:focus {
      outline: 2px solid #007bff !important;
      outline-offset: 1px !important;
      border-color: #007bff !important;
    }
    
    a:focus {
      outline: 2px solid #007bff !important;
      outline-offset: 2px !important;
      text-decoration: underline !important;
    }
    
    /* 跳过鼠标用户的焦点样式 */
    .js-focus-visible *:focus:not(.focus-visible) {
      outline: none !important;
      box-shadow: none !important;
    }
    
    .js-focus-visible *:focus.focus-visible {
      outline: 2px solid #007bff !important;
      outline-offset: 2px !important;
    }
  `;
  document.head.appendChild(style);
}

// 支持用户偏好设置
function supportUserPreferences() {
  // 检测用户是否偏好减少动画
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const style = document.createElement('style');
    style.textContent = `
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
    `;
    document.head.appendChild(style);
  }
  
  // 检测用户是否偏好高对比度
  if (window.matchMedia('(prefers-contrast: high)').matches) {
    document.body.classList.add('high-contrast');
    const style = document.createElement('style');
    style.textContent = `
      .high-contrast {
        --text-primary: #000000 !important;
        --text-secondary: #333333 !important;
        --glass-bg: rgba(255, 255, 255, 0.95) !important;
        --glass-border: #000000 !important;
      }
      
      .high-contrast .btn, .high-contrast button {
        border: 2px solid #000000 !important;
        background: #ffffff !important;
        color: #000000 !important;
      }
      
      .high-contrast .btn:hover, .high-contrast button:hover {
        background: #000000 !important;
        color: #ffffff !important;
      }
    `;
    document.head.appendChild(style);
  }
}

// 屏幕阅读器支持
function enhanceScreenReaderSupport() {
  // 为动态内容添加aria-live区域
  const dynamicContentAreas = document.querySelectorAll('.dynamic-content, .status-message, .alert');
  dynamicContentAreas.forEach(area => {
    if (!area.hasAttribute('aria-live')) {
      area.setAttribute('aria-live', 'polite');
    }
  });
  
  // 为加载状态添加屏幕阅读器文本
  const loadingElements = document.querySelectorAll('.loading, .spinner');
  loadingElements.forEach(loading => {
    if (!loading.querySelector('.sr-only')) {
      const srText = document.createElement('span');
      srText.className = 'sr-only';
      srText.textContent = '加载中...';
      loading.appendChild(srText);
    }
  });
  
  // 为图标按钮添加aria-label
  const iconButtons = document.querySelectorAll('button:not([aria-label]) .icon, button:not([aria-label]) i[class*="icon"]');
  iconButtons.forEach(iconButton => {
    const button = iconButton.closest('button');
    if (button && !button.textContent.trim()) {
      // 根据图标类名推断功能
      const iconClass = iconButton.className;
      let label = '按钮';
      
      if (iconClass.includes('close') || iconClass.includes('times')) label = '关闭';
      else if (iconClass.includes('edit') || iconClass.includes('pencil')) label = '编辑';
      else if (iconClass.includes('delete') || iconClass.includes('trash')) label = '删除';
      else if (iconClass.includes('save') || iconClass.includes('check')) label = '保存';
      else if (iconClass.includes('search')) label = '搜索';
      else if (iconClass.includes('menu') || iconClass.includes('bars')) label = '菜单';
      else if (iconClass.includes('home')) label = '首页';
      else if (iconClass.includes('user')) label = '用户';
      else if (iconClass.includes('settings') || iconClass.includes('cog')) label = '设置';
      
      button.setAttribute('aria-label', label);
    }
  });
}

// 初始化所有可访问性修复
function initAccessibilityFixes() {
  console.log('Initializing accessibility fixes...');
  
  // 等待DOM完全加载
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      runAccessibilityFixes();
    });
  } else {
    runAccessibilityFixes();
  }
}

function runAccessibilityFixes() {
  try {
    addMissingAltAttributes();
    enhanceFormAccessibility();
    addSkipToContentLink();
    enhanceSemanticHTML();
    enhanceKeyboardNavigation();
    addFocusIndicators();
    supportUserPreferences();
    enhanceScreenReaderSupport();
    
    console.log('Accessibility fixes applied successfully');
  } catch (error) {
    console.error('Error applying accessibility fixes:', error);
  }
}

// 监听动态内容变化
function observeContentChanges() {
  // 检查document.body是否存在
  if (!document.body) {
    console.warn('document.body not available for MutationObserver');
    return;
  }
  
  const observer = new MutationObserver((mutations) => {
    let shouldReapplyFixes = false;
    
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        // 检查是否有新的图片或表单元素
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.tagName === 'IMG' || node.querySelector('img') ||
                node.tagName === 'FORM' || node.querySelector('form') ||
                node.tagName === 'INPUT' || node.querySelector('input')) {
              shouldReapplyFixes = true;
            }
          }
        });
      }
    });
    
    if (shouldReapplyFixes) {
      setTimeout(() => {
        addMissingAltAttributes();
        enhanceFormAccessibility();
        enhanceSemanticHTML();
        enhanceKeyboardNavigation();
        enhanceScreenReaderSupport();
      }, 100);
    }
  });
  
  try {
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  } catch (error) {
    console.error('Failed to observe content changes:', error);
  }
}

// 自动初始化
initAccessibilityFixes();

// 监听内容变化
if (typeof MutationObserver !== 'undefined' && document.body) {
  observeContentChanges();
}

// 导出函数供外部调用
window.AccessibilityFixes = {
  init: initAccessibilityFixes,
  addMissingAltAttributes,
  enhanceFormAccessibility,
  addSkipToContentLink,
  enhanceSemanticHTML,
  enhanceKeyboardNavigation,
  supportUserPreferences,
  enhanceScreenReaderSupport
};