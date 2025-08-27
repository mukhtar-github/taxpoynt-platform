/**
 * Performance Utilities
 * =====================
 * Tools for monitoring and optimizing frontend performance
 */

import { useEffect, useState } from 'react';

// Web Vitals tracking
export interface WebVitals {
  CLS: number | null;
  FID: number | null;
  FCP: number | null;
  LCP: number | null;
  TTFB: number | null;
}

// Performance observer for Core Web Vitals
export const trackWebVitals = (onVital: (metric: { name: string; value: number }) => void) => {
  if (typeof window === 'undefined') return;

  // Track LCP (Largest Contentful Paint)
  if ('PerformanceObserver' in window) {
    try {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        if (lastEntry) {
          onVital({ name: 'LCP', value: lastEntry.startTime });
        }
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

      // Track FID (First Input Delay)
      const fidObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          if (entry.name === 'first-input') {
            onVital({ name: 'FID', value: (entry as any).processingStart - entry.startTime });
          }
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });

      // Track CLS (Cumulative Layout Shift)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
            onVital({ name: 'CLS', value: clsValue });
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      console.warn('Performance observation failed:', error);
    }
  }
};

// Image optimization utility
export const getOptimizedImageSrc = (src: string, format: 'webp' | 'avif' | 'auto' = 'auto') => {
  if (typeof window === 'undefined') return src;
  
  // Check browser support
  const supportsWebP = (() => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      return canvas.toDataURL('image/webp').startsWith('data:image/webp');
    } catch {
      return false;
    }
  })();

  const supportsAvif = (() => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      return canvas.toDataURL('image/avif').startsWith('data:image/avif');
    } catch {
      return false;
    }
  })();

  // Return optimized format based on browser support
  if (format === 'auto') {
    if (supportsAvif) {
      return src.replace(/\.(jpg|jpeg|png)$/i, '.avif');
    } else if (supportsWebP) {
      return src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    }
  } else if (format === 'webp' && supportsWebP) {
    return src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
  } else if (format === 'avif' && supportsAvif) {
    return src.replace(/\.(jpg|jpeg|png)$/i, '.avif');
  }

  return src;
};

// Hook for tracking component performance
export const usePerformanceTracking = (componentName: string) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Log slow renders in development
      if (process.env.NODE_ENV === 'development' && renderTime > 16.67) {
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
      }
    };
  });
};

// Hook for lazy loading intersection observer
export const useLazyLoading = () => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [element, setElement] = useState<Element | null>(null);

  useEffect(() => {
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);
          observer.unobserve(element);
        }
      },
      {
        rootMargin: '50px 0px', // Start loading 50px before element comes into view
        threshold: 0.1
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [element]);

  return { isIntersecting, setElement };
};

// Bundle size analyzer (development only)
export const analyzeBundleSize = () => {
  if (process.env.NODE_ENV !== 'development') return;

  // Analyze loaded scripts
  const scripts = Array.from(document.scripts);
  let totalSize = 0;

  scripts.forEach((script) => {
    if (script.src) {
      fetch(script.src, { method: 'HEAD' })
        .then((response) => {
          const size = parseInt(response.headers.get('content-length') || '0');
          totalSize += size;
          console.log(`Script: ${script.src} - Size: ${(size / 1024).toFixed(2)}KB`);
        })
        .catch(() => {
          // Silent fail for CORS issues
        });
    }
  });

  setTimeout(() => {
    console.log(`Total estimated bundle size: ${(totalSize / 1024).toFixed(2)}KB`);
  }, 1000);
};

// Memory usage tracking
export const trackMemoryUsage = () => {
  if (typeof window === 'undefined' || !(performance as any).memory) return null;

  const memory = (performance as any).memory;
  return {
    used: Math.round(memory.usedJSHeapSize / 1048576 * 100) / 100, // MB
    total: Math.round(memory.totalJSHeapSize / 1048576 * 100) / 100, // MB
    limit: Math.round(memory.jsHeapSizeLimit / 1048576 * 100) / 100 // MB
  };
};

// Network-aware loading
export const useNetworkAwareLoading = () => {
  const [networkInfo, setNetworkInfo] = useState({
    isSlowConnection: false,
    effectiveType: '4g'
  });

  useEffect(() => {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const updateNetworkInfo = () => {
        setNetworkInfo({
          isSlowConnection: ['slow-2g', '2g', '3g'].includes(connection.effectiveType),
          effectiveType: connection.effectiveType
        });
      };

      updateNetworkInfo();
      connection.addEventListener('change', updateNetworkInfo);

      return () => {
        connection.removeEventListener('change', updateNetworkInfo);
      };
    }
  }, []);

  return networkInfo;
};

// Preload critical resources
export const preloadCriticalResources = (resources: Array<{ href: string; as: string; type?: string }>) => {
  if (typeof document === 'undefined') return;

  resources.forEach(({ href, as, type }) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    if (type) link.type = type;
    
    // Avoid duplicate preloads
    if (!document.querySelector(`link[href="${href}"]`)) {
      document.head.appendChild(link);
    }
  });
};

export default {
  trackWebVitals,
  getOptimizedImageSrc,
  usePerformanceTracking,
  useLazyLoading,
  analyzeBundleSize,
  trackMemoryUsage,
  useNetworkAwareLoading,
  preloadCriticalResources
};
