/**
 * Mobile Onboarding Optimization Utilities
 * ========================================
 * 
 * Utilities for optimizing onboarding flows on mobile devices.
 * Provides responsive design helpers, touch optimization, and mobile-specific UX patterns.
 * 
 * Features:
 * - Device detection and capabilities
 * - Touch-optimized interaction patterns
 * - Mobile-first responsive utilities
 * - Performance optimization for mobile networks
 * - Accessibility enhancements for mobile
 * - Nigerian mobile network optimizations
 */

export interface MobileCapabilities {
  isMobile: boolean;
  isTablet: boolean;
  isTouch: boolean;
  screenWidth: number;
  screenHeight: number;
  devicePixelRatio: number;
  connectionType: 'slow-2g' | '2g' | '3g' | '4g' | 'unknown';
  isLowEndDevice: boolean;
  supportsWebP: boolean;
  prefersReducedMotion: boolean;
}

export interface MobileOptimizationConfig {
  enableTouchOptimization: boolean;
  enableDataSaving: boolean;
  enableReducedAnimations: boolean;
  enableLargerTouchTargets: boolean;
  enableSimplifiedLayouts: boolean;
  enableProgressiveLoading: boolean;
}

class MobileOnboardingOptimizer {
  private capabilities: MobileCapabilities | null = null;
  private config: MobileOptimizationConfig;

  constructor() {
    this.config = {
      enableTouchOptimization: true,
      enableDataSaving: false, // Will be enabled based on connection
      enableReducedAnimations: false,
      enableLargerTouchTargets: true,
      enableSimplifiedLayouts: false,
      enableProgressiveLoading: true
    };

    if (typeof window !== 'undefined') {
      this.detectCapabilities();
      this.applyOptimizations();
    }
  }

  /**
   * Detect mobile capabilities and constraints
   */
  private detectCapabilities(): void {
    const userAgent = navigator.userAgent;
    const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
    const isTablet = /iPad|Android(?=.*Mobile)/i.test(userAgent);
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    // Get connection information
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    let connectionType: MobileCapabilities['connectionType'] = 'unknown';
    
    if (connection) {
      const effectiveType = connection.effectiveType;
      connectionType = effectiveType || 'unknown';
    }

    // Detect low-end devices (simplified heuristic)
    const isLowEndDevice = navigator.hardwareConcurrency <= 2 || 
                          (navigator as any).deviceMemory <= 2 || 
                          connectionType === 'slow-2g' || connectionType === '2g';

    // Check WebP support
    const supportsWebP = this.checkWebPSupport();

    // Check motion preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    this.capabilities = {
      isMobile,
      isTablet,
      isTouch,
      screenWidth: window.innerWidth,
      screenHeight: window.innerHeight,
      devicePixelRatio: window.devicePixelRatio || 1,
      connectionType,
      isLowEndDevice,
      supportsWebP,
      prefersReducedMotion
    };

