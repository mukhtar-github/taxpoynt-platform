'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton } from '../../../../design_system';

interface BusinessSystem {
  id: string;
  name: string;
  category: 'erp' | 'crm' | 'pos' | 'ecommerce';
  description: string;
  icon: string;
  status: 'available' | 'connecting' | 'connected' | 'demo';
  complexity: 'Easy' | 'Medium' | 'Complex';
  estimatedTime: string;
  popularity: 'Popular' | 'Trending' | null;
  features: string[];
  isRecommended?: boolean;
}

export default function BusinessSystemsSetupPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSystems, setSelectedSystems] = useState<string[]>([]);
  const [connectingSystem, setConnectingSystem] = useState<string | null>(null);

  // Enhanced business systems with comprehensive coverage
  const businessSystems: BusinessSystem[] = [
    // ERP Systems
    {
      id: 'sap',
      name: 'SAP ERP',
      category: 'erp',
      description: 'Enterprise Resource Planning - SAP S/4HANA, Business One',
      icon: '🏢',
      status: 'available',
      complexity: 'Complex',
      estimatedTime: '45-60 min',
      popularity: 'Popular',
      features: ['Financial Management', 'Supply Chain', 'Customer Data', 'Inventory'],
      isRecommended: true
    },
    {
      id: 'odoo',
      name: 'Odoo ERP',
      category: 'erp',
      description: 'Open-source business management suite',
      icon: '🟣',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '15-30 min',
      popularity: 'Popular',
      features: ['Invoicing', 'CRM', 'Inventory', 'Accounting'],
      isRecommended: true
    },
    {
      id: 'netsuite',
      name: 'Oracle NetSuite',
      category: 'erp',
      description: 'Cloud-based ERP and business management',
      icon: '🌐',
      status: 'available',
      complexity: 'Medium',
      estimatedTime: '30-45 min',
      popularity: null,
      features: ['Financial Management', 'E-commerce', 'CRM', 'Reporting']
    },
    {
      id: 'dynamics',
      name: 'Microsoft Dynamics',
      category: 'erp',
      description: 'Dynamics 365, NAV, GP integration',
      icon: '🔷',
      status: 'available',
      complexity: 'Medium',
      estimatedTime: '30-45 min',
      popularity: 'Trending',
      features: ['Business Central', 'Finance', 'Operations', 'Customer Service']
    },

    // CRM Systems
    {
      id: 'salesforce',
      name: 'Salesforce CRM',
      category: 'crm',
      description: 'World\'s #1 CRM platform for customer management',
      icon: '☁️',
      status: 'available',
      complexity: 'Medium',
      estimatedTime: '20-30 min',
      popularity: 'Popular',
      features: ['Customer Data', 'Sales Pipeline', 'Deal Management', 'Analytics'],
      isRecommended: true
    },
    {
      id: 'hubspot',
      name: 'HubSpot CRM',
      category: 'crm',
      description: 'Inbound marketing and sales platform',
      icon: '🧡',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '15-25 min',
      popularity: 'Popular',
      features: ['Contact Management', 'Deal Tracking', 'Email Marketing', 'Reporting']
    },
    {
      id: 'zoho',
      name: 'Zoho CRM',
      category: 'crm',
      description: 'Comprehensive customer relationship management',
      icon: '🟡',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '15-25 min',
      popularity: 'Trending',
      features: ['Lead Management', 'Sales Automation', 'Analytics', 'Mobile CRM']
    },

    // POS Systems
    {
      id: 'square',
      name: 'Square POS',
      category: 'pos',
      description: 'Complete point-of-sale solution for retail',
      icon: '⬜',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '10-20 min',
      popularity: 'Popular',
      features: ['Payment Processing', 'Inventory', 'Customer Data', 'Sales Reports']
    },
    {
      id: 'shopify_pos',
      name: 'Shopify POS',
      category: 'pos',
      description: 'Unified online and offline sales platform',
      icon: '🛍️',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '15-25 min',
      popularity: 'Trending',
      features: ['E-commerce Integration', 'Inventory Sync', 'Customer Profiles', 'Analytics']
    },
    {
      id: 'clover',
      name: 'Clover POS',
      category: 'pos',
      description: 'Business management and POS system',
      icon: '🍀',
      status: 'available',
      complexity: 'Medium',
      estimatedTime: '20-30 min',
      popularity: null,
      features: ['Payment Processing', 'Employee Management', 'Inventory', 'Reporting']
    },

    // E-commerce Platforms
    {
      id: 'shopify',
      name: 'Shopify Store',
      category: 'ecommerce',
      description: 'Leading e-commerce platform for online stores',
      icon: '🛒',
      status: 'available',
      complexity: 'Easy',
      estimatedTime: '10-20 min',
      popularity: 'Popular',
      features: ['Product Catalog', 'Order Management', 'Customer Data', 'Sales Analytics'],
      isRecommended: true
    },
    {
      id: 'woocommerce',
      name: 'WooCommerce',
      category: 'ecommerce',
      description: 'WordPress-based e-commerce solution',
      icon: '🌐',
      status: 'available',
      complexity: 'Medium',
      estimatedTime: '20-30 min',
      popularity: 'Popular',
      features: ['WordPress Integration', 'Product Management', 'Order Processing', 'Extensions']
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
    setIsLoading(false);
    
    // Update onboarding state
    OnboardingStateManager.updateStep(currentUser.id, 'business_systems_setup');
  }, [router]);

  const handleSystemConnect = async (systemId: string) => {
    const system = businessSystems.find(s => s.id === systemId);
    if (!system) return;

    setConnectingSystem(systemId);
    
    try {
      console.log(`🔗 Connecting to ${system.name}...`);
      
      // Call appropriate API based on system category
      const apiEndpoint = getSystemAPIEndpoint(system.category);
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          system_type: systemId,
          customer: {
            name: `${user.first_name} ${user.last_name}`,
            email: user.email
          },
          redirect_url: `${window.location.origin}/onboarding/si/business-systems-callback`,
          meta: {
            ref: `taxpoynt_business_${Date.now()}`,
            user_id: user.id,
            onboarding_step: 'business_systems_setup',
            system_category: system.category
          }
        })
      });

      if (!response.ok) {
        console.warn(`${system.name} API not available, using demo flow`);
        handleSystemDemoFlow(systemId);
        return;
      }

      const data = await response.json();
      if (data.setup_url) {
        // Open system setup in new window
        const setupWindow = window.open(data.setup_url, `${systemId}-setup`, 'width=800,height=600,scrollbars=yes,resizable=yes');
        
        // Monitor window closure
        const checkClosed = setInterval(() => {
          if (setupWindow?.closed) {
            clearInterval(checkClosed);
            handleSystemSetupComplete(systemId);
          }
        }, 1000);
      } else {
        handleSystemDemoFlow(systemId);
      }

    } catch (error) {
      console.error(`${system.name} setup failed:`, error);
      handleSystemDemoFlow(systemId);
    } finally {
      setConnectingSystem(null);
    }
  };

  const getSystemAPIEndpoint = (category: string): string => {
    const endpoints: Record<string, string> = {
      'erp': '/api/v1/si/integrations/erp',
      'crm': '/api/v1/si/integrations/crm', 
      'pos': '/api/v1/si/integrations/pos',
      'ecommerce': '/api/v1/si/integrations/ecommerce'
    };
    return endpoints[category] || '/api/v1/si/integrations/erp';
  };

  const handleSystemDemoFlow = (systemId: string) => {
    const system = businessSystems.find(s => s.id === systemId);
    setTimeout(() => {
      alert(`✅ Demo: ${system?.name} connected successfully! \n\n🔗 Integration Features:\n${system?.features.join('\n• ')}`);
      setSelectedSystems(prev => [...prev, systemId]);
      
    }, 2000);
  };

  const handleSystemSetupComplete = (systemId: string) => {
    setSelectedSystems(prev => [...prev, systemId]);
    console.log(`✅ ${systemId} setup completed successfully`);
  };

  const handleCompleteSetup = () => {
    if (selectedSystems.length === 0) {
      alert('Please connect at least one business system to continue');
      return;
    }

    // Update onboarding state
    OnboardingStateManager.updateStep(user.id, 'business_systems_complete', true);
    
    // Route to reconciliation setup (NOT directly to dashboard)
    router.push('/onboarding/si/reconciliation-setup');
  };

  const handleSkipForNow = () => {
    // Skip business systems and go to reconciliation setup
    router.push('/onboarding/si/reconciliation-setup');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) return null;

  const getCategoryStats = (category: string) => {
    const systems = businessSystems.filter(s => s.category === category);
    const connected = systems.filter(s => selectedSystems.includes(s.id));
    return { total: systems.length, connected: connected.length };
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Easy': return 'text-green-600 bg-green-50';
      case 'Medium': return 'text-orange-600 bg-orange-50';
      case 'Complex': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusDisplay = (system: BusinessSystem) => {
    if (selectedSystems.includes(system.id)) {
      return { text: 'Connected', color: 'text-green-600 bg-green-50', icon: '✅' };
    }
    if (connectingSystem === system.id) {
      return { text: 'Connecting...', color: 'text-blue-600 bg-blue-50', icon: '🔄' };
    }
    return { text: 'Click to Connect', color: 'text-gray-600 bg-gray-50', icon: '🔗' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        
        {/* Enhanced Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                🏢 Business Systems Integration
              </h1>
              <p className="text-xl text-slate-600">
                Connect your ERP, CRM, POS, and E-commerce systems for comprehensive data automation
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={handleSkipForNow}
                className="border-2 border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                Skip for Now
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={handleCompleteSetup}
                disabled={selectedSystems.length === 0}
                className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700"
              >
                Complete Setup ({selectedSystems.length} connected)
              </TaxPoyntButton>
            </div>
          </div>

          {/* Progress Stats */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {[
              { category: 'erp', name: 'ERP Systems', icon: '🏢', color: 'indigo' },
              { category: 'crm', name: 'CRM Systems', icon: '👥', color: 'green' },
              { category: 'pos', name: 'POS Systems', icon: '🛒', color: 'purple' },
              { category: 'ecommerce', name: 'E-commerce', icon: '🌐', color: 'orange' }
            ].map((cat) => {
              const stats = getCategoryStats(cat.category);
              return (
                <div key={cat.category} className={`bg-white p-4 rounded-xl shadow-md border border-${cat.color}-100`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{cat.icon}</span>
                    <span className={`text-sm font-bold text-${cat.color}-600`}>
                      {stats.connected}/{stats.total}
                    </span>
                  </div>
                  <div className={`text-sm font-medium text-${cat.color}-700`}>{cat.name}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Integration Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {businessSystems.map((system) => {
            const status = getStatusDisplay(system);
            const isConnected = selectedSystems.includes(system.id);
            const isConnecting = connectingSystem === system.id;
            
            return (
              <div
                key={system.id}
                className={`bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer border-2 ${
                  isConnected 
                    ? 'border-green-300 bg-green-50' 
                    : isConnecting
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 hover:border-indigo-300'
                } ${isConnected ? 'transform hover:scale-102' : 'hover:scale-105'}`}
                onClick={() => !isConnected && !isConnecting && handleSystemConnect(system.id)}
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">{system.icon}</span>
                      <div>
                        <h3 className="text-lg font-bold text-slate-800">{system.name}</h3>
                        <p className="text-sm text-slate-600">{system.description}</p>
                      </div>
                    </div>
                    {system.popularity && (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        system.popularity === 'Popular' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                      }`}>
                        {system.popularity}
                      </span>
                    )}
                  </div>

                  {/* Features */}
                  <div className="mb-4">
                    <div className="grid grid-cols-2 gap-2">
                      {system.features.slice(0, 4).map((feature, index) => (
                        <div key={index} className="flex items-center text-xs text-slate-600">
                          <span className="w-1 h-1 bg-slate-400 rounded-full mr-2"></span>
                          {feature}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getComplexityColor(system.complexity)}`}>
                        {system.complexity}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">
                        {system.estimatedTime}
                      </span>
                    </div>
                    {system.isRecommended && (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">
                        Recommended
                      </span>
                    )}
                  </div>

                  {/* Status/Action */}
                  <div className={`w-full p-3 rounded-lg text-center text-sm font-medium ${status.color}`}>
                    <span className="mr-2">{status.icon}</span>
                    {isConnecting && (
                      <div className="inline-block animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent mr-2"></div>
                    )}
                    {status.text}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Next Steps Information */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
          <div className="flex items-start">
            <span className="text-blue-500 mr-4 mt-1 text-2xl">💡</span>
            <div>
              <h3 className="text-lg font-bold text-slate-800 mb-2">What Happens Next?</h3>
              <div className="space-y-2 text-sm text-slate-600">
                <p>• <strong>Auto-Reconciliation Setup:</strong> Configure automatic transaction matching rules</p>
                <p>• <strong>Data Mapping:</strong> Map your business data fields to TaxPoynt&apos;s invoice structure</p>
                <p>• <strong>FIRS Integration:</strong> Complete setup for tax-compliant invoice generation</p>
                <p>• <strong>Dashboard Access:</strong> Monitor all integrations from your SI Dashboard</p>
              </div>
              
              <div className="mt-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                <p className="text-sm text-indigo-700">
                  <strong>🔗 Integration Pattern:</strong> Business Systems → Financial Systems → Auto-Reconciliation → FIRS Invoice Generation
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
