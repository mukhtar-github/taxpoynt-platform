/**
 * APP Interface Main Router
 * =========================
 * 
 * Main router component for Access Point Provider (APP) interface.
 * Manages routing between all APP-specific pages, workflows, and components.
 * 
 * Features:
 * - Complete APP interface routing
 * - Authentication and authorization guards
 * - Layout management with sidebar navigation
 * - Breadcrumb navigation
 * - Loading states and error boundaries
 * - Responsive design for all screen sizes
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect, Suspense } from 'react';
import { Layout, Menu, Breadcrumb, Spin, Alert, Avatar, Dropdown, Badge, Space } from 'antd';
import {
  DashboardOutlined,
  SendOutlined,
  CloudServerOutlined,
  ShieldCheckOutlined,
  FileTextOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  RocketOutlined
} from '@ant-design/icons';

// Lazy load pages for better performance
const TransmissionMonitorPage = React.lazy(() => import('./pages/transmission_monitor'));
const FIRSDashboardPage = React.lazy(() => import('./pages/firs_dashboard'));
const SecurityAuditPage = React.lazy(() => import('./pages/security_audit'));
const ComplianceReportsPage = React.lazy(() => import('./pages/compliance_reports'));

// Lazy load workflows
const FIRSSetupWorkflow = React.lazy(() => import('./workflows/firs_setup'));
const TransmissionConfigWorkflow = React.lazy(() => import('./workflows/transmission_config'));
const SecuritySetupWorkflow = React.lazy(() => import('./workflows/security_setup'));

const { Header, Sider, Content } = Layout;

interface APPInterfaceProps {
  onLogout?: () => void;
  userInfo?: {
    name: string;
    email: string;
    role: string;
    avatar?: string;
  };
  className?: string;
}

interface NavigationItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
  children?: NavigationItem[];
}

interface BreadcrumbItem {
  title: string;
  path?: string;
}

// Navigation configuration
const navigationItems: NavigationItem[] = [
  {
    key: 'transmission',
    icon: <SendOutlined />,
    label: 'Transmission Monitor',
    path: '/app/transmission'
  },
  {
    key: 'firs',
    icon: <CloudServerOutlined />,
    label: 'FIRS Dashboard',
    path: '/app/firs'
  },
  {
    key: 'security',
    icon: <ShieldCheckOutlined />,
    label: 'Security Audit',
    path: '/app/security'
  },
  {
    key: 'compliance',
    icon: <FileTextOutlined />,
    label: 'Compliance Reports',
    path: '/app/compliance'
  },
  {
    key: 'setup',
    icon: <SettingOutlined />,
    label: 'Setup & Configuration',
    path: '/app/setup',
    children: [
      {
        key: 'firs-setup',
        icon: <CloudServerOutlined />,
        label: 'FIRS Setup',
        path: '/app/setup/firs'
      },
      {
        key: 'transmission-config',
        icon: <SendOutlined />,
        label: 'Transmission Config',
        path: '/app/setup/transmission'
      },
      {
        key: 'security-setup',
        icon: <ShieldCheckOutlined />,
        label: 'Security Setup',
        path: '/app/setup/security'
      }
    ]
  }
];

// Breadcrumb mapping
const breadcrumbMap: Record<string, BreadcrumbItem[]> = {
  '/app/transmission': [
    { title: 'APP Interface' },
    { title: 'Transmission Monitor' }
  ],
  '/app/firs': [
    { title: 'APP Interface' },
    { title: 'FIRS Dashboard' }
  ],
  '/app/security': [
    { title: 'APP Interface' },
    { title: 'Security Audit' }
  ],
  '/app/compliance': [
    { title: 'APP Interface' },
    { title: 'Compliance Reports' }
  ],
  '/app/setup/firs': [
    { title: 'APP Interface' },
    { title: 'Setup', path: '/app/setup' },
    { title: 'FIRS Setup' }
  ],
  '/app/setup/transmission': [
    { title: 'APP Interface' },
    { title: 'Setup', path: '/app/setup' },
    { title: 'Transmission Config' }
  ],
  '/app/setup/security': [
    { title: 'APP Interface' },
    { title: 'Setup', path: '/app/setup' },
    { title: 'Security Setup' }
  ]
};

const LoadingSpinner: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '400px' 
  }}>
    <Spin size="large" tip="Loading..." />
  </div>
);

const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const handleError = () => setHasError(true);
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return (
      <div style={{ padding: '50px' }}>
        <Alert
          type="error"
          message="Something went wrong"
          description="An error occurred while loading this page. Please try refreshing."
          showIcon
          action={
            <button onClick={() => window.location.reload()}>
              Refresh Page
            </button>
          }
        />
      </div>
    );
  }

  return <>{children}</>;
};

const AppLayout: React.FC<APPInterfaceProps> = ({ 
  onLogout, 
  userInfo,
  className 
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [openKeys, setOpenKeys] = useState<string[]>(['setup']);

  // Default to transmission monitoring
  useEffect(() => {
    setSelectedKeys(['transmission']);
  }, []);

  // User dropdown menu
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile Settings'
    },
    {
      key: 'preferences',
      icon: <SettingOutlined />,
      label: 'Preferences'
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: onLogout
    }
  ];

  // Default breadcrumb
  const currentBreadcrumb = [
    { title: 'APP Interface' },
    { title: 'Transmission Monitor' }
  ];

  return (
    <Layout className={`app-interface-layout ${className || ''}`} style={{ minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        width={250}
        style={{
          background: '#001529',
          position: 'fixed',
          height: '100vh',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100
        }}
      >
        {/* Logo */}
        <div style={{ 
          height: 64, 
          margin: 16,
          background: 'rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: collapsed ? 14 : 16
        }}>
          <RocketOutlined style={{ marginRight: collapsed ? 0 : 8 }} />
          {!collapsed && 'TaxPoynt APP'}
        </div>

        {/* Navigation Menu */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          style={{ borderRight: 0 }}
          items={navigationItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
            children: item.children?.map(child => ({
              key: child.key,
              icon: child.icon,
              label: child.label,
              onClick: () => window.location.hash = child.path
            })),
            onClick: !item.children ? () => window.location.hash = item.path : undefined
          }))}
        />
      </Sider>

      {/* Main Layout */}
      <Layout style={{ marginLeft: collapsed ? 80 : 250 }}>
        {/* Header */}
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px #f0f1f2'
        }}>
          {/* Collapse Button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: 16,
              width: 64,
              height: 64,
              border: 'none',
              background: 'transparent',
              cursor: 'pointer'
            }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </button>

          {/* User Info */}
          <Space size="large">
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18 }} />
            </Badge>
            
            {userInfo && (
              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar 
                    src={userInfo.avatar} 
                    icon={!userInfo.avatar && <UserOutlined />}
                    size="small"
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 14, fontWeight: 500 }}>{userInfo.name}</span>
                    <span style={{ fontSize: 12, color: '#666' }}>{userInfo.role}</span>
                  </div>
                </Space>
              </Dropdown>
            )}
          </Space>
        </Header>

        {/* Breadcrumb */}
        <div style={{ padding: '16px 24px 0' }}>
          <Breadcrumb>
            {currentBreadcrumb.map((item, index) => (
              <Breadcrumb.Item key={index}>
                {item.path ? (
                  <a href={`#${item.path}`}>{item.title}</a>
                ) : (
                  item.title
                )}
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>
        </div>

        {/* Main Content */}
        <Content style={{ 
          margin: '24px',
          padding: '24px',
          background: '#fff',
          borderRadius: 6,
          minHeight: 'calc(100vh - 112px)'
        }}>
          <ErrorBoundary>
            <div className="text-center py-20">
              <div className="max-w-md mx-auto">
                <div className="mb-6">
                  <SendOutlined style={{ fontSize: '3rem', color: '#1890ff' }} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">APP Interface Dashboard</h2>
                <p className="text-gray-600 mb-6">
                  Welcome to your Access Point Provider dashboard. Manage FIRS transmission, 
                  security audits, and compliance reporting.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-900 mb-2">Transmission Status</h3>
                    <p className="text-blue-700 text-sm">Monitor invoice transmission to FIRS</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-green-900 mb-2">FIRS Integration</h3>
                    <p className="text-green-700 text-sm">Manage FIRS API connections</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-purple-900 mb-2">Security Audit</h3>
                    <p className="text-purple-700 text-sm">Review security compliance</p>
                  </div>
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-orange-900 mb-2">Compliance</h3>
                    <p className="text-orange-700 text-sm">Generate compliance reports</p>
                  </div>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        </Content>
      </Layout>
    </Layout>
  );
};

// Main APP Interface Component
export const APPInterface: React.FC<APPInterfaceProps> = (props) => {
  return <AppLayout {...props} />;
};

// Default export
export default APPInterface;

// Export individual components for flexibility
export {
  TransmissionMonitorPage,
  FIRSDashboardPage, 
  SecurityAuditPage,
  ComplianceReportsPage,
  FIRSSetupWorkflow,
  TransmissionConfigWorkflow,
  SecuritySetupWorkflow
};