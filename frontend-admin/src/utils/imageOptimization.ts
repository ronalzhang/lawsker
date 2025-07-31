/**
 * 图片优化工具
 * 基于系统优化建议文档的具体要求
 */

// 检测WebP支持
function supportsWebP(): boolean {
  if (typeof window === 'undefined') return false;
  
  const canvas = document.createElement('canvas');
  canvas.width = 1;
  canvas.height = 1;
  
  return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
}

// 图片懒加载和压缩
export const imageOptimization = {
  // WebP格式支持
  convertToWebP: (src: string): string => {
    if (supportsWebP()) {
      return src.replace(/\.(jpg|jpeg|png)$/, '.webp');
    }
    return src;
  },
  
  // 响应式图片
  generateSrcSet: (baseSrc: string): string => {
    const sizes = [320, 640, 1024, 1920];
    return sizes.map(size => 
      `${baseSrc}?w=${size} ${size}w`
    ).join(', ');
  },

  // 图片预加载
  preloadImage: (src: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = reject;
      img.src = src;
    });
  },

  // 图片压缩
  compressImage: (file: File, quality: number = 0.8): Promise<Blob> => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      const img = new Image();
      
      img.onload = () => {
        // 计算压缩后的尺寸
        const maxWidth = 1920;
        const maxHeight = 1080;
        let { width, height } = img;
        
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        
        if (height > maxHeight) {
          width = (width * maxHeight) / height;
          height = maxHeight;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // 绘制并压缩
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(resolve, 'image/jpeg', quality);
      };
      
      img.src = URL.createObjectURL(file);
    });
  },

  // 图片懒加载观察器
  createLazyLoadObserver: (callback?: (entry: IntersectionObserverEntry) => void) => {
    if (!('IntersectionObserver' in window)) {
      // 降级处理
      return {
        observe: (element: Element) => {
          if (element instanceof HTMLImageElement) {
            const dataSrc = element.getAttribute('data-src');
            if (dataSrc) {
              element.src = dataSrc;
              element.removeAttribute('data-src');
            }
          }
        },
        disconnect: () => {}
      };
    }

    return new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          const dataSrc = img.getAttribute('data-src');
          
          if (dataSrc) {
            img.src = imageOptimization.convertToWebP(dataSrc);
            img.removeAttribute('data-src');
            img.classList.remove('lazy');
            img.classList.add('loaded');
          }
          
          callback?.(entry);
        }
      });
    }, {
      rootMargin: '50px 0px',
      threshold: 0.01
    });
  },

  // 初始化懒加载
  initLazyLoading: () => {
    const observer = imageOptimization.createLazyLoadObserver();
    
    // 观察所有懒加载图片
    document.querySelectorAll('img[data-src]').forEach((img) => {
      observer.observe(img);
    });

    // 监听动态添加的图片
    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node as Element;
            
            // 检查新添加的图片
            if (element.tagName === 'IMG' && element.hasAttribute('data-src')) {
              observer.observe(element);
            }
            
            // 检查子元素中的图片
            element.querySelectorAll?.('img[data-src]').forEach((img) => {
              observer.observe(img);
            });
          }
        });
      });
    });

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true
    });

    return { observer, mutationObserver };
  },

  // 图片错误处理
  handleImageError: (img: HTMLImageElement, fallbackSrc?: string) => {
    img.onerror = () => {
      if (fallbackSrc) {
        img.src = fallbackSrc;
      } else {
        // 使用默认占位图
        img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuWbvueJh+WKoOi9veWksei0pTwvdGV4dD48L3N2Zz4=';
      }
      img.classList.add('error');
    };
  },

  // 创建响应式图片元素
  createResponsiveImage: (src: string, alt: string, className?: string): HTMLImageElement => {
    const img = document.createElement('img');
    
    // 设置基本属性
    img.alt = alt;
    img.className = className || '';
    
    // 设置响应式属性
    img.setAttribute('data-src', src);
    img.srcset = imageOptimization.generateSrcSet(src);
    img.sizes = '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw';
    
    // 设置占位图
    img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PC9zdmc+';
    
    // 添加懒加载类
    img.classList.add('lazy');
    
    // 错误处理
    imageOptimization.handleImageError(img);
    
    return img;
  },

  // 图片格式检测和转换
  detectOptimalFormat: (src: string): string => {
    // 检测浏览器支持的格式
    const formats = {
      webp: supportsWebP(),
      avif: 'createImageBitmap' in window // 简单的AVIF检测
    };

    if (formats.avif && src.includes('.jpg') || src.includes('.png')) {
      return src.replace(/\.(jpg|jpeg|png)$/, '.avif');
    }
    
    if (formats.webp && src.includes('.jpg') || src.includes('.png')) {
      return src.replace(/\.(jpg|jpeg|png)$/, '.webp');
    }
    
    return src;
  },

  // 图片预加载策略
  preloadCriticalImages: (images: string[]) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    
    images.forEach((src) => {
      const optimizedSrc = imageOptimization.detectOptimalFormat(src);
      const preloadLink = link.cloneNode() as HTMLLinkElement;
      preloadLink.href = optimizedSrc;
      document.head.appendChild(preloadLink);
    });
  }
};

// Vue 3 组合式API
export function useImageOptimization() {
  const { onMounted, onUnmounted } = require('vue');
  let observers: { observer: IntersectionObserver; mutationObserver: MutationObserver } | null = null;

  onMounted(() => {
    observers = imageOptimization.initLazyLoading();
  });

  onUnmounted(() => {
    if (observers) {
      observers.observer.disconnect();
      observers.mutationObserver.disconnect();
    }
  });

  return {
    convertToWebP: imageOptimization.convertToWebP,
    generateSrcSet: imageOptimization.generateSrcSet,
    preloadImage: imageOptimization.preloadImage,
    compressImage: imageOptimization.compressImage,
    createResponsiveImage: imageOptimization.createResponsiveImage,
    detectOptimalFormat: imageOptimization.detectOptimalFormat,
    preloadCriticalImages: imageOptimization.preloadCriticalImages
  };
}

// 自动初始化
if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    imageOptimization.initLazyLoading();
  });
}