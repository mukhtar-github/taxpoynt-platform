/**
 * TaxPoynt Navigation System
 * ==========================
 * Extracted from legacy MainNav.tsx + Mobile optimizations
 * Complete navigation system for all platform needs
 */

'use client';

import React, { useState, forwardRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cva, type VariantProps } from 'class-variance-authority';

// Navigation container variants
const taxPoyntNavVariants = cva(
  "sticky top-0 z-50 border-b transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-white border-gray-200 shadow-sm",
        dark: "bg-gray-900 border-gray-700",
        transparent: "bg-white/95 backdrop-blur-sm border-gray-200/50",
        landing: "bg-gray-900 border-gray-700", // For landing page
      },
      size: {
        default: "h-16",
        compact: "h-14",
        large: "h-20",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

// Navigation item variants
const navItemVariants = cva(
  "inline-flex items-center px-3 py-2 text-sm font-medium transition-colors rounded-md",
  {
    variants: {
      variant: {
        default: "text-gray-700 hover:text-brand-primary hover:bg-gray-100",
        dark: "text-gray-300 hover:text-white hover:bg-gray-800",
        active: "text-brand-primary bg-brand-primary/10",
        activeDark: "text-white bg-gray-800",
      }
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface NavItem {
  name: string;
  href: string;
  icon?: React.ComponentType<any>;
  children?: NavItem[];
  badge?: string | number;
}

export interface TaxPoyntNavigationProps extends VariantProps<typeof taxPoyntNavVariants> {
  title?: string;
  logo?: React.ReactNode;
  navItems?: NavItem[];
  userInfo?: {
    name: string;
    email: string;
    avatar?: string;
  };
  authButtons?: React.ReactNode;
  onLogout?: () => void;
  className?: string;
}

const TaxPoyntNavigation = forwardRef<HTMLElement, TaxPoyntNavigationProps>(
  ({ 
    variant = "default",
    size = "default",
    title = "TaxPoynt",
    logo,
    navItems = [],
    userInfo,
    authButtons,
    onLogout,
    className,
    ...props 
  }, ref) => {
    const pathname = usePathname();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [openDropdown, setOpenDropdown] = useState<string | null>(null);

    const isDark = variant === 'dark' || variant === 'landing';
    const textColor = isDark ? 'text-white' : 'text-gray-900';
    const mutedTextColor = isDark ? 'text-gray-300' : 'text-gray-600';

    const toggleMobileMenu = () => setIsMobileMenuOpen(prev => !prev);
    const handleDropdownToggle = (name: string) => {
      setOpenDropdown(curr => curr === name ? null : name);
    };

    const isActive = (href: string) => {
      return pathname === href || pathname.startsWith(`${href}/`);
    };

    return (
      <>
        {/* Desktop Navigation */}
        <header 
          ref={ref}
          className={`hidden lg:block ${taxPoyntNavVariants({ variant, size, className })}`}
          {...props}
        >
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center justify-between h-full">
              {/* Logo and Brand */}
              <div className="flex items-center">
                {logo ? (
                  logo
                ) : (
                  <Link href="/" className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-lg">T</span>
                    </div>
                    <span className={`text-xl font-bold ${textColor}`}>
                      {title}
                    </span>
                  </Link>
                )}
              </div>

              {/* Desktop Navigation Links */}
              {navItems.length > 0 && (
                <nav className="hidden lg:flex items-center space-x-1">
                  {navItems.map((item) => (
                    <div key={item.name} className="relative group">
                      {item.children ? (
                        <button 
                          onClick={() => handleDropdownToggle(item.name)}
                          className={navItemVariants({ 
                            variant: isDark ? 'dark' : 'default'
                          })}
                        >
                          {item.icon && <item.icon className="w-4 h-4 mr-2" />}
                          {item.name}
                          {item.badge && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-primary text-white rounded-full">
                              {item.badge}
                            </span>
                          )}
                          <svg className="ml-1 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      ) : (
                        <Link
                          href={item.href}
                          className={navItemVariants({ 
                            variant: isActive(item.href) 
                              ? (isDark ? 'activeDark' : 'active')
                              : (isDark ? 'dark' : 'default')
                          })}
                        >
                          {item.icon && <item.icon className="w-4 h-4 mr-2" />}
                          {item.name}
                          {item.badge && (
                            <span className="ml-2 px-2 py-0.5 text-xs bg-primary text-white rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </Link>
                      )}

                      {/* Dropdown Menu */}
                      {item.children && openDropdown === item.name && (
                        <div className="absolute left-0 mt-2 w-48 rounded-lg shadow-lg bg-white ring-1 ring-gray-200 z-10">
                          <div className="py-2">
                            {item.children.map((child) => (
                              <Link
                                key={child.name}
                                href={child.href}
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-brand-primary"
                              >
                                {child.icon && <child.icon className="w-4 h-4 mr-3" />}
                                {child.name}
                                {child.badge && (
                                  <span className="ml-auto px-2 py-0.5 text-xs bg-primary text-white rounded-full">
                                    {child.badge}
                                  </span>
                                )}
                              </Link>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </nav>
              )}

              {/* User Menu and Auth */}
              <div className="flex items-center space-x-4">
                {/* Notifications */}
                {userInfo && (
                  <button className="p-2 text-gray-400 hover:text-gray-500 relative">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-5 5v-5zM10.586 3L13 5.414A2 2 0 0014.414 6H16a2 2 0 012 2v4.586a2 2 0 01-.586 1.414L13 18.414A2 2 0 0011.586 19H10a2 2 0 01-2-2v-4.586A2 2 0 018.586 11L13 6.586z" />
                    </svg>
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                  </button>
                )}

                {/* Auth Buttons or User Menu */}
                {authButtons ? (
                  <div className="flex items-center space-x-2">
                    {authButtons}
                  </div>
                ) : userInfo ? (
                  <div className="relative">
                    <button 
                      onClick={() => handleDropdownToggle('user')}
                      className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    >
                      <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-white font-medium">
                        {userInfo.name.charAt(0).toUpperCase()}
                      </div>
                    </button>

                    {openDropdown === 'user' && (
                      <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-white ring-1 ring-gray-200 z-10">
                        <div className="px-4 py-3 border-b border-gray-200">
                          <p className="text-sm font-medium text-gray-900">{userInfo.name}</p>
                          <p className="text-sm text-gray-600">{userInfo.email}</p>
                        </div>
                        <div className="py-2">
                          <Link href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            Profile
                          </Link>
                          <Link href="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            Settings
                          </Link>
                          {onLogout && (
                            <button
                              onClick={onLogout}
                              className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                            >
                              Sign out
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </header>

        {/* Mobile Navigation */}
        <header className={`lg:hidden ${taxPoyntNavVariants({ variant, size: 'compact' })}`}>
          <div className="px-4">
            <div className="flex items-center justify-between h-14">
              {/* Mobile Logo */}
              <div className="flex items-center">
                {logo ? (
                  <div className="scale-90">{logo}</div>
                ) : (
                  <Link href="/" className="flex items-center space-x-2">
                    <div className="w-7 h-7 bg-primary rounded-md flex items-center justify-center">
                      <span className="text-white font-bold text-sm">T</span>
                    </div>
                    <span className={`text-lg font-bold ${textColor}`}>
                      {title}
                    </span>
                  </Link>
                )}
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={toggleMobileMenu}
                className={`p-2 rounded-md ${mutedTextColor} hover:text-gray-500 hover:bg-gray-100`}
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isMobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {isMobileMenuOpen && (
            <div className="lg:hidden bg-white border-t border-gray-200">
              <div className="px-4 py-3 space-y-1">
                {/* Mobile Navigation Items */}
                {navItems.map((item) => (
                  <div key={item.name}>
                    {item.children ? (
                      <>
                        <button
                          onClick={() => handleDropdownToggle(item.name)}
                          className="flex items-center justify-between w-full px-3 py-2 text-base font-medium text-gray-700 hover:text-brand-primary hover:bg-gray-50 rounded-md"
                        >
                          <span className="flex items-center">
                            {item.icon && <item.icon className="mr-3 h-5 w-5" />}
                            {item.name}
                          </span>
                          <svg className={`h-5 w-5 transition-transform ${openDropdown === item.name ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                        
                        {openDropdown === item.name && (
                          <div className="pl-10 space-y-1 mt-1">
                            {item.children.map((child) => (
                              <Link
                                key={child.name}
                                href={child.href}
                                className="flex items-center px-3 py-2 text-base font-medium text-gray-600 hover:text-brand-primary hover:bg-gray-50 rounded-md"
                              >
                                {child.icon && <child.icon className="mr-3 h-5 w-5" />}
                                {child.name}
                              </Link>
                            ))}
                          </div>
                        )}
                      </>
                    ) : (
                      <Link
                        href={item.href}
                        className="flex items-center px-3 py-2 text-base font-medium text-gray-700 hover:text-brand-primary hover:bg-gray-50 rounded-md"
                      >
                        {item.icon && <item.icon className="mr-3 h-5 w-5" />}
                        {item.name}
                      </Link>
                    )}
                  </div>
                ))}

                {/* Mobile User Info */}
                {userInfo && (
                  <div className="pt-4 mt-4 border-t border-gray-200">
                    <div className="flex items-center px-3 py-2">
                      <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-white font-medium">
                        {userInfo.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="ml-3">
                        <p className="text-base font-medium text-gray-900">{userInfo.name}</p>
                        <p className="text-sm text-gray-600">{userInfo.email}</p>
                      </div>
                    </div>
                    {onLogout && (
                      <button
                        onClick={onLogout}
                        className="mt-2 w-full text-left px-3 py-2 text-base font-medium text-red-700 hover:bg-red-50 rounded-md"
                      >
                        Sign out
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </header>
      </>
    );
  }
);

TaxPoyntNavigation.displayName = "TaxPoyntNavigation";

export { TaxPoyntNavigation, taxPoyntNavVariants, navItemVariants };

// Specialized navigation variants

// Landing Page Navigation
export const LandingNavigation: React.FC<Omit<TaxPoyntNavigationProps, 'variant'>> = (props) => (
  <TaxPoyntNavigation variant="landing" {...props} />
);

// Dashboard Navigation  
export const DashboardNavigation: React.FC<Omit<TaxPoyntNavigationProps, 'variant'>> = (props) => (
  <TaxPoyntNavigation variant="default" {...props} />
);

// Auth Page Navigation
export const AuthNavigation: React.FC<Omit<TaxPoyntNavigationProps, 'variant' | 'size'>> = (props) => (
  <TaxPoyntNavigation variant="transparent" size="compact" {...props} />
);