    // Update config based on capabilities
    this.updateConfigBasedOnCapabilities();
  }

  /**
   * Update optimization config based on detected capabilities
   */
  private updateConfigBasedOnCapabilities(): void {
    if (!this.capabilities) return;

    const { connectionType, isLowEndDevice, prefersReducedMotion, isMobile } = this.capabilities;

    // Enable data saving for slow connections
    if (connectionType === 'slow-2g' || connectionType === '2g') {
      this.config.enableDataSaving = true;
      this.config.enableProgressiveLoading = true;
    }

    // Simplify for low-end devices
    if (isLowEndDevice) {
      this.config.enableReducedAnimations = true;
      this.config.enableSimplifiedLayouts = true;
    }

    // Respect user motion preferences
    if (prefersReducedMotion) {
      this.config.enableReducedAnimations = true;
    }

    // Mobile-specific optimizations
    if (isMobile) {
      this.config.enableLargerTouchTargets = true;
      this.config.enableTouchOptimization = true;
    }
  }

  /**
   * Check WebP support
   */
  private checkWebPSupport(): boolean {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    } catch {
      return false;
    }
  }

  /**
   * Apply global mobile optimizations
   */
  private applyOptimizations(): void {
    if (!this.capabilities) return;

    // Add mobile-specific CSS classes to body
    const classes = [];
    
    if (this.capabilities.isMobile) classes.push('mobile-device');
    if (this.capabilities.isTablet) classes.push('tablet-device');
    if (this.capabilities.isTouch) classes.push('touch-device');
    if (this.config.enableLargerTouchTargets) classes.push('large-touch-targets');
    if (this.config.enableReducedAnimations) classes.push('reduced-animations');
    if (this.config.enableDataSaving) classes.push('data-saving');

    document.body.classList.add(...classes);

    // Set CSS custom properties for responsive design
    document.documentElement.style.setProperty('--screen-width', `${this.capabilities.screenWidth}px`);
    document.documentElement.style.setProperty('--screen-height', `${this.capabilities.screenHeight}px`);
    document.documentElement.style.setProperty('--device-pixel-ratio', `${this.capabilities.devicePixelRatio}`);
  }

  /**
   * Get responsive classes for onboarding components
   */
  getResponsiveClasses(componentType: 'form' | 'button' | 'card' | 'navigation' | 'progress'): string {
    if (!this.capabilities) return '';

    const classes = [];

    switch (componentType) {
      case 'form':
        if (this.capabilities.isMobile) {
          classes.push('space-y-4', 'px-4', 'py-6');
        } else {
          classes.push('space-y-6', 'px-6', 'py-8');
        }
        break;

      case 'button':
        if (this.config.enableLargerTouchTargets) {
          classes.push('min-h-[44px]', 'px-6', 'text-base');
        }
        if (this.capabilities.isMobile) {
          classes.push('w-full', 'sm:w-auto');
        }
        break;

      case 'card':
        if (this.capabilities.isMobile) {
          classes.push('mx-2', 'rounded-lg', 'shadow-sm');
        } else {
          classes.push('mx-auto', 'max-w-md', 'rounded-xl', 'shadow-lg');
        }
        break;

      case 'navigation':
        if (this.capabilities.isMobile) {
          classes.push('flex-col', 'space-y-2');
        } else {
          classes.push('flex-row', 'space-x-4');
        }
        break;

      case 'progress':
        if (this.capabilities.isMobile) {
          classes.push('text-sm', 'compact');
        } else {
          classes.push('text-base');
        }
        break;
    }

    return classes.join(' ');
  }

  /**
   * Get optimized image loading strategy
   */
  getImageLoadingStrategy(): 'eager' | 'lazy' {
    if (!this.capabilities) return 'lazy';
    
    return this.config.enableDataSaving ? 'lazy' : 'eager';
  }

  /**
   * Get animation duration based on device capabilities
   */
  getAnimationDuration(defaultDuration: number): number {
    if (!this.capabilities) return defaultDuration;

    if (this.config.enableReducedAnimations) return 0;
    if (this.capabilities.isLowEndDevice) return defaultDuration * 0.5;
    
    return defaultDuration;
  }

  /**
   * Check if device should use simplified layouts
   */
  shouldUseSimplifiedLayout(): boolean {
    return this.config.enableSimplifiedLayouts;
  }

  /**
   * Get optimal touch target size
   */
  getTouchTargetSize(): { minHeight: string; minWidth: string } {
    if (!this.capabilities?.isTouch) {
      return { minHeight: '32px', minWidth: '32px' };
    }

    // Nigerian mobile optimization: Larger touch targets for better usability
    return { minHeight: '44px', minWidth: '44px' };
  }

  /**
   * Get network-optimized loading strategy
   */
  getLoadingStrategy(): {
    batchSize: number;
    delayBetweenBatches: number;
    enablePreloading: boolean;
  } {
    if (!this.capabilities) {
      return { batchSize: 5, delayBetweenBatches: 100, enablePreloading: true };
    }

    const { connectionType, isLowEndDevice } = this.capabilities;

    if (connectionType === 'slow-2g' || connectionType === '2g') {
      return { batchSize: 2, delayBetweenBatches: 500, enablePreloading: false };
    }

    if (isLowEndDevice) {
      return { batchSize: 3, delayBetweenBatches: 200, enablePreloading: false };
    }

    return { batchSize: 5, delayBetweenBatches: 100, enablePreloading: true };
  }

  /**
   * Get mobile-optimized form configuration
   */
  getFormConfig(): {
    showLabelsInside: boolean;
    useNativeInputs: boolean;
    enableAutocomplete: boolean;
    groupRelatedFields: boolean;
  } {
    const isMobile = this.capabilities?.isMobile || false;

    return {
      showLabelsInside: isMobile, // Floating labels on mobile
      useNativeInputs: isMobile, // Use native date/time pickers on mobile
      enableAutocomplete: true,
      groupRelatedFields: isMobile // Group related fields to reduce scrolling
    };
  }

  /**
   * Get capabilities for external use
   */
  getCapabilities(): MobileCapabilities | null {
    return this.capabilities;
  }

  /**
   * Get current configuration
   */
  getConfig(): MobileOptimizationConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<MobileOptimizationConfig>): void {
    this.config = { ...this.config, ...updates };
    if (typeof window !== 'undefined') {
      this.applyOptimizations();
    }
  }

  /**
   * Check if current viewport is mobile
   */
  isMobileViewport(): boolean {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < 768; // Tailwind md breakpoint
  }

  /**
   * Get viewport-specific grid classes
   */
  getGridClasses(desktopCols: number = 3): string {
    if (this.isMobileViewport()) {
      return 'grid-cols-1';
    } else if (window.innerWidth < 1024) { // Tailwind lg breakpoint
      return 'grid-cols-2';
    } else {
      return `grid-cols-${desktopCols}`;
    }
  }

  /**
   * Nigerian mobile network specific optimizations
   */
  getNigerianMobileOptimizations(): {
    enableOfflineMode: boolean;
    enableDataCompression: boolean;
    enableProgressiveForms: boolean;
    showDataUsageWarnings: boolean;
  } {
    const isSlowConnection = this.capabilities?.connectionType === 'slow-2g' || this.capabilities?.connectionType === '2g';
    
    return {
      enableOfflineMode: isSlowConnection,
      enableDataCompression: true,
      enableProgressiveForms: this.capabilities?.isMobile || false,
      showDataUsageWarnings: isSlowConnection
    };
  }
}

// Export singleton instance
export const mobileOptimizer = new MobileOnboardingOptimizer();

// Utility functions for React components
export const useMobileOptimization = () => {
  return {
    capabilities: mobileOptimizer.getCapabilities(),
    config: mobileOptimizer.getConfig(),
    getResponsiveClasses: mobileOptimizer.getResponsiveClasses.bind(mobileOptimizer),
    shouldUseSimplifiedLayout: mobileOptimizer.shouldUseSimplifiedLayout.bind(mobileOptimizer),
    getTouchTargetSize: mobileOptimizer.getTouchTargetSize.bind(mobileOptimizer),
    getFormConfig: mobileOptimizer.getFormConfig.bind(mobileOptimizer),
    isMobileViewport: mobileOptimizer.isMobileViewport.bind(mobileOptimizer),
    getGridClasses: mobileOptimizer.getGridClasses.bind(mobileOptimizer)
  };
};

export default mobileOptimizer;
