/**
 * TaxPoynt Legacy Card Component
 * ==============================
 * Extracted and enhanced from legacy/frontend/components/ui/Card.tsx
 * Provides consistent card styling across the new platform
 */

import React, { HTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Legacy card variants using class-variance-authority
const legacyCardVariants = cva(
  // Base styles matching legacy Card.tsx exactly
  "bg-white border border-gray-200 rounded-lg shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-1",
  {
    variants: {
      variant: {
        // Standard card (default)
        default: "p-4",
        
        // Compact card for mobile/dense layouts
        compact: "p-3 xs:p-4",
        
        // Spacious card for hero/featured content
        spacious: "p-6 xs:p-8",
        
        // Elevated card with stronger shadow
        elevated: "p-4 shadow-md border-none hover:shadow-lg",
        
        // Interactive card with enhanced hover effects
        interactive: "p-4 cursor-pointer hover:shadow-lg hover:-translate-y-2 hover:border-blue-200",
        
        // Status card with left border indicator
        status: "p-4 border-l-4",
        
        // Problem card specifically for our Problems section
        problem: "p-6 bg-white rounded-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-200 border border-gray-200",
      },
      size: {
        default: "w-full",
        sm: "max-w-sm",
        md: "max-w-md", 
        lg: "max-w-lg",
        xl: "max-w-xl",
        full: "w-full",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface LegacyCardProps 
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof legacyCardVariants> {
  loading?: boolean;
  statusColor?: 'primary' | 'success' | 'warning' | 'error';
  emoji?: string;
}

const LegacyCard = forwardRef<HTMLDivElement, LegacyCardProps>(
  ({ className, variant, size, loading = false, statusColor, emoji, children, ...props }, ref) => {
    const statusBorderColor = statusColor ? {
      primary: 'border-l-blue-500',
      success: 'border-l-green-500', 
      warning: 'border-l-yellow-500',
      error: 'border-l-red-500',
    }[statusColor] : '';

    const cardClass = legacyCardVariants({ 
      variant, 
      size, 
      className: `${loading ? 'animate-pulse' : ''} ${
        variant === 'status' && statusBorderColor ? statusBorderColor : ''
      } ${className || ''}` 
    });

    return (
      <div
        className={cardClass}
        ref={ref}
        {...props}
      >
        {emoji && (
          <div className="text-blue-500 text-4xl mb-4">
            {emoji}
          </div>
        )}
        {children}
      </div>
    );
  }
);
LegacyCard.displayName = "LegacyCard";

// Legacy Card Header component
interface LegacyCardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const LegacyCardHeader = forwardRef<
  HTMLDivElement, 
  LegacyCardHeaderProps
>(({ className, title, subtitle, action, children, ...props }, ref) => (
  <div
    ref={ref}
    className={`flex flex-col space-y-1.5 pb-4 ${className || ''}`}
    {...props}
  >
    {title && <LegacyCardTitle>{title}</LegacyCardTitle>}
    {subtitle && <LegacyCardDescription>{subtitle}</LegacyCardDescription>}
    {action && (
      <div className="mt-2">
        {action}
      </div>
    )}
    {children}
  </div>
));
LegacyCardHeader.displayName = "LegacyCardHeader";

// Legacy Card Title component
const LegacyCardTitle = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={`font-semibold text-xl text-gray-900 ${className || ''}`}
    {...props}
  />
));
LegacyCardTitle.displayName = "LegacyCardTitle";

// Legacy Card Description component
const LegacyCardDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={`text-sm text-gray-600 ${className || ''}`}
    {...props}
  />
));
LegacyCardDescription.displayName = "LegacyCardDescription";

// Legacy Card Content component
const LegacyCardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={`py-2 ${className || ''}`} {...props} />
));
LegacyCardContent.displayName = "LegacyCardContent";

// Legacy Card Footer component
const LegacyCardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`flex items-center pt-4 ${className || ''}`}
    {...props}
  />
));
LegacyCardFooter.displayName = "LegacyCardFooter";

// Problem Card - specialized for our Problems section
interface ProblemCardProps {
  emoji: string;
  title: string;
  quote: string;
  attribution: string;
  className?: string;
}

export const ProblemCard: React.FC<ProblemCardProps> = ({
  emoji,
  title,
  quote,
  attribution,
  className = '',
}) => {
  return (
    <div className={`group relative p-8 bg-gradient-to-br from-white via-gray-50/50 to-white rounded-2xl 
                    shadow-xl hover:shadow-2xl hover:shadow-slate-500/10 
                    transition-all duration-300 hover:-translate-y-1 
                    cursor-pointer border border-gray-200/50 hover:border-slate-300/50 
                    backdrop-blur-sm ${className}`}
         style={{
           background: 'linear-gradient(135deg, #ffffff 0%, #fafafa 50%, #ffffff 100%)',
           boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
         }}>
      
      {/* Premium Background Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50/20 via-transparent to-gray-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Subtle Pattern Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-gray-50/30 rounded-2xl"></div>
      
      {/* Content */}
      <div className="relative z-10">
        {/* Enhanced Emoji */}
        <div className="mb-6 transform group-hover:scale-105 transition-transform duration-200">
          <div className="w-16 h-16 bg-gradient-to-br from-slate-500/10 to-gray-500/10 rounded-2xl 
                          flex items-center justify-center text-5xl group-hover:shadow-lg 
                          transition-all duration-300 border border-slate-100/50"
               style={{
                 background: 'linear-gradient(135deg, rgba(100, 116, 139, 0.1) 0%, rgba(148, 163, 184, 0.1) 100%)',
                 backdropFilter: 'blur(10px)'
               }}>
            {emoji}
          </div>
        </div>
        
        {/* Enhanced Title */}
        <h3 className="text-2xl md:text-3xl font-black text-blue-900 mb-6 leading-tight group-hover:text-blue-700 transition-colors duration-300"
            style={{ 
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased',
              fontWeight: 900,
              textShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
          {title}
        </h3>
        
        {/* Enhanced Quote */}
        <div className="relative mb-8">
          {/* Quote decoration */}
          <div className="absolute -left-2 -top-2 text-6xl text-slate-200/40 font-bold leading-none">"</div>
          <p className="text-lg md:text-xl text-slate-600 leading-relaxed relative z-10 italic group-hover:text-slate-700 transition-colors duration-300"
             style={{ 
               textRendering: 'optimizeLegibility', 
               WebkitFontSmoothing: 'antialiased',
               lineHeight: '1.6'
             }}>
            {quote}
          </p>
          <div className="absolute -right-2 -bottom-2 text-6xl text-slate-200/40 font-bold leading-none">"</div>
        </div>
        
        {/* Enhanced Attribution */}
        <div className="relative">
          <div className="h-px bg-gradient-to-r from-transparent via-slate-200/50 to-transparent mb-4"></div>
          <div className="text-green-600 font-bold text-base tracking-wide group-hover:text-green-700 transition-colors duration-300"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 1px 2px rgba(100, 116, 139, 0.1)'
               }}>
            — {attribution}
          </div>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-slate-500/5 to-gray-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
    </div>
  );
};

export { 
  LegacyCard, 
  LegacyCardHeader, 
  LegacyCardTitle, 
  LegacyCardDescription, 
  LegacyCardContent, 
  LegacyCardFooter 
};