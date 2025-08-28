'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SIServiceSelectionPage() {
  const router = useRouter();
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const integrationTypes = [
    {
      id: 'business_systems',
      name: 'Business Systems Integration',
      description: 'Connect ERP, CRM, POS, and E-commerce systems for comprehensive business management',
      features: [
        'ERP Integration (SAP, Odoo, NetSuite, QuickBooks)',
        'CRM Connectivity (Salesforce, HubSpot, Zoho)',
        'POS Systems (Square, Clover, Toast)',
        'E-commerce Platforms (Shopify, WooCommerce)',
        'Data Mapping & Transformation',
        'Business Process Automation'
      ],
      icon: '🏢',
      color: 'blue',
      estimatedTime: '2-4 hours setup',
      complexity: 'Advanced'
    },
    {
      id: 'financial_systems',
      name: 'Financial Systems Integration',
      description: 'Connect banking, payment processors, and financial platforms via Mono and other providers',
      features: [
        'Banking Integration via Mono Open Banking',
        'Payment Processors (Paystack, Flutterwave, Razorpay)',
        'Account Reconciliation',
        'Transaction Categorization',
        'Real-time Financial Data Sync',
        'Automated Tax Calculations'
      ],
      icon: '💰',
      color: 'green',
      estimatedTime: '30-60 minutes setup',
      complexity: 'Intermediate'
    },
    {
      id: 'both_systems',
      name: 'Complete Integration Suite',
      description: 'Full integration covering both business and financial systems for maximum automation',
      features: [
        'All Business Systems features',
        'All Financial Systems features',
        'Cross-system data synchronization',
        'Advanced reporting and analytics',
        'End-to-end invoice automation',
        'Comprehensive tax compliance'
      ],
      icon: '🔗',
      color: 'purple',
      estimatedTime: '3-5 hours setup',
      complexity: 'Expert'
    }
  ];

  const getColorClasses = (color: string, isSelected: boolean) => {
    const colorMap = {
      blue: isSelected 
        ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' 
        : 'border-gray-300 bg-white hover:border-blue-300',
      green: isSelected 
        ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
        : 'border-gray-300 bg-white hover:border-green-300',
      purple: isSelected 
        ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200' 
        : 'border-gray-300 bg-white hover:border-purple-300'
    };
    return colorMap[color as keyof typeof colorMap];
  };

  const getBadgeClasses = (color: string) => {
    const badgeMap = {
      blue: 'bg-blue-100 text-blue-800',
      green: 'bg-green-100 text-green-800',
      purple: 'bg-purple-100 text-purple-800'
    };
    return badgeMap[color as keyof typeof badgeMap];
  };

  const handleContinue = async () => {
    if (!selectedIntegration) {
      alert('Please select an integration type to continue');
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('SI user selected integration:', selectedIntegration);
      
      // Route to our new enhanced integration choice page first
      router.push('/onboarding/si/integration-choice');
      
    } catch (error) {
      console.error('Integration selection failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    router.push('/dashboard/si');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Choose Your Integration Type
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            As a System Integrator, select the systems you want to connect with TaxPoynt
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {integrationTypes.map((integration) => (
            <div
              key={integration.id}
              className={`
                relative border rounded-lg p-6 cursor-pointer transition-all duration-200
                ${getColorClasses(integration.color, selectedIntegration === integration.id)}
              `}
              onClick={() => setSelectedIntegration(integration.id)}
            >
              {/* Selection indicator */}
              <div className={`
                absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center
                ${selectedIntegration === integration.id 
                  ? `border-${integration.color}-500 bg-${integration.color}-500` 
                  : 'border-gray-300'
                }
              `}>
                {selectedIntegration === integration.id && (
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>

              {/* Integration details */}
              <div className="text-4xl mb-4">{integration.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {integration.name}
              </h3>
              <p className="text-gray-600 mb-4 text-sm leading-relaxed">
                {integration.description}
              </p>

              {/* Complexity and time badges */}
              <div className="flex gap-2 mb-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getBadgeClasses(integration.color)}`}>
                  {integration.complexity}
                </span>
                <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                  {integration.estimatedTime}
                </span>
              </div>

              {/* Features list */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900 text-sm">Key Features:</h4>
                <ul className="space-y-1">
                  {integration.features.slice(0, 4).map((feature, index) => (
                    <li key={index} className="text-xs text-gray-600 flex items-start">
                      <span className="text-green-500 mr-2 mt-0.5">✓</span>
                      {feature}
                    </li>
                  ))}
                  {integration.features.length > 4 && (
                    <li className="text-xs text-gray-500 italic">
                      +{integration.features.length - 4} more features...
                    </li>
                  )}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="flex justify-between items-center">
          <button
            onClick={handleSkipForNow}
            className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Skip for Now
          </button>
          
          <button
            onClick={handleContinue}
            disabled={!selectedIntegration || isLoading}
            className={`
              px-8 py-2 rounded-md font-medium transition-all duration-200
              ${selectedIntegration && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? 'Setting up...' : 'Continue Setup'}
          </button>
        </div>

        {/* Help text */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start">
            <div className="text-blue-500 mr-3 mt-0.5">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h4 className="text-blue-900 font-medium mb-1">Need Help Choosing?</h4>
              <p className="text-blue-700 text-sm">
                • <strong>Business Systems</strong>: Best for companies with existing ERP/CRM systems<br/>
                • <strong>Financial Systems</strong>: Ideal for banking integration and payment automation<br/>
                • <strong>Complete Suite</strong>: Recommended for businesses wanting full automation
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
