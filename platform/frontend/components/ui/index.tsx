'use client';

/**
 * TaxPoynt Unified UI Components
 * ===============================
 * 
 * Professional UI component bridge that maps '@/components/ui' imports 
 * to TaxPoynt's sophisticated existing component ecosystem.
 * 
 * This system leverages:
 * - design_system/components - Enterprise role-aware Button & Input
 * - shared_components - Nigerian business forms, charts, navigation 
 * - Legacy battle-tested components - 40+ production-ready UI elements
 * 
 * Features:
 * - Role-based theming (SI, APP, Hybrid, Admin)
 * - Nigerian business context (validation, forms)
 * - Enterprise accessibility standards
 * - Professional micro-interactions
 * 
 * @author TaxPoynt Development Team
 * @version 2.0.0 - Unified Architecture
 */

import React, { useEffect, useState } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';
import { Button } from '../../design_system/components/Button';
import { Input } from '../../design_system/components/Input';
import { Select } from '../../shared_components/forms/Select';

// ========================================
// CORE FORM COMPONENTS
// ========================================

// Import existing sophisticated components
export { Button };

export { Input, inputVariants } from '../../design_system/components/Input';
export type { InputProps } from '../../design_system/components/Input';

export { Select } from '../../shared_components/forms/Select';
export type { SelectProps, SelectOption } from '../../shared_components/forms/Select';

// ========================================
// EXTENDED FORM COMPONENTS
// ========================================

// Textarea component with role-aware theming
const textareaVariants = cva(
  [
    'w-full rounded-md border transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'placeholder:text-gray-400 resize-vertical min-h-[80px]'
  ],
  {
    variants: {
      variant: {
        default: [
          'border-gray-300 bg-white text-gray-900',
          'focus:border-blue-500 focus:ring-blue-500',
          'hover:border-gray-400'
        ],
        filled: [
          'border-gray-200 bg-gray-50 text-gray-900',
          'focus:border-blue-500 focus:ring-blue-500 focus:bg-white'
        ]
      },
      size: {
        sm: 'px-3 py-2 text-sm',
        md: 'px-3 py-3 text-sm', 
        lg: 'px-4 py-4 text-base'
      },
      role: {
        si: '',
        app: '',
        hybrid: '',
        admin: ''
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      role: 'si'
    },
    compoundVariants: [
      { variant: 'default', role: 'app', class: 'focus:border-green-600 focus:ring-green-600' },
      { variant: 'default', role: 'hybrid', class: 'focus:border-indigo-500 focus:ring-indigo-500' },
      { variant: 'default', role: 'admin', class: 'focus:border-purple-500 focus:ring-purple-500' }
    ]
  }
);

export interface TextareaProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size' | 'role'>,
    VariantProps<typeof textareaVariants> {}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant, size, role, ...props }, ref) => (
    <textarea
      className={clsx(textareaVariants({ variant, size, role }), className)}
      ref={ref}
      {...props}
    />
  )
);
Textarea.displayName = 'Textarea';

// Switch component
export interface SwitchProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: 'sm' | 'md' | 'lg';
  role?: 'si' | 'app' | 'hybrid' | 'admin';
}

export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, size = 'md', role = 'si', ...props }, ref) => {
    const sizeClasses = {
      sm: 'h-4 w-7',
      md: 'h-5 w-9', 
      lg: 'h-6 w-11'
    };

    const roleClasses = {
      si: 'bg-blue-600',
      app: 'bg-green-600',
      hybrid: 'bg-indigo-600',
      admin: 'bg-purple-600'
    };

    return (
      <label className="relative inline-flex cursor-pointer items-center">
        <input
          type="checkbox"
          className="sr-only peer"
          ref={ref}
          {...props}
        />
        <div className={clsx(
          'rounded-full bg-gray-200 transition-colors duration-200',
          'peer-checked:' + roleClasses[role],
          'peer-focus:ring-4 peer-focus:ring-blue-300',
          sizeClasses[size],
          className
        )}>
          <div className={clsx(
            'absolute top-0.5 left-0.5 bg-white rounded-full transition-transform duration-200',
            'peer-checked:translate-x-full',
            size === 'sm' && 'h-3 w-3',
            size === 'md' && 'h-4 w-4',
            size === 'lg' && 'h-5 w-5'
          )} />
        </div>
      </label>
    );
  }
);
Switch.displayName = 'Switch';

