'use client';

/**
 * Optimized Image Component
 * =========================
 * Performance-optimized image component with WebP support,
 * lazy loading, and accessibility improvements
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useLazyLoading, getOptimizedImageSrc } from '../../shared_components/utils/performance';

export interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number | string;
  height?: number | string;
  priority?: boolean; // For above-the-fold images
  placeholder?: 'blur' | 'empty';
  quality?: number;
  sizes?: string;
  onLoad?: () => void;
  onError?: () => void;
  style?: React.CSSProperties;
  loading?: 'lazy' | 'eager';
  decoding?: 'async' | 'sync' | 'auto';
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  className = '',
  width,
  height,
  priority = false,
  placeholder = 'empty',
  quality = 85,
  sizes,
  onLoad,
  onError,
  style,
  loading = 'lazy',
  decoding = 'async'
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState<string>('');
  const { isIntersecting, setElement } = useLazyLoading();
  const imgRef = useRef<HTMLImageElement>(null);

  // Set up intersection observer for lazy loading
  useEffect(() => {
    if (imgRef.current) {
      setElement(imgRef.current);
    }
  }, [setElement]);

  // Load image when it comes into view or if priority is true
  useEffect(() => {
    if (priority || isIntersecting) {
      // Try to load optimized format first
      const webpSrc = getOptimizedImageSrc(src, 'webp');
      const avifSrc = getOptimizedImageSrc(src, 'avif');
      
      // Create a picture element to test format support
      const img = new Image();
      
      // Try AVIF first, then WebP, then original
      img.onload = () => {
        setCurrentSrc(avifSrc !== src ? avifSrc : webpSrc !== src ? webpSrc : src);
      };
      
      img.onerror = () => {
        // AVIF failed, try WebP
        const webpImg = new Image();
        webpImg.onload = () => setCurrentSrc(webpSrc);
        webpImg.onerror = () => setCurrentSrc(src);
        webpImg.src = webpSrc;
      };
      
      img.src = avifSrc;
    }
  }, [priority, isIntersecting, src]);

  const handleLoad = () => {
    setIsLoaded(true);
    setHasError(false);
    if (onLoad) onLoad();
  };

  const handleError = () => {
    setHasError(true);
    if (onError) onError();
    
    // Fallback to original source if optimized version fails
    if (currentSrc !== src) {
      setCurrentSrc(src);
    }
  };

  // Generate responsive sizes if not provided
  const responsiveSizes = sizes || '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw';

  // Placeholder styles
  const placeholderStyle: React.CSSProperties = {
    backgroundColor: placeholder === 'blur' ? '#f3f4f6' : 'transparent',
    backgroundImage: placeholder === 'blur' 
      ? 'linear-gradient(45deg, #f9fafb 25%, transparent 25%), linear-gradient(-45deg, #f9fafb 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f9fafb 75%), linear-gradient(-45deg, transparent 75%, #f9fafb 75%)'
      : undefined,
    backgroundSize: placeholder === 'blur' ? '20px 20px' : undefined,
    backgroundPosition: placeholder === 'blur' ? '0 0, 0 10px, 10px -10px, -10px 0px' : undefined,
    filter: !isLoaded && placeholder === 'blur' ? 'blur(10px)' : undefined,
    transition: 'filter 0.3s ease-out, opacity 0.3s ease-out',
    opacity: isLoaded ? 1 : (placeholder === 'blur' ? 0.6 : 1)
  };

  const combinedStyle = {
    ...placeholderStyle,
    ...style
  };

  // Error fallback
  if (hasError) {
    return (
      <div 
        className={`flex items-center justify-center bg-gray-100 text-gray-400 ${className}`}
        style={{ width, height, ...style }}
        role="img"
        aria-label={`Failed to load image: ${alt}`}
      >
        <svg 
          className="w-8 h-8" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
          />
        </svg>
      </div>
    );
  }

  return (
    <picture className={className}>
      {/* AVIF source for modern browsers */}
      {currentSrc && currentSrc.endsWith('.avif') && (
        <source srcSet={currentSrc} type="image/avif" sizes={responsiveSizes} />
      )}
      
      {/* WebP source for browsers that support it */}
      {currentSrc && (currentSrc.endsWith('.webp') || currentSrc === getOptimizedImageSrc(src, 'webp')) && (
        <source srcSet={getOptimizedImageSrc(src, 'webp')} type="image/webp" sizes={responsiveSizes} />
      )}
      
      {/* Fallback image */}
      <img
        ref={imgRef}
        src={currentSrc || (priority ? src : undefined)}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : loading}
        decoding={decoding}
        onLoad={handleLoad}
        onError={handleError}
        style={combinedStyle}
        sizes={responsiveSizes}
        // Accessibility improvements
        role="img"
        aria-describedby={alt ? undefined : 'image-no-description'}
      />
      
      {/* Hidden description for screen readers if alt is insufficient */}
      {!alt && (
        <span id="image-no-description" className="sr-only">
          Decorative image
        </span>
      )}
    </picture>
  );
};
