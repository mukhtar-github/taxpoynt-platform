'use client';

import React, { Suspense, useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/services/onboardingApi';
import { TaxPoyntButton } from '../../../../design_system';
import apiClient from '../../../../shared_components/api/client';

interface ConnectedSystemInfo {
  name: string;
  type: string;
  category: string;
  features: string[];
  dataTypes: string[];
}

const BusinessSystemsCallbackContent: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [user, setUser] = useState<User | null>(null);
  const [isProcessing, setIsProcessing] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [systemInfo, setSystemInfo] = useState<ConnectedSystemInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  const processCallback = useCallback(async () => {
    try {
      setIsProcessing(true);
      
      // Extract callback parameters
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const systemType = searchParams.get('system_type') || 'unknown';
      const category = searchParams.get('category') || 'erp';
      const error = searchParams.get('error');

      if (error) {
        throw new Error(`Integration failed: ${error}`);
      }

      if (!code || !state) {
        throw new Error('Missing required callback parameters');
      }

      console.log('📋 Processing business system callback:', { code, state, systemType, category });

      // Call backend to finalize the connection
      const result = await apiClient.post<{
        data?: { supported_data_types?: string[] };
      }>('/si/integrations/callback', {
        code,
        state,
        system_type: systemType,
        category,
        callback_type: 'business_systems'
      });

      setSystemInfo({
        name: getSystemDisplayName(systemType),
        type: systemType,
        category,
        features: getSystemFeatures(systemType),
        dataTypes: result.data?.supported_data_types || []
      });

      // Update onboarding state
      OnboardingStateManager.updateStep(user?.id, 'business_system_connected', true);
      
      setConnectionStatus('success');

      // Auto-redirect to reconciliation setup after 3 seconds
      setTimeout(() => {
        router.push('/onboarding/si/reconciliation-setup');
      }, 3000);

    } catch (error) {
      console.error('Business system callback processing failed:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error occurred');
      setConnectionStatus('error');
    } finally {
      setIsProcessing(false);
    }
  }, [router, searchParams, user]);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    setUser(currentUser);
    processCallback();
  }, [processCallback, router]);

  const getSystemDisplayName = (systemType: string): string => {
    const names: Record<string, string> = {
      'sap': 'SAP ERP',
      'odoo': 'Odoo ERP', 
      'netsuite': 'Oracle NetSuite',
      'dynamics': 'Microsoft Dynamics',
      'salesforce': 'Salesforce CRM',
      'hubspot': 'HubSpot CRM',
      'zoho': 'Zoho CRM',
      'square': 'Square POS',
      'shopify_pos': 'Shopify POS',
      'clover': 'Clover POS',
      'shopify': 'Shopify Store',
      'woocommerce': 'WooCommerce'
    };
    return names[systemType] || systemType.toUpperCase();
  };

  const getSystemFeatures = (systemType: string): string[] => {
    const features: Record<string, string[]> = {
      'sap': ['Financial Management', 'Supply Chain', 'Customer Data', 'Inventory'],
      'odoo': ['Invoicing', 'CRM', 'Inventory', 'Accounting'],
      'netsuite': ['Financial Management', 'E-commerce', 'CRM', 'Reporting'],
      'dynamics': ['Business Central', 'Finance', 'Operations', 'Customer Service'],
      'salesforce': ['Customer Data', 'Sales Pipeline', 'Deal Management', 'Analytics'],
      'hubspot': ['Contact Management', 'Deal Tracking', 'Email Marketing', 'Reporting'],
      'zoho': ['Lead Management', 'Sales Automation', 'Analytics', 'Mobile CRM'],
      'square': ['Payment Processing', 'Inventory', 'Customer Data', 'Sales Reports'],
      'shopify_pos': ['E-commerce Integration', 'Inventory Sync', 'Customer Profiles', 'Analytics'],
      'clover': ['Payment Processing', 'Employee Management', 'Inventory', 'Reporting'],
      'shopify': ['Product Catalog', 'Order Management', 'Customer Data', 'Sales Analytics'],
      'woocommerce': ['WordPress Integration', 'Product Management', 'Order Processing', 'Extensions']
    };
    return features[systemType] || ['Data Integration', 'Transaction Processing'];
  };

  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      'erp': '🏢',
      'crm': '👥', 
      'pos': '🛒',
      'ecommerce': '🌐'
    };
    return icons[category] || '🔗';
  };

  if (isProcessing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-indigo-600 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Processing Connection...</h2>
          <p className="text-slate-600">Finalizing your business system integration</p>
        </div>
      </div>
    );
  }

  if (connectionStatus === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center bg-white rounded-xl shadow-lg p-8">
          <div className="text-6xl mb-6">❌</div>
          <h2 className="text-2xl font-bold text-red-800 mb-4">Connection Failed</h2>
          <p className="text-red-600 mb-6">{errorMessage}</p>
          
          <div className="space-y-3">
            <TaxPoyntButton
              variant="primary"
              onClick={() => router.push('/onboarding/si/business-systems-setup')}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              Try Again
            </TaxPoyntButton>
            <TaxPoyntButton
              variant="outline"
              onClick={() => router.push('/onboarding/si/reconciliation-setup')}
              className="w-full border-red-300 text-red-700 hover:bg-red-50"
            >
              Continue Without This System
            </TaxPoyntButton>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center">
      <div className="max-w-lg mx-auto text-center bg-white rounded-xl shadow-lg p-8">
        
        {/* Success Icon and Header */}
        <div className="mb-6">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-3xl font-bold text-green-800 mb-2">
            {systemInfo?.name} Connected!
          </h2>
          <p className="text-green-600">
            Your business system integration was successful
          </p>
        </div>

        {/* System Information */}
        {systemInfo && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-center mb-3">
              <span className="text-3xl mr-3">{getCategoryIcon(systemInfo.category)}</span>
              <div>
                <h3 className="text-lg font-bold text-green-800">{systemInfo.name}</h3>
                <p className="text-sm text-green-600 capitalize">{systemInfo.category} System</p>
              </div>
            </div>
            
            <div className="text-left">
              <h4 className="font-medium text-green-800 mb-2">Integration Features:</h4>
              <div className="grid grid-cols-2 gap-2">
                {systemInfo.features.map((feature: string, index: number) => (
                  <div key={index} className="flex items-center text-sm text-green-700">
                    <span className="w-1 h-1 bg-green-500 rounded-full mr-2"></span>
                    {feature}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* What&apos;s Next */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-blue-800 mb-2">📋 What&apos;s Next?</h4>
          <div className="text-left text-sm text-blue-700 space-y-1">
            <p>• Set up automatic transaction matching rules</p>
            <p>• Configure data categorization preferences</p>
            <p>• Complete FIRS-compliant invoice generation setup</p>
            <p>• Access your comprehensive SI Dashboard</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <TaxPoyntButton
            variant="primary"
            onClick={() => router.push('/onboarding/si/reconciliation-setup')}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            Continue to Auto-Reconciliation Setup
          </TaxPoyntButton>
          
          <div className="text-sm text-slate-500">
            Auto-redirecting in 3 seconds...
          </div>
        </div>

        {/* Integration Success Summary */}
        <div className="mt-6 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
          <p className="text-sm text-emerald-700">
            <strong>🎯 Business System Ready:</strong> Your {systemInfo?.name} data will now feed into TaxPoynt&apos;s auto-reconciliation engine for seamless FIRS-compliant invoice generation.
          </p>
        </div>

      </div>
    </div>
  );
};

const BusinessSystemsCallbackFallback: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
    <div className="text-center">
      <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
      <p className="text-sm text-gray-600">Processing business system callback…</p>
    </div>
  </div>
);

export default function BusinessSystemsCallbackPage() {
  return (
    <Suspense fallback={<BusinessSystemsCallbackFallback />}>
      <BusinessSystemsCallbackContent />
    </Suspense>
  );
}
