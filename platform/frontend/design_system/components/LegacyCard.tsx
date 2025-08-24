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
    <LegacyCard variant="problem" className={className}>
      <div className="text-blue-500 text-4xl mb-4">{emoji}</div>
      <h3 className="text-xl font-bold text-gray-900 mb-4">{title}</h3>
      <p className="text-gray-700 mb-4">"{quote}"</p>
      <div className="text-blue-600 font-semibold text-sm">{attribution}</div>
    </LegacyCard>
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