/**
 * Enhanced Dashboard Layout Component
 * ===================================
 * Unified dashboard layout for all roles (SI, APP, Hybrid) using refined design system
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { OptimizedImage } from '../../design_system/components/OptimizedImage';
import { TaxPoyntButton } from '../../design_system';
import { 
  TYPOGRAPHY_STYLES, 
  getSectionBackground, 
  combineStyles,
  ACCESSIBILITY_PATTERNS 
} from '../../design_system/style-utilities';

export interface DashboardLayoutProps {
  children: React.ReactNode;
  role: 'si' | 'app' | 'hybrid';
  userName?: string;
  userEmail?: string;
  activeTab?: string;
  className?: string;
}

interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon: string;
  badge?: string;
  roles: ('si' | 'app' | 'hybrid')[];
  prefetch?: boolean; // Disable prefetching for non-existent routes
}

const navigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
    icon: '📊',
    roles: ['si', 'app', 'hybrid']
  },
  {
    id: 'integrations',
    label: 'Integrations',
    href: '/dashboard/integrations',
    icon: '🔗',
    badge: '15',
    roles: ['si', 'hybrid'],
    prefetch: false
  },
  {
    id: 'firs-communication',
    label: 'FIRS Communication',
    href: '/dashboard/firs',
    icon: '🏛️',
    roles: ['app', 'hybrid']
  },
  {
    id: 'firs-invoicing',
    label: 'FIRS Invoice Generator',
    href: '/dashboard/si/firs-invoice-generator',
    icon: '📋',
    roles: ['si', 'hybrid']
  },
  {
    id: 'business-systems',
    label: 'Business Systems',
    href: '/dashboard/si/business-systems',
    icon: '🏢',
    roles: ['si', 'hybrid']
  },
  {
    id: 'processing',
    label: 'Processing Center',
    href: '/dashboard/processing',
    icon: '⚙️',
    badge: '45',
    roles: ['si', 'app', 'hybrid'],
    prefetch: false
  },
  {
    id: 'compliance',
    label: 'Compliance',
    href: '/dashboard/compliance',
    icon: '✅',
    roles: ['si', 'app', 'hybrid'],
    prefetch: false
  },
  {
    id: 'analytics',
    label: 'Analytics',
    href: '/dashboard/analytics',
    icon: '📈',
    roles: ['si', 'app', 'hybrid'],
    prefetch: false
  },
  {
    id: 'financial',
    label: 'Financial Systems',
    href: '/dashboard/financial',
    icon: '💰',
    roles: ['si', 'hybrid'],
    prefetch: false
  },
  {
    id: 'security',
    label: 'Security Center',
    href: '/dashboard/security',
    icon: '🛡️',
    roles: ['app', 'hybrid']
  },
  {
    id: 'sdk-hub',
    label: 'SDK Hub',
    href: '/dashboard/si/sdk-hub',
    icon: '🚀',
    roles: ['si', 'hybrid'],
    prefetch: false
  },
  {
    id: 'tools',
    label: 'System Tools',
    href: '/dashboard/tools',
    icon: '🛠️',
    roles: ['si', 'hybrid'],
    prefetch: false
  },
  {
    id: 'workflows',
    label: 'Workflows',
    href: '/dashboard/workflows',
    icon: '🔄',
    roles: ['hybrid']
  }
];

const roleThemes = {
  si: {
    primary: 'indigo',
    gradient: 'from-indigo-600 to-blue-600',
    accent: 'indigo-600',
    name: 'System Integrator',
    description: 'Connect and manage business systems'
  },
  app: {
    primary: 'green',
    gradient: 'from-green-600 to-emerald-600',
    accent: 'green-600',
    name: 'Access Point Provider',
    description: 'Direct FIRS communication'
  },
  hybrid: {
    primary: 'purple',
    gradient: 'from-purple-600 to-indigo-600',
    accent: 'purple-600',
    name: 'Hybrid Solution',
    description: 'Unified compliance platform'
  }
};

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  role,
  userName = 'User',
  userEmail = 'user@example.com',
  activeTab = 'dashboard',
  className = ''
}) => {
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  const theme = roleThemes[role];
  const filteredNavItems = navigationItems.filter(item => item.roles.includes(role));

  const headerStyle = combineStyles(
    {
      background: `linear-gradient(135deg, var(--tw-gradient-stops))`,
      backdropFilter: 'blur(16px)'
    }
  );

  const handleSignOut = () => {
    // Handle sign out logic
    router.push('/auth/signin');
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      
      {/* Top Header */}
      <header 
        className={`fixed top-0 left-0 right-0 z-40 bg-gradient-to-r ${theme.gradient} shadow-lg`}
        style={headerStyle}
      >
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo & Branding */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="lg:hidden text-white hover:bg-white/20 p-2 rounded-lg transition-colors"
                aria-label="Toggle sidebar"
              >
                ☰
              </button>
              
              <div className="flex items-center space-x-3">
                <OptimizedImage
                  src="/logo.svg"
                  alt="TaxPoynt Logo"
                  width={40}
                  height={40}
                  className="w-10 h-10"
                  priority={true}
                />
                <div>
                  <div 
                    className="text-xl font-bold text-white"
                    style={TYPOGRAPHY_STYLES.optimizedText}
                  >
                    TaxPoynt
                  </div>
                  <div className="text-xs text-blue-100 font-medium">
                    {theme.name}
                  </div>
                </div>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              
              {/* Notifications */}
              <button className="relative text-white hover:bg-white/20 p-2 rounded-lg transition-colors">
                <span className="text-xl">🔔</span>
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  3
                </span>
              </button>

              {/* Help */}
              <button className="text-white hover:bg-white/20 p-2 rounded-lg transition-colors">
                <span className="text-xl">❓</span>
              </button>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-3 text-white hover:bg-white/20 p-2 rounded-lg transition-colors"
                  style={ACCESSIBILITY_PATTERNS.focusRing}
                >
                  <div className="w-8 h-8 bg-white/30 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold">{userName.charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="hidden md:block text-left">
                    <div className="text-sm font-medium">{userName}</div>
                    <div className="text-xs text-blue-100">{userEmail}</div>
                  </div>
                  <span className="text-sm">▼</span>
                </button>

                {/* User Dropdown */}
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="font-medium text-gray-900">{userName}</div>
                      <div className="text-sm text-gray-500">{userEmail}</div>
                      <div className="text-xs text-blue-600 font-medium mt-1">{theme.name}</div>
                    </div>
                    
                    <div className="py-2">
                      <Link href="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                        👤 Profile Settings
                      </Link>
                      <Link href="/billing" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                        💳 Billing & Usage
                      </Link>
                      <Link href="/support" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                        🎧 Support Center
                      </Link>
                      <hr className="my-2" />
                      <button 
                        onClick={handleSignOut}
                        className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        🚪 Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside 
        className={`fixed left-0 top-20 bottom-0 z-30 bg-white shadow-lg border-r border-gray-200 transition-all duration-300 ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        <div className="p-4">
          
          {/* Role Badge */}
          {!sidebarCollapsed && (
            <div className={`mb-6 p-3 bg-gradient-to-r ${theme.gradient} rounded-xl text-white`}>
              <div className="text-sm font-bold">{theme.name}</div>
              <div className="text-xs opacity-90">{theme.description}</div>
            </div>
          )}

          {/* Navigation */}
          <nav className="space-y-2">
            {filteredNavItems.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                prefetch={item.prefetch !== false}
                className={`flex items-center p-3 rounded-xl transition-all duration-200 ${
                  activeTab === item.id
                    ? `bg-${theme.accent} text-white shadow-lg`
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
                style={ACCESSIBILITY_PATTERNS.focusRing}
              >
                <span className="text-xl">{item.icon}</span>
                {!sidebarCollapsed && (
                  <>
                    <span className="ml-3 font-medium">{item.label}</span>
                    {item.badge && (
                      <span className={`ml-auto px-2 py-1 text-xs rounded-full ${
                        activeTab === item.id
                          ? 'bg-white/30 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </Link>
            ))}
          </nav>

          {/* Sidebar Footer */}
          {!sidebarCollapsed && (
            <div className="absolute bottom-4 left-4 right-4">
              <div className="p-3 bg-gray-50 rounded-xl">
                <div className="text-xs text-gray-500 mb-2">System Status</div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-xs text-gray-600">All Systems Operational</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main 
        className={`transition-all duration-300 pt-20 ${
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        <div className="p-6">
          {children}
        </div>
      </main>

      {/* Mobile Overlay */}
      {!sidebarCollapsed && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-20"
          onClick={() => setSidebarCollapsed(true)}
        />
      )}
    </div>
  );
};
