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

interface LegacyCardProps 
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

const ProblemCard: React.FC<ProblemCardProps> = ({
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
        
        {/* Challenge Category Badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-slate-100/80 text-slate-700 text-xs font-bold rounded-full border border-slate-200/50">
            Enterprise Challenge
          </span>
        </div>
        
        {/* Enhanced Title */}
        <h3 className="text-2xl md:text-3xl font-black text-slate-900 mb-6 leading-tight group-hover:text-slate-800 transition-colors duration-300"
            style={{ 
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased',
              fontWeight: 900,
              textShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
          {title}
        </h3>
        
        {/* Enhanced Quote */}
        <div className="relative mb-6">
          {/* Quote decoration */}
          <div className="absolute -left-2 -top-2 text-6xl text-slate-200/40 font-bold leading-none">"</div>
          <p className="text-lg md:text-xl text-slate-700 leading-relaxed relative z-10 italic group-hover:text-slate-800 transition-colors duration-300"
             style={{ 
               textRendering: 'optimizeLegibility', 
               WebkitFontSmoothing: 'antialiased',
               lineHeight: '1.6'
             }}>
            {quote}
          </p>
          <div className="absolute -right-2 -bottom-2 text-6xl text-slate-200/40 font-bold leading-none">"</div>
        </div>
        
        {/* Problem Impact Badge */}
        <div className="mb-6">
          <div className="inline-block px-4 py-2 bg-gradient-to-r from-slate-500 to-gray-500 text-white rounded-full text-sm font-bold shadow-lg">
            Critical Enterprise Pain Point
          </div>
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

// Solution Card - specialized for our Solutions section
interface SolutionCardProps {
  emoji: string;
  title: string;
  problem: string;
  quote: string;
  attribution: string;
  metrics: string;
  className?: string;
}

const SolutionCard: React.FC<SolutionCardProps> = ({
  emoji,
  title,
  problem,
  quote,
  attribution,
  metrics,
  className = '',
}) => {
  return (
    <div className={`group relative p-8 bg-gradient-to-br from-green-50 via-white to-emerald-50/50 rounded-2xl 
                    shadow-xl hover:shadow-2xl hover:shadow-green-500/10 
                    transition-all duration-300 hover:-translate-y-1 
                    cursor-pointer border border-green-200/50 hover:border-green-300/50 
                    backdrop-blur-sm ${className}`}
         style={{
           background: 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 50%, #ecfdf5 100%)',
           boxShadow: '0 10px 25px -5px rgba(34, 197, 94, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
         }}>
      
      {/* Premium Background Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-50/20 via-transparent to-emerald-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Subtle Pattern Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-green-50/30 rounded-2xl"></div>
      
      {/* Content */}
      <div className="relative z-10">
        {/* Enhanced Emoji */}
        <div className="mb-6 transform group-hover:scale-105 transition-transform duration-200">
          <div className="w-16 h-16 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-2xl 
                          flex items-center justify-center text-5xl group-hover:shadow-lg 
                          transition-all duration-300 border border-green-100/50"
               style={{
                 background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
                 backdropFilter: 'blur(10px)'
               }}>
            {emoji}
          </div>
        </div>
        
        {/* Problem Reference Badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-green-100/80 text-green-700 text-xs font-bold rounded-full border border-green-200/50">
            Solves: {problem}
          </span>
        </div>
        
        {/* Enhanced Title */}
        <h3 className="text-2xl md:text-3xl font-black text-green-900 mb-6 leading-tight group-hover:text-green-800 transition-colors duration-300"
            style={{ 
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased',
              fontWeight: 900,
              textShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
          {title}
        </h3>
        
        {/* Enhanced Quote */}
        <div className="relative mb-6">
          {/* Quote decoration */}
          <div className="absolute -left-2 -top-2 text-6xl text-green-200/40 font-bold leading-none">"</div>
          <p className="text-lg md:text-xl text-slate-700 leading-relaxed relative z-10 italic group-hover:text-slate-800 transition-colors duration-300"
             style={{ 
               textRendering: 'optimizeLegibility', 
               WebkitFontSmoothing: 'antialiased',
               lineHeight: '1.6'
             }}>
            {quote}
          </p>
          <div className="absolute -right-2 -bottom-2 text-6xl text-green-200/40 font-bold leading-none">"</div>
        </div>
        
        {/* Metrics Badge */}
        <div className="mb-6">
          <div className="inline-block px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full text-sm font-bold shadow-lg">
            {metrics}
          </div>
        </div>
        
        {/* Enhanced Attribution */}
        <div className="relative">
          <div className="h-px bg-gradient-to-r from-transparent via-green-200/50 to-transparent mb-4"></div>
          <div className="text-green-600 font-bold text-base tracking-wide group-hover:text-green-700 transition-colors duration-300"
               style={{ 
                 textRendering: 'optimizeLegibility', 
                 WebkitFontSmoothing: 'antialiased',
                 textShadow: '0 1px 2px rgba(34, 197, 94, 0.1)'
               }}>
            — {attribution}
          </div>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
    </div>
  );
};

// Feature Card - specialized for our Features section
interface FeatureCardProps {
  category: string;
  icon: string;
  title: string;
  description: string;
  capabilities: string[];
  metrics: {
    label: string;
    value: string;
    detail: string;
  };
  className?: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  category,
  icon,
  title,
  description,
  capabilities,
  metrics,
  className = '',
}) => {
  return (
    <div className={`group relative p-8 bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 rounded-2xl 
                    shadow-xl hover:shadow-2xl hover:shadow-slate-500/10 
                    transition-all duration-300 hover:-translate-y-1 
                    cursor-pointer border border-slate-200/50 hover:border-indigo-300/50 
                    backdrop-blur-sm overflow-hidden ${className}`}
         style={{
           background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 50%, #eef2ff 100%)',
           boxShadow: '0 10px 25px -5px rgba(71, 85, 105, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
         }}>
      
      {/* Premium Background Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/20 via-transparent to-slate-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Subtle Pattern Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-slate-50/30 rounded-2xl"></div>
      
      {/* Content */}
      <div className="relative z-10">
        {/* Category Badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-indigo-100/80 text-indigo-700 text-xs font-bold rounded-full border border-indigo-200/50">
            {category}
          </span>
        </div>
        
        {/* Enhanced Icon */}
        <div className="mb-6 transform group-hover:scale-105 transition-transform duration-200">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-500/10 to-slate-500/10 rounded-2xl 
                          flex items-center justify-center text-5xl group-hover:shadow-lg 
                          transition-all duration-300 border border-indigo-100/50"
               style={{
                 background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(71, 85, 105, 0.1) 100%)',
                 backdropFilter: 'blur(10px)'
               }}>
            {icon}
          </div>
        </div>
        
        {/* Enhanced Title */}
        <h3 className="text-2xl md:text-3xl font-black text-slate-900 mb-4 leading-tight group-hover:text-indigo-900 transition-colors duration-300"
            style={{ 
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased',
              fontWeight: 900,
              textShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
          {title}
        </h3>
        
        {/* Description */}
        <p className="text-lg text-slate-600 leading-relaxed mb-6 group-hover:text-slate-700 transition-colors duration-300"
           style={{ 
             textRendering: 'optimizeLegibility', 
             WebkitFontSmoothing: 'antialiased',
             lineHeight: '1.6'
           }}>
          {description}
        </p>
        
        {/* Capabilities List */}
        <div className="mb-6">
          <div className="space-y-3">
            {capabilities.map((capability, index) => (
              <div key={index} className="flex items-start gap-3">
                <span className="w-3 h-3 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: '#4f46e5' }}></span>
                <span className="text-slate-700 leading-relaxed group-hover:text-slate-800 transition-colors duration-300"
                      style={{ 
                        textRendering: 'optimizeLegibility', 
                        WebkitFontSmoothing: 'antialiased'
                      }}>
                  {capability}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Metrics Badge */}
        <div className="mb-4">
          <div className="bg-gradient-to-r from-indigo-50 to-slate-50 rounded-xl p-4 border border-indigo-100/50">
            <div className="text-xs font-bold text-indigo-600 mb-1">{metrics.label}</div>
            <div className="text-xl font-black text-indigo-900 mb-1">{metrics.value}</div>
            <div className="text-sm text-slate-600">{metrics.detail}</div>
          </div>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/5 to-slate-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
    </div>
  );
};

// Before/After Card - specialized for transformation comparison
interface BeforeAfterCardProps {
  metric: string;
  before: {
    value: string;
    description: string;
    painPoints: string[];
  };
  after: {
    value: string;
    description: string;
    benefits: string[];
  };
  improvement: string;
  category: string;
  className?: string;
}

const BeforeAfterCard: React.FC<BeforeAfterCardProps> = ({
  metric,
  before,
  after,
  improvement,
  category,
  className = '',
}) => {
  return (
    <div className={`group relative bg-gradient-to-br from-purple-50 via-white to-violet-50/30 rounded-2xl 
                    shadow-xl hover:shadow-2xl hover:shadow-purple-500/10 
                    transition-all duration-300 hover:-translate-y-1 
                    cursor-pointer border border-purple-200/50 hover:border-purple-300/50 
                    backdrop-blur-sm overflow-hidden ${className}`}
         style={{
           background: 'linear-gradient(135deg, #faf5ff 0%, #ffffff 50%, #f3e8ff 100%)',
           boxShadow: '0 10px 25px -5px rgba(147, 51, 234, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
         }}>
      
      {/* Premium Background Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50/20 via-transparent to-violet-50/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Content */}
      <div className="relative z-10 p-8">
        {/* Category Badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-purple-100/80 text-purple-700 text-xs font-bold rounded-full border border-purple-200/50">
            {category}
          </span>
        </div>
        
        {/* Metric Title */}
        <h3 className="text-xl md:text-2xl font-black text-purple-900 mb-6 leading-tight group-hover:text-purple-800 transition-colors duration-300"
            style={{ 
              textRendering: 'optimizeLegibility', 
              WebkitFontSmoothing: 'antialiased',
              fontWeight: 900,
              textShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
          {metric}
        </h3>
        
        {/* Before/After Comparison */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Before Section */}
          <div className="relative">
            {/* Before Header */}
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-white text-sm font-bold">❌</span>
              </div>
              <span className="text-red-700 font-bold text-sm uppercase tracking-wide">Before TaxPoynt</span>
            </div>
            
            {/* Before Value */}
            <div className="text-2xl font-black text-red-800 mb-2">{before.value}</div>
            <p className="text-sm text-slate-600 mb-3">{before.description}</p>
            
            {/* Pain Points */}
            <div className="space-y-1">
              {before.painPoints.slice(0, 2).map((point, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-xs text-slate-600 leading-tight">{point}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* After Section */}
          <div className="relative">
            {/* After Header */}
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-white text-sm font-bold">✅</span>
              </div>
              <span className="text-green-700 font-bold text-sm uppercase tracking-wide">With TaxPoynt</span>
            </div>
            
            {/* After Value */}
            <div className="text-2xl font-black text-green-800 mb-2">{after.value}</div>
            <p className="text-sm text-slate-600 mb-3">{after.description}</p>
            
            {/* Benefits */}
            <div className="space-y-1">
              {after.benefits.slice(0, 2).map((benefit, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                  <span className="text-xs text-slate-600 leading-tight">{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Transformation Arrow */}
        <div className="flex items-center justify-center mb-4">
          <div className="bg-gradient-to-r from-purple-500 to-violet-500 text-white px-6 py-2 rounded-full text-sm font-bold shadow-lg">
            {improvement}
          </div>
        </div>
        
        {/* Divider */}
        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-purple-200/50"></div>
          </div>
          <div className="relative flex justify-center">
            <div className="bg-white px-3">
              <span className="text-purple-400 text-sm">●</span>
            </div>
          </div>
        </div>
        
        {/* Call to Action */}
        <div className="text-center">
          <p className="text-sm text-purple-700 font-medium">
            See this transformation in your business
          </p>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/5 to-violet-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
    </div>
  );
};

// Pricing Card - specialized for service packages
interface PricingCardProps {
  id: string;
  name: string;
  subtitle: string;
  description: string;
  price: {
    monthly: number;
    annual: number;
  };
  originalAnnual: number;
  badge?: string | null;
  features: string[];
  limits: {
    invoicesPerMonth: number | 'unlimited';
    integrations: number | 'unlimited';
    users: number | 'unlimited';
    storage: string;
  };
  ideal: string;
  color: 'blue' | 'green' | 'purple' | 'indigo';
  billingCycle: 'monthly' | 'annual';
  onSelectPackage: (packageId: string) => void;
  className?: string;
}

const PricingCard: React.FC<PricingCardProps> = ({
  id,
  name,
  subtitle,
  description,
  price,
  originalAnnual,
  badge,
  features,
  limits,
  ideal,
  color,
  billingCycle,
  onSelectPackage,
  className = '',
}) => {
  const colorThemes = {
    blue: {
      gradient: 'from-blue-50 via-white to-indigo-50/30',
      border: 'border-blue-200/50 hover:border-blue-300/50',
      shadow: 'hover:shadow-blue-500/10',
      badge: 'from-blue-500 to-indigo-500',
      text: 'text-blue-900',
      dot: '#1e40af',
      background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #eef2ff 100%)'
    },
    green: {
      gradient: 'from-green-50 via-white to-emerald-50/30',
      border: 'border-green-200/50 hover:border-green-300/50',
      shadow: 'hover:shadow-green-500/10',
      badge: 'from-green-500 to-emerald-500',
      text: 'text-green-900',
      dot: '#166534',
      background: 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 50%, #ecfdf5 100%)'
    },
    purple: {
      gradient: 'from-purple-50 via-white to-violet-50/30',
      border: 'border-purple-200/50 hover:border-purple-300/50',
      shadow: 'hover:shadow-purple-500/10',
      badge: 'from-purple-500 to-violet-500',
      text: 'text-purple-900',
      dot: '#6b21a8',
      background: 'linear-gradient(135deg, #faf5ff 0%, #ffffff 50%, #f3e8ff 100%)'
    },
    indigo: {
      gradient: 'from-indigo-50 via-white to-slate-50/30',
      border: 'border-indigo-200/50 hover:border-indigo-300/50',
      shadow: 'hover:shadow-indigo-500/10',
      badge: 'from-indigo-500 to-slate-500',
      text: 'text-indigo-900',
      dot: '#3730a3',
      background: 'linear-gradient(135deg, #eef2ff 0%, #ffffff 50%, #f8fafc 100%)'
    }
  };

  const theme = colorThemes[color];
  const primaryPrice = price.monthly;  // Always show monthly as primary
  const secondaryPrice = price.annual;
  const savings = originalAnnual - price.annual;
  const savingsPercentage = Math.round((savings / originalAnnual) * 100);

  const formatPrice = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className={`group relative bg-gradient-to-br ${theme.gradient} rounded-2xl 
                    shadow-xl hover:shadow-2xl ${theme.shadow} 
                    transition-all duration-300 hover:-translate-y-1 
                    cursor-pointer border ${theme.border} 
                    backdrop-blur-sm ${className} ${
                      badge === 'Most Popular' ? 'ring-2 ring-green-500 ring-opacity-50 scale-105' : ''
                    } ${
                      badge === 'Recommended' ? 'ring-2 ring-purple-500 ring-opacity-50' : ''
                    } h-[900px] flex flex-col`}
         style={{
           background: theme.background,
           boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.5)'
         }}>
      
      {/* Premium Background Overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${theme.gradient.replace('via-white', 'via-transparent')} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>
      
      {/* Badge */}
      {badge && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className={`bg-gradient-to-r ${theme.badge} text-white px-6 py-3 rounded-full text-sm font-bold shadow-xl border-2 border-white`}>
            {badge}
          </div>
        </div>
      )}
      
      {/* Content - Flexible container */}
      <div className="relative z-10 p-8 pt-20 pb-8 flex flex-col flex-grow">
        {/* Header - Fixed height section */}
        <div className="text-center mb-6 h-24 flex flex-col justify-center">
          <h3 className={`text-xl md:text-2xl font-black ${theme.text} mb-1 leading-tight group-hover:opacity-90 transition-colors duration-300`}
              style={{ 
                textRendering: 'optimizeLegibility', 
                WebkitFontSmoothing: 'antialiased',
                fontWeight: 900,
                textShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}>
            {name}
          </h3>
          <p className="text-sm font-semibold text-slate-600 mb-1">{subtitle}</p>
          <p className="text-xs text-slate-600 leading-tight line-clamp-2">{description}</p>
        </div>
        
        {/* Pricing - Fixed height section */}
        <div className="text-center mb-6 h-28 flex flex-col justify-center">
          {/* Primary Price (Monthly) */}
          <div className="flex items-center justify-center mb-1">
            <span className={`text-3xl md:text-4xl font-black ${theme.text}`}
                  style={{ fontWeight: 950 }}>
              {formatPrice(primaryPrice)}
            </span>
          </div>
          <div className="text-xs text-slate-600 font-semibold mb-2">
            /month
          </div>
          
          {/* Secondary Price (Annual) */}
          <div className="text-center">
            <div className="text-sm text-slate-500 mb-1">
              or {formatPrice(secondaryPrice)}/year
            </div>
            <div className="inline-block px-2 py-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs font-bold rounded-full shadow-lg">
              Save {savingsPercentage}%
            </div>
          </div>
        </div>
        
        {/* Features - Controlled flexible section */}
        <div className="flex-grow mb-6 min-h-[200px] max-h-[250px] overflow-hidden">
          <h4 className="font-bold text-slate-900 mb-3 text-sm">What's included:</h4>
          <div className="space-y-2">
            {features.slice(0, 8).map((feature, index) => (
              <div key={index} className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: theme.dot }}></span>
                <span className="text-slate-700 leading-tight text-xs line-clamp-2"
                      style={{ 
                        textRendering: 'optimizeLegibility', 
                        WebkitFontSmoothing: 'antialiased'
                      }}>
                  {feature}
                </span>
              </div>
            ))}
            {features.length > 8 && (
              <div className="text-center mt-2">
                <span className="text-xs text-slate-500 font-medium">+ {features.length - 8} more features</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Bottom section - stays at bottom */}
        <div className="mt-auto h-[320px] flex flex-col justify-end">
          {/* Limits */}
          <div className={`bg-gradient-to-r ${theme.gradient.replace('via-white', 'via-gray-50/50')} rounded-lg p-3 mb-4 border border-gray-100/50`}>
            <h4 className="font-bold text-slate-900 mb-2 text-xs">Usage limits:</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="text-center">
                <strong className="text-xs">{limits.invoicesPerMonth === 'unlimited' ? '∞' : `${limits.invoicesPerMonth}`}</strong>
                <div className="text-xs">invoices/mo</div>
              </div>
              <div className="text-center">
                <strong className="text-xs">{limits.integrations === 'unlimited' ? '∞' : limits.integrations}</strong>
                <div className="text-xs">integrations</div>
              </div>
              <div className="text-center">
                <strong className="text-xs">{limits.users === 'unlimited' ? '∞' : limits.users}</strong>
                <div className="text-xs">users</div>
              </div>
              <div className="text-center">
                <strong className="text-xs">{limits.storage}</strong>
                <div className="text-xs">storage</div>
              </div>
            </div>
          </div>
          
          {/* Ideal For */}
          <div className="mb-4">
            <div className={`bg-gradient-to-r ${theme.badge} bg-opacity-10 rounded-lg p-3`}>
              <h4 className="font-bold text-slate-900 mb-1 text-xs">Ideal for:</h4>
              <p className="text-xs text-slate-600 line-clamp-2">{ideal}</p>
            </div>
          </div>
          
          {/* CTA Button */}
          <div className="text-center mb-3">
            <button
              onClick={() => onSelectPackage(id)}
              className={`w-full py-3 px-4 bg-gradient-to-r ${theme.badge} hover:opacity-90 text-white font-bold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 transform text-sm`}
              style={{
                textRendering: 'optimizeLegibility',
                WebkitFontSmoothing: 'antialiased'
              }}
            >
              Get Started with {name}
            </button>
            
            <p className="text-xs text-slate-500 mt-3 mb-4">30-day money back guarantee</p>
          </div>
        </div>
      </div>
      
      {/* Hover Glow Effect */}
      <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${theme.gradient.replace('via-white', 'via-transparent')} opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none`}></div>
    </div>
  );
};

export { 
  LegacyCard, 
  LegacyCardHeader, 
  LegacyCardTitle, 
  LegacyCardDescription, 
  LegacyCardContent, 
  LegacyCardFooter,
  ProblemCard,
  SolutionCard,
  FeatureCard,
  BeforeAfterCard,
  PricingCard,
  type LegacyCardProps 
};