/**
 * Enhanced Dashboard Card Component
 * =================================
 * Modern dashboard card using our refined design system
 */

import React from 'react';
import { LegacyCard, LegacyCardHeader, LegacyCardTitle, LegacyCardContent } from '../../design_system';
import { TYPOGRAPHY_STYLES, combineStyles, ACCESSIBILITY_PATTERNS } from '../../design_system/style-utilities';

export interface DashboardCardProps {
  title: string;
  description?: string;
  icon?: string;
  children?: React.ReactNode;
  badge?: string;
  badgeColor?: 'green' | 'blue' | 'purple' | 'orange' | 'red' | 'indigo' | 'emerald';
  onClick?: () => void;
  className?: string;
  variant?: 'default' | 'highlight' | 'warning' | 'success' | 'error';
}

const variantStyles = {
  default: {
    card: 'bg-white border-gray-200 hover:border-gray-300',
    title: 'text-slate-800',
    description: 'text-slate-600'
  },
  highlight: {
    card: 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 hover:border-blue-300',
    title: 'text-blue-800',
    description: 'text-blue-600'
  },
  warning: {
    card: 'bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200 hover:border-orange-300',
    title: 'text-orange-800',
    description: 'text-orange-600'
  },
  success: {
    card: 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 hover:border-green-300',
    title: 'text-green-800',
    description: 'text-green-600'
  },
  error: {
    card: 'bg-gradient-to-br from-red-50 to-pink-50 border-red-200 hover:border-red-300',
    title: 'text-red-800',
    description: 'text-red-600'
  }
};

const badgeColors = {
  green: 'bg-green-100 text-green-700 border-green-200',
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  purple: 'bg-purple-100 text-purple-700 border-purple-200',
  orange: 'bg-orange-100 text-orange-700 border-orange-200',
  red: 'bg-red-100 text-red-700 border-red-200',
  indigo: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200'
};

export const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  description,
  icon,
  children,
  badge,
  badgeColor = 'blue',
  onClick,
  className = '',
  variant = 'default'
}) => {
  const styles = variantStyles[variant];
  const isClickable = !!onClick;

  const cardStyle = combineStyles(
    TYPOGRAPHY_STYLES.optimizedText,
    {
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      transition: 'all 0.3s ease',
      cursor: isClickable ? 'pointer' : 'default'
    }
  );

  const cardContent = (
    <LegacyCard 
      className={`${styles.card} ${isClickable ? 'hover:shadow-xl hover:-translate-y-1' : ''} ${className}`}
      style={cardStyle}
      onClick={onClick}
      tabIndex={isClickable ? 0 : undefined}
      role={isClickable ? 'button' : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      } : undefined}
      {...(isClickable ? ACCESSIBILITY_PATTERNS.focusRing : {})}
    >
      <LegacyCardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            {icon && (
              <div className="flex-shrink-0">
                <span className="text-3xl">{icon}</span>
              </div>
            )}
            <div className="flex-1 min-w-0">
              <LegacyCardTitle 
                className={`${styles.title} font-bold text-lg leading-tight`}
                style={TYPOGRAPHY_STYLES.optimizedText}
              >
                {title}
              </LegacyCardTitle>
              {description && (
                <p 
                  className={`${styles.description} mt-1 text-sm leading-relaxed`}
                  style={TYPOGRAPHY_STYLES.optimizedText}
                >
                  {description}
                </p>
              )}
            </div>
          </div>
          
          {badge && (
            <span 
              className={`flex-shrink-0 px-3 py-1 text-xs font-bold rounded-full border ${badgeColors[badgeColor]}`}
            >
              {badge}
            </span>
          )}
        </div>
      </LegacyCardHeader>

      <LegacyCardContent className="pt-0">
        {children}
      </LegacyCardContent>
    </LegacyCard>
  );

  return cardContent;
};