// Slider component 
export interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  size?: 'sm' | 'md' | 'lg';
  role?: 'si' | 'app' | 'hybrid' | 'admin';
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, size = 'md', role = 'si', ...props }, ref) => {
    const roleClasses = {
      si: 'accent-blue-600',
      app: 'accent-green-600', 
      hybrid: 'accent-indigo-600',
      admin: 'accent-purple-600'
    };

    return (
      <input
        type="range"
        className={clsx(
          'w-full appearance-none bg-gray-200 rounded-lg cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-blue-500',
          roleClasses[role],
          size === 'sm' && 'h-1',
          size === 'md' && 'h-2',
          size === 'lg' && 'h-3',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Slider.displayName = 'Slider';

// ========================================
// LAYOUT COMPONENTS  
// ========================================

// Card components
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-white border border-gray-200 rounded-lg',
      elevated: 'bg-white border border-gray-200 rounded-lg shadow-lg',
      outlined: 'bg-white border-2 border-gray-300 rounded-lg'
    };

    return (
      <div
        ref={ref}
        className={clsx(variants[variant], 'overflow-hidden', className)}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={clsx('p-6 pb-4', className)} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={clsx('text-lg font-semibold text-gray-900', className)} {...props} />
  )
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={clsx('text-sm text-gray-600 mt-1', className)} {...props} />
  )
);
CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={clsx('p-6 pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={clsx('p-6 pt-0 flex items-center', className)} {...props} />
  )
);
CardFooter.displayName = 'CardFooter';

// ========================================
// DIALOG COMPONENTS
// ========================================

export interface DialogProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const Dialog: React.FC<DialogProps> = ({ children, open, onOpenChange }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="fixed inset-0 bg-black bg-opacity-50" 
        onClick={() => onOpenChange?.(false)}
      />
      <div className="relative z-50">{children}</div>
    </div>
  );
};

export const DialogTrigger: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, ...props }) => (
  <div {...props}>{children}</div>
);

export const DialogContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        'bg-white rounded-lg shadow-xl p-6 w-full max-w-lg max-h-[85vh] overflow-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
DialogContent.displayName = 'DialogContent';

export const DialogHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={clsx('mb-4', className)} {...props} />
  )
);
DialogHeader.displayName = 'DialogHeader';

export const DialogTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h2 ref={ref} className={clsx('text-xl font-semibold text-gray-900', className)} {...props} />
  )
);
DialogTitle.displayName = 'DialogTitle';

export const DialogDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={clsx('text-sm text-gray-600', className)} {...props} />
  )
);
DialogDescription.displayName = 'DialogDescription';

// ========================================
// TABLE COMPONENTS
// ========================================

export const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <table ref={ref} className={clsx('w-full border-collapse', className)} {...props} />
  )
);
Table.displayName = 'Table';

export const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <thead ref={ref} className={clsx('bg-gray-50', className)} {...props} />
  )
);
TableHeader.displayName = 'TableHeader';

export const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className, ...props }, ref) => (
    <tbody ref={ref} className={clsx('divide-y divide-gray-200', className)} {...props} />
  )
);
TableBody.displayName = 'TableBody';

export const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr ref={ref} className={clsx('hover:bg-gray-50', className)} {...props} />
  )
);
TableRow.displayName = 'TableRow';

export const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th ref={ref} className={clsx('px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider', className)} {...props} />
  )
);
TableHead.displayName = 'TableHead';

export const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td ref={ref} className={clsx('px-6 py-4 whitespace-nowrap text-sm text-gray-900', className)} {...props} />
  )
);
TableCell.displayName = 'TableCell';

// ========================================
// SELECT COMPONENTS (Enhanced)
// ========================================

export const SelectItem: React.FC<{ value: string; children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

export const SelectContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => (
  <div className={clsx('absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg', className)} {...props}>
    {children}
  </div>
);

export const SelectTrigger: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className, ...props }) => (
  <div className={clsx('flex items-center justify-between px-3 py-2 border border-gray-300 rounded-md cursor-pointer', className)} {...props}>
    {children}
  </div>
);

export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => (
  <span className="text-gray-500">{placeholder}</span>
);

