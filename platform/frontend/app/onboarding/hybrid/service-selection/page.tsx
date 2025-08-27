'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function HybridServiceSelectionPage() {
  const router = useRouter();
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const services = [
    {
      id: 'si',
      name: 'System Integration',
      description: 'Connect and manage ERP, CRM, and POS systems',
      features: ['ERP Integration', 'CRM Connectivity', 'POS Systems', 'Data Mapping'],
      icon: '🔗'
    },
    {
      id: 'app',
      name: 'Invoice Processing',
      description: 'Direct FIRS e-invoice processing and compliance',
      features: ['FIRS Integration', 'Invoice Validation', 'Compliance Monitoring', 'Tax Reporting'],
      icon: '📄'
    }
  ];

  const handleServiceToggle = (serviceId: string) => {
    setSelectedServices(prev => 
      prev.includes(serviceId) 
        ? prev.filter(id => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const handleContinue = async () => {
    if (selectedServices.length === 0) {
      alert('Please select at least one service to continue');
      return;
    }

    setIsLoading(true);
    
    try {
      // Save service selection
      console.log('Hybrid user selected services:', selectedServices);
      
      if (selectedServices.includes('si') && selectedServices.includes('app')) {
        // Both services - go to combined setup
        router.push('/onboarding/hybrid/combined-setup');
      } else if (selectedServices.includes('si')) {
        // SI only - go to SI service selection
        router.push('/onboarding/si/service-selection');
      } else if (selectedServices.includes('app')) {
        // APP only - go to APP setup
        router.push('/onboarding/app/invoice-processing-setup');
      }
      
    } catch (error) {
      console.error('Service selection failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    router.push('/dashboard/hybrid');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Choose Your Services
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            As a Hybrid user, you can access both System Integration and Invoice Processing services
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {services.map((service) => (
            <div
              key={service.id}
              className={`
                relative border rounded-lg p-6 cursor-pointer transition-all duration-200
                ${selectedServices.includes(service.id) 
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' 
                  : 'border-gray-300 bg-white hover:border-gray-400'
                }
              `}
              onClick={() => handleServiceToggle(service.id)}
            >
              {/* Selection indicator */}
              <div className={`
                absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center
                ${selectedServices.includes(service.id) 
                  ? 'border-blue-500 bg-blue-500' 
                  : 'border-gray-300'
                }
              `}>
                {selectedServices.includes(service.id) && (
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>

              <div className="text-4xl mb-4">{service.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {service.name}
              </h3>
              <p className="text-gray-600 mb-4">
                {service.description}
              </p>
              
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Key Features:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {service.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2"></span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600 mb-6">
            You can select one or both services. Additional services can be enabled later from your dashboard.
          </p>
          
          <div className="flex justify-center space-x-4">
            <button 
              onClick={handleSkipForNow}
              className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Skip for Now
            </button>
            <button 
              onClick={handleContinue}
              disabled={isLoading || selectedServices.length === 0}
              className="px-8 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Setting up...' : `Continue with ${selectedServices.length} service${selectedServices.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}