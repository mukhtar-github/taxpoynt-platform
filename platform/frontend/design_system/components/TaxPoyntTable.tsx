/**
 * TaxPoynt Table Component System
 * ===============================
 * Extracted from legacy Table.tsx - Complete table system for dashboards
 * Supports: Business interfaces, dashboard tables, mobile-responsive
 */

import React, { HTMLProps, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Table container variants from legacy
const taxPoyntTableContainerVariants = cva(
  "w-full overflow-x-auto",
  {
    variants: {
      variant: {
        default: "border border-gray-200 shadow-sm rounded-lg",
        bordered: "border border-gray-300",
        card: "border border-gray-200 bg-white shadow-md rounded-lg",
        minimal: "border-0",
        elevated: "shadow-lg rounded-lg border border-gray-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface TaxPoyntTableContainerProps
  extends HTMLProps<HTMLDivElement>,
    VariantProps<typeof taxPoyntTableContainerVariants> {}

const TaxPoyntTableContainer = forwardRef<HTMLDivElement, TaxPoyntTableContainerProps>(
  ({ className, variant, children, ...props }, ref) => {
    return (
      <div
        className={taxPoyntTableContainerVariants({ variant, className })}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }
);
TaxPoyntTableContainer.displayName = "TaxPoyntTableContainer";

// Main table component from legacy
export interface TaxPoyntTableProps extends HTMLProps<HTMLTableElement> {
  minWidth?: string;
  stickyHeader?: boolean;
}

const TaxPoyntTable = forwardRef<HTMLTableElement, TaxPoyntTableProps>(
  ({ className, minWidth = "600px", stickyHeader = false, ...props }, ref) => {
    return (
      <table
        ref={ref}
        className={`w-full border-collapse bg-white ${className || ''}`}
        style={{ minWidth }}
        {...props}
      />
    );
  }
);
TaxPoyntTable.displayName = "TaxPoyntTable";

// Table Header from legacy
const TaxPoyntTableHeader = forwardRef<
  HTMLTableSectionElement,
  HTMLProps<HTMLTableSectionElement> & { sticky?: boolean }
>(({ className, sticky = false, ...props }, ref) => (
  <thead
    ref={ref}
    className={`bg-gray-50 ${
      sticky ? 'sticky top-0 z-10' : ''
    } ${className || ''}`}
    {...props}
  />
));
TaxPoyntTableHeader.displayName = "TaxPoyntTableHeader";

// Table Body from legacy
const TaxPoyntTableBody = forwardRef<
  HTMLTableSectionElement,
  HTMLProps<HTMLTableSectionElement> & { maxHeight?: string }
>(({ className, maxHeight, ...props }, ref) => {
  const style: React.CSSProperties | undefined = maxHeight 
    ? { 
        maxHeight, 
        overflowY: 'auto' as const, 
        display: 'block' as const 
      } 
    : undefined;
  
  return (
    <tbody
      ref={ref}
      className={className || ''}
      style={style}
      {...props}
    />
  );
});
TaxPoyntTableBody.displayName = "TaxPoyntTableBody";

// Table Row from legacy
const TaxPoyntTableRow = forwardRef<HTMLTableRowElement, HTMLProps<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={`border-b border-gray-200 hover:bg-gray-50 transition-colors duration-200 ${className || ''}`}
      {...props}
    />
  )
);
TaxPoyntTableRow.displayName = "TaxPoyntTableRow";

// Table Head Cell from legacy
const TaxPoyntTableHead = forwardRef<HTMLTableCellElement, HTMLProps<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={`px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b border-gray-300 bg-gray-50 ${className || ''}`}
      {...props}
    />
  )
);
TaxPoyntTableHead.displayName = "TaxPoyntTableHead";

// Table Cell from legacy
const TaxPoyntTableCell = forwardRef<HTMLTableCellElement, HTMLProps<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={`px-4 py-3 text-sm text-gray-700 ${className || ''}`}
      {...props}
    />
  )
);
TaxPoyntTableCell.displayName = "TaxPoyntTableCell";