// ========================================
// FEEDBACK COMPONENTS
// ========================================

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    const variants = {
      default: 'bg-gray-100 text-gray-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800', 
      error: 'bg-red-100 text-red-800',
      info: 'bg-blue-100 text-blue-800'
    };

    const sizes = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-2.5 py-1.5 text-sm',
      lg: 'px-3 py-2 text-base'
    };

    return (
      <span
        ref={ref}
        className={clsx(
          'inline-flex items-center rounded-full font-medium',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);
Badge.displayName = 'Badge';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error';
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-blue-50 border-blue-200 text-blue-800',
      success: 'bg-green-50 border-green-200 text-green-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      error: 'bg-red-50 border-red-200 text-red-800'
    };

    return (
      <div
        ref={ref}
        className={clsx(
          'p-4 border rounded-lg',
          variants[variant],
          className
        )}
        {...props}
      />
    );
  }
);
Alert.displayName = 'Alert';

export const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={clsx('text-sm', className)} {...props} />
  )
);
AlertDescription.displayName = 'AlertDescription';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  role?: 'si' | 'app' | 'hybrid' | 'admin';
}

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, size = 'md', role = 'si', ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    
    const sizes = {
      sm: 'h-1',
      md: 'h-2', 
      lg: 'h-3'
    };

    const roleColors = {
      si: 'bg-blue-600',
      app: 'bg-green-600',
      hybrid: 'bg-indigo-600',
      admin: 'bg-purple-600'
    };

    return (
      <div
        ref={ref}
        className={clsx('w-full bg-gray-200 rounded-full overflow-hidden', sizes[size], className)}
        {...props}
      >
        <div
          className={clsx('h-full transition-all duration-300', roleColors[role])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  }
);
Progress.displayName = 'Progress';

// ========================================
// NAVIGATION COMPONENTS
// ========================================

// Tabs components
export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ 
  children, 
  defaultValue, 
  value, 
  onValueChange, 
  className, 
  ...props 
}) => {
  const [activeTab, setActiveTab] = useState(value ?? defaultValue ?? '');

  useEffect(() => {
    if (value !== undefined) {
      setActiveTab(value);
    }
  }, [value]);

  const handleTabChange = (newValue: string) => {
    setActiveTab(newValue);
    onValueChange?.(newValue);
  };

  return (
    <div className={clsx('tabs-container', className)} {...props}>
      {React.Children.map(children, child => 
        React.isValidElement(child) 
          ? React.cloneElement(child, { activeTab, onTabChange: handleTabChange })
          : child
      )}
    </div>
  );
};

export const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div 
      ref={ref}
      className={clsx(
        'flex space-x-1 rounded-lg bg-gray-100 p-1',
        className
      )} 
      {...props} 
    />
  )
);
TabsList.displayName = 'TabsList';

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  activeTab?: string;
  onTabChange?: (value: string) => void;
}

export const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, activeTab, onTabChange, children, ...props }, ref) => (
    <button
      ref={ref}
      className={clsx(
        'px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
        activeTab === value
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-600 hover:text-gray-900 hover:bg-white/50',
        className
      )}
      onClick={() => onTabChange?.(value)}
      {...props}
    >
      {children}
    </button>
  )
);
TabsTrigger.displayName = 'TabsTrigger';

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
  activeTab?: string;
}

export const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, activeTab, ...props }, ref) => {
    if (activeTab !== value) return null;

    return (
      <div
        ref={ref}
        className={clsx('mt-4', className)}
        {...props}
      />
    );
  }
);
TabsContent.displayName = 'TabsContent';

// ScrollArea component
export const ScrollArea = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('overflow-auto', className)}
      {...props}
    >
      {children}
    </div>
  )
);
ScrollArea.displayName = 'ScrollArea';

// Separator component
export const Separator = React.forwardRef<HTMLHRElement, React.HTMLAttributes<HTMLHRElement>>(
  ({ className, ...props }, ref) => (
    <hr
      ref={ref}
      className={clsx('border-0 bg-gray-200 h-px w-full', className)}
      {...props}
    />
  )
);
Separator.displayName = 'Separator';

// ========================================
// EXPORT ALL COMPONENTS
// ========================================

export const components = {
  // Form Components
  Button,
  Input, 
  Select,
  Textarea,
  Switch,
  Slider,
  
  // Layout Components
  Card,
  CardHeader,
  CardTitle,
  CardDescription, 
  CardContent,
  CardFooter,
  
  // Dialog Components
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  
  // Table Components
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  
  // Select Components
  SelectItem,
  SelectContent,
  SelectTrigger,
  SelectValue,
  
  // Navigation Components
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  ScrollArea,
  Separator,
  
  // Feedback Components
  Badge,
  Alert,
  AlertDescription,
  Progress
};

// Note: Individual exports are already handled above via the components object

export default components;
