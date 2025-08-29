'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { DashboardCard } from '../../../../shared_components/dashboard/DashboardCard';
import { TaxPoyntButton } from '../../../../design_system';

interface ConnectedSystem {
  id: string;
  name: string;
  category: 'erp' | 'crm' | 'pos' | 'ecommerce';
  icon: string;
  status: 'connected' | 'syncing' | 'error' | 'paused';
  lastSync: string;
  nextSync: string;
  healthScore: number;
  dataMetrics: {
    totalRecords: number;
    monthlyVolume: number;
    syncFrequency: string;
    errorRate: number;
  };
  features: string[];
  businessData: Record<string, string | number>;
}

export default function BusinessSystemsManagementPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [connectedSystems, setConnectedSystems] = useState<ConnectedSystem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock comprehensive business systems data
  const mockSystems: ConnectedSystem[] = [
    {
      id: 'sap-erp-001',
      name: 'SAP ERP System',
      category: 'erp',
      icon: '🏢',
      status: 'connected',
      lastSync: '5 minutes ago',
      nextSync: 'in 10 minutes',
      healthScore: 98.5,
      dataMetrics: {
        totalRecords: 45600,
        monthlyVolume: 2847,
        syncFrequency: 'Every 15 minutes',
        errorRate: 0.2
      },
      features: ['Financial Management', 'Supply Chain', 'Customer Data', 'Inventory Tracking'],
      businessData: {
        customers: 2847,
        invoices: 1456,
        products: 892,
        transactions: 15600
      }
    },
    {
      id: 'odoo-erp-002',
      name: 'Odoo ERP Community',
      category: 'erp',
      icon: '🟣',
      status: 'connected',
      lastSync: '12 minutes ago',
      nextSync: 'in 3 minutes',
      healthScore: 96.8,
      dataMetrics: {
        totalRecords: 28400,
        monthlyVolume: 1203,
        syncFrequency: 'Every 15 minutes',
        errorRate: 0.5
      },
      features: ['Invoicing', 'CRM', 'Inventory', 'Accounting'],
      businessData: {
        customers: 1203,
        invoices: 758,
        products: 445,
        transactions: 9200
      }
    },
    {
      id: 'salesforce-crm-001',
      name: 'Salesforce CRM',
      category: 'crm',
      icon: '☁️',
      status: 'connected',
      lastSync: '8 minutes ago',
      nextSync: 'in 22 minutes',
      healthScore: 96.2,
      dataMetrics: {
        totalRecords: 12600,
        monthlyVolume: 5892,
        syncFrequency: 'Every 30 minutes',
        errorRate: 0.3
      },
      features: ['Customer Data', 'Sales Pipeline', 'Deal Management', 'Analytics'],
      businessData: {
        contacts: 5892,
        deals: 234,
        accounts: 892,
        pipelineValue: 125000000
      }
    },
    {
      id: 'square-pos-001',
      name: 'Square POS Terminal',
      category: 'pos',
      icon: '⬜',
      status: 'connected',
      lastSync: '3 minutes ago',
      nextSync: 'Real-time',
      healthScore: 99.1,
      dataMetrics: {
        totalRecords: 8900,
        monthlyVolume: 456,
        syncFrequency: 'Real-time',
        errorRate: 0.1
      },
      features: ['Payment Processing', 'Inventory', 'Customer Data', 'Sales Reports'],
      businessData: {
        dailySales: 145000,
        transactions: 89,
        items: 456,
        customers: 234
      }
    },
    {
      id: 'shopify-pos-001',
      name: 'Shopify POS',
      category: 'pos',
      icon: '🛍️',
      status: 'syncing',
      lastSync: '7 minutes ago',
      nextSync: 'in 3 minutes',
      healthScore: 97.8,
      dataMetrics: {
        totalRecords: 6700,
        monthlyVolume: 234,
        syncFrequency: 'Every 10 minutes',
        errorRate: 0.2
      },
      features: ['E-commerce Integration', 'Inventory Sync', 'Customer Profiles', 'Analytics'],
      businessData: {
        dailySales: 89500,
        transactions: 56,
        items: 234,
        customers: 189
      }
    },
    {
      id: 'shopify-store-001',
      name: 'Shopify Online Store',
      category: 'ecommerce',
      icon: '🛒',
      status: 'connected',
      lastSync: '4 minutes ago',
      nextSync: 'in 6 minutes',
      healthScore: 97.8,
      dataMetrics: {
        totalRecords: 15600,
        monthlyVolume: 342,
        syncFrequency: 'Every 10 minutes',
        errorRate: 0.3
      },
      features: ['Product Catalog', 'Order Management', 'Customer Data', 'Sales Analytics'],
      businessData: {
        orders: 342,
        products: 156,
        customers: 1847,
        revenue: 8900000
      }
    }
  ];

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }
    if (currentUser.role !== 'system_integrator') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    
    // Load connected systems
    loadConnectedSystems();
  }, [router]);

  const loadConnectedSystems = async () => {
    setIsLoading(true);
    try {
      // In a real implementation, this would fetch from API
      // For now, use mock data
      setConnectedSystems(mockSystems);
    } catch (error) {
      console.error('Failed to load connected systems:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'paused': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCategoryName = (category: string) => {
    switch (category) {
      case 'erp': return 'ERP Systems';
      case 'crm': return 'CRM Systems';
      case 'pos': return 'POS Systems';
      case 'ecommerce': return 'E-commerce';
      default: return 'All Systems';
    }
  };

  const filteredSystems = selectedCategory === 'all' 
    ? connectedSystems 
    : connectedSystems.filter(system => system.category === selectedCategory);

  const categoryStats = {
    erp: connectedSystems.filter(s => s.category === 'erp').length,
    crm: connectedSystems.filter(s => s.category === 'crm').length,
    pos: connectedSystems.filter(s => s.category === 'pos').length,
    ecommerce: connectedSystems.filter(s => s.category === 'ecommerce').length
  };

  const handleSystemAction = (systemId: string, action: 'sync' | 'pause' | 'disconnect' | 'configure') => {
    console.log(`Performing ${action} on system ${systemId}`);
    // Implement system actions
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="business-systems"
    >
      <div className="min-h-full bg-gradient-to-br from-indigo-50 to-blue-50 p-6">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                🏢 Business Systems Management
              </h1>
              <p className="text-xl text-slate-600">
                Monitor and manage all your connected business system integrations
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/si')}
                className="border-2 border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                ← Back to Dashboard
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/onboarding/si/business-systems-setup')}
                className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
              >
                + Add New System
              </TaxPoyntButton>
            </div>
          </div>

          {/* Category Filter & Stats */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex space-x-4">
              {[
                { id: 'all', name: 'All Systems', count: connectedSystems.length },
                { id: 'erp', name: 'ERP', count: categoryStats.erp },
                { id: 'crm', name: 'CRM', count: categoryStats.crm },
                { id: 'pos', name: 'POS', count: categoryStats.pos },
                { id: 'ecommerce', name: 'E-commerce', count: categoryStats.ecommerce }
              ].map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 border'
                  }`}
                >
                  {category.name} ({category.count})
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Systems Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredSystems.map((system) => (
            <div key={system.id} className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
              
              {/* System Header */}
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{system.icon}</span>
                    <div>
                      <h3 className="text-lg font-bold text-slate-800">{system.name}</h3>
                      <p className="text-sm text-slate-600 capitalize">{system.category} System</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(system.status)}`}>
                      {system.status.charAt(0).toUpperCase() + system.status.slice(1)}
                    </span>
                    <span className={`text-sm font-bold ${getHealthScoreColor(system.healthScore)}`}>
                      {system.healthScore}%
                    </span>
                  </div>
                </div>

                {/* Sync Information */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Last Sync:</span>
                    <span className="font-medium text-slate-800 ml-2">{system.lastSync}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Next Sync:</span>
                    <span className="font-medium text-slate-800 ml-2">{system.nextSync}</span>
                  </div>
                </div>
              </div>

              {/* Business Data Metrics */}
              <div className="p-6">
                <h4 className="text-sm font-medium text-slate-700 mb-3">📊 Business Data</h4>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(system.businessData).map(([key, value]) => {
                    const displayValue = typeof value === 'number' && value > 1000000 
                      ? `₦${(value / 1000000).toFixed(1)}M`
                      : typeof value === 'number' 
                      ? value.toLocaleString()
                      : String(value);
                    
                    return (
                      <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-lg font-bold text-slate-800">
                          {displayValue}
                        </div>
                        <div className="text-xs text-slate-500 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* System Features */}
              <div className="p-6 bg-gray-50">
                <h4 className="text-sm font-medium text-slate-700 mb-3">🔧 Features</h4>
                <div className="grid grid-cols-2 gap-2">
                  {system.features.map((feature, index) => (
                    <div key={index} className="flex items-center text-xs text-slate-600">
                      <span className="w-1 h-1 bg-slate-400 rounded-full mr-2"></span>
                      {feature}
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-6 border-t border-gray-100">
                <div className="flex space-x-2">
                  <TaxPoyntButton
                    variant="outline"
                    size="sm"
                    onClick={() => handleSystemAction(system.id, 'sync')}
                    className="flex-1 border-blue-300 text-blue-700 hover:bg-blue-50"
                  >
                    🔄 Sync Now
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="outline"
                    size="sm"
                    onClick={() => handleSystemAction(system.id, 'configure')}
                    className="flex-1 border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                  >
                    ⚙️ Configure
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="outline"
                    size="sm"
                    onClick={() => handleSystemAction(system.id, 'pause')}
                    className="border-yellow-300 text-yellow-700 hover:bg-yellow-50"
                  >
                    ⏸️
                  </TaxPoyntButton>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary Information */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-slate-800 mb-4">📈 Integration Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">{connectedSystems.length}</div>
              <div className="text-sm text-slate-600">Total Systems</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {connectedSystems.reduce((sum, s) => sum + s.dataMetrics.totalRecords, 0).toLocaleString()}
              </div>
              <div className="text-sm text-slate-600">Total Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {(connectedSystems.reduce((sum, s) => sum + s.healthScore, 0) / connectedSystems.length).toFixed(1)}%
              </div>
              <div className="text-sm text-slate-600">Avg Health Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {(connectedSystems.reduce((sum, s) => sum + s.dataMetrics.errorRate, 0) / connectedSystems.length).toFixed(1)}%
              </div>
              <div className="text-sm text-slate-600">Avg Error Rate</div>
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