// Table Caption from legacy
const TaxPoyntTableCaption = forwardRef<HTMLTableCaptionElement, HTMLProps<HTMLTableCaptionElement>>(
  ({ className, ...props }, ref) => (
    <caption
      ref={ref}
      className={`py-2 text-sm text-gray-600 ${className || ''}`}
      {...props}
    />
  )
);
TaxPoyntTableCaption.displayName = "TaxPoyntTableCaption";

// Empty state component from legacy
interface TaxPoyntTableEmptyProps extends HTMLProps<HTMLTableRowElement> {
  colSpan: number;
  message?: string;
  icon?: React.ReactNode;
}

const TaxPoyntTableEmpty = forwardRef<HTMLTableRowElement, TaxPoyntTableEmptyProps>(
  ({ className, colSpan, message = "No data available", icon, ...props }, ref) => (
    <tr ref={ref} className={className} {...props}>
      <td 
        colSpan={colSpan}
        className="px-4 py-8 text-center text-gray-500"
      >
        <div className="flex flex-col items-center space-y-3">
          {icon && <div className="text-gray-400">{icon}</div>}
          <p className="text-sm font-medium">{message}</p>
        </div>
      </td>
    </tr>
  )
);
TaxPoyntTableEmpty.displayName = "TaxPoyntTableEmpty";

// Loading state component from legacy
interface TaxPoyntTableLoadingProps extends HTMLProps<HTMLTableRowElement> {
  colSpan: number;
  message?: string;
}

const TaxPoyntTableLoading = forwardRef<HTMLTableRowElement, TaxPoyntTableLoadingProps>(
  ({ className, colSpan, message = "Loading...", ...props }, ref) => (
    <tr ref={ref} className={className} {...props}>
      <td 
        colSpan={colSpan}
        className="px-4 py-8 text-center text-gray-500"
      >
        <div className="flex flex-col items-center space-y-3">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-r-transparent" />
          <p className="text-sm font-medium">{message}</p>
        </div>
      </td>
    </tr>
  )
);
TaxPoyntTableLoading.displayName = "TaxPoyntTableLoading";

// Pagination component for tables
interface TaxPoyntTablePaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showInfo?: boolean;
  totalItems?: number;
  itemsPerPage?: number;
}

const TaxPoyntTablePagination: React.FC<TaxPoyntTablePaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  showInfo = true,
  totalItems,
  itemsPerPage = 10,
}) => {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems || 0);

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
      {/* Info */}
      {showInfo && totalItems && (
        <div className="text-sm text-gray-700">
          Showing <span className="font-medium">{startItem}</span> to{' '}
          <span className="font-medium">{endItem}</span> of{' '}
          <span className="font-medium">{totalItems}</span> results
        </div>
      )}

      {/* Pagination Controls */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="px-3 py-1 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <span className="text-sm text-gray-700">
          Page {currentPage} of {totalPages}
        </span>
        
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="px-3 py-1 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export {
  TaxPoyntTableContainer,
  TaxPoyntTable,
  TaxPoyntTableHeader,
  TaxPoyntTableBody,
  TaxPoyntTableRow,
  TaxPoyntTableHead,
  TaxPoyntTableCell,
  TaxPoyntTableCaption,
  TaxPoyntTableEmpty,
  TaxPoyntTableLoading,
  TaxPoyntTablePagination
};

// Specialized table variants

// Dashboard Table - For business interface dashboards
export const DashboardTable: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <TaxPoyntTableContainer variant="card" className={className}>
    <TaxPoyntTable stickyHeader={true}>
      {children}
    </TaxPoyntTable>
  </TaxPoyntTableContainer>
);

// Simple Data Table - For basic data display
export const SimpleDataTable: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <TaxPoyntTableContainer variant="default" className={className}>
    <TaxPoyntTable>
      {children}
    </TaxPoyntTable>
  </TaxPoyntTableContainer>
);

// Mobile Responsive Table - Optimized for mobile viewing
export const MobileTable: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <TaxPoyntTableContainer variant="minimal" className={`overflow-x-auto ${className}`}>
    <TaxPoyntTable minWidth="320px">
      {children}
    </TaxPoyntTable>
  </TaxPoyntTableContainer>
);