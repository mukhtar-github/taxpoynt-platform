/**
 * APP Business Verification Page
 * ==============================
 * Business verification and KYC for Access Point Provider users
 * Collects detailed business information required for FIRS compliance
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';

interface BusinessVerificationData {
  business_type: string;
  tin: string;
  rc_number: string;
  address: string;
  state: string;
  lga: string;
  phone: string;
  website?: string;
  industry_sector: string;
  business_size: string;
  annual_revenue_range: string;
}

export default function APPBusinessVerificationPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<BusinessVerificationData>({
    business_type: '',
    tin: '',
    rc_number: '',
    address: '',
    state: '',
    lga: '',
    phone: '',
    website: '',
    industry_sector: '',
    business_size: '',
    annual_revenue_range: ''
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    if (currentUser.role !== 'access_point_provider') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    
    // Update onboarding state
    OnboardingStateManager.updateStep(currentUser.id, 'business_verification');
  }, [router]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.business_type.trim()) errors.business_type = 'Business type is required';
    if (!formData.tin.trim()) errors.tin = 'TIN is required';
    else if (!/^\d{8}-\d{4}$/.test(formData.tin)) errors.tin = 'TIN must be in format 12345678-0001';
    if (!formData.rc_number.trim()) errors.rc_number = 'RC Number is required';
    if (!formData.address.trim()) errors.address = 'Business address is required';
    if (!formData.state.trim()) errors.state = 'State is required';
    if (!formData.lga.trim()) errors.lga = 'LGA is required';
    if (!formData.phone.trim()) errors.phone = 'Phone number is required';
    if (!formData.industry_sector.trim()) errors.industry_sector = 'Industry sector is required';
    if (!formData.business_size.trim()) errors.business_size = 'Business size is required';
    if (!formData.annual_revenue_range.trim()) errors.annual_revenue_range = 'Revenue range is required';

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleContinue = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    
    try {
      console.log('📊 APP user completed business verification:', formData);
      
      // Save business verification data
      // TODO: Call API to update user profile with business details
      
      // Update onboarding state
      OnboardingStateManager.updateStep(user.id, 'business_verification', true);
      
      // Route to invoice processing setup
      router.push('/onboarding/app/invoice-processing-setup');
      
    } catch (error) {
      console.error('Business verification failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipForNow = () => {
    // Mark onboarding as complete and go to dashboard
    OnboardingStateManager.completeOnboarding(user?.id);
    router.push('/dashboard/app');
  };

  const businessTypes = [
    'Limited Liability Company (LLC)',
    'Public Limited Company (PLC)',
    'Sole Proprietorship',
    'Partnership',
    'Non-Profit Organization',
    'Government Agency',
    'Other'
  ];

  const industrySectors = [
    'Technology',
    'Manufacturing',
    'Retail/E-commerce',
    'Professional Services',
    'Healthcare',
    'Education',
    'Financial Services',
    'Construction',
    'Agriculture',
    'Transportation',
    'Other'
  ];

  const businessSizes = [
    'Micro (1-10 employees)',
    'Small (11-50 employees)',
    'Medium (51-250 employees)',
    'Large (250+ employees)'
  ];

  const revenueRanges = [
    'Under ₦1 million',
    '₦1 - ₦5 million',
    '₦5 - ₦25 million',
    '₦25 - ₦100 million',
    '₦100 - ₦500 million',
    'Over ₦500 million'
  ];

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Business Verification 🏢
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Complete your business verification to enable FIRS integration and invoice processing.
            This information is required for tax compliance.
          </p>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center text-green-800 text-sm">
              <span className="mr-2">👋</span>
              <span>Welcome, {user.first_name}! Let's verify your <strong>Access Point Provider</strong> business details.</span>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Business Type */}
            <div className="col-span-full">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Type *
              </label>
              <select
                value={formData.business_type}
                onChange={(e) => setFormData({...formData, business_type: e.target.value})}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  fieldErrors.business_type ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select business type</option>
                {businessTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              {fieldErrors.business_type && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.business_type}</p>
              )}
            </div>

            {/* TIN */}
            <TaxPoyntInput
              label="Tax Identification Number (TIN) *"
              value={formData.tin}
              onChange={(e) => setFormData({...formData, tin: e.target.value})}
              variant={fieldErrors.tin ? 'error' : 'default'}
              placeholder="12345678-0001"
              helpText="Format: 12345678-0001"
            />

            {/* RC Number */}
            <TaxPoyntInput
              label="RC Number *"
              value={formData.rc_number}
              onChange={(e) => setFormData({...formData, rc_number: e.target.value})}
              variant={fieldErrors.rc_number ? 'error' : 'default'}
              placeholder="RC123456"
            />

            {/* Address */}
            <div className="col-span-full">
              <TaxPoyntInput
                label="Business Address *"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                variant={fieldErrors.address ? 'error' : 'default'}
                placeholder="123 Business Street, Lagos"
              />
            </div>

            {/* State */}
            <TaxPoyntInput
              label="State *"
              value={formData.state}
              onChange={(e) => setFormData({...formData, state: e.target.value})}
              variant={fieldErrors.state ? 'error' : 'default'}
              placeholder="Lagos"
            />

            {/* LGA */}
            <TaxPoyntInput
              label="Local Government Area (LGA) *"
              value={formData.lga}
              onChange={(e) => setFormData({...formData, lga: e.target.value})}
              variant={fieldErrors.lga ? 'error' : 'default'}
              placeholder="Lagos Island"
            />

            {/* Phone */}
            <TaxPoyntInput
              label="Business Phone *"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              variant={fieldErrors.phone ? 'error' : 'default'}
              placeholder="+2348012345678"
            />

            {/* Website */}
            <TaxPoyntInput
              label="Website (Optional)"
              value={formData.website}
              onChange={(e) => setFormData({...formData, website: e.target.value})}
              placeholder="https://yourbusiness.com"
            />

            {/* Industry Sector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry Sector *
              </label>
              <select
                value={formData.industry_sector}
                onChange={(e) => setFormData({...formData, industry_sector: e.target.value})}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  fieldErrors.industry_sector ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select industry</option>
                {industrySectors.map((sector) => (
                  <option key={sector} value={sector}>{sector}</option>
                ))}
              </select>
              {fieldErrors.industry_sector && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.industry_sector}</p>
              )}
            </div>

            {/* Business Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Size *
              </label>
              <select
                value={formData.business_size}
                onChange={(e) => setFormData({...formData, business_size: e.target.value})}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  fieldErrors.business_size ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select size</option>
                {businessSizes.map((size) => (
                  <option key={size} value={size}>{size}</option>
                ))}
              </select>
              {fieldErrors.business_size && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.business_size}</p>
              )}
            </div>

            {/* Annual Revenue */}
            <div className="col-span-full">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Annual Revenue Range *
              </label>
              <select
                value={formData.annual_revenue_range}
                onChange={(e) => setFormData({...formData, annual_revenue_range: e.target.value})}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 ${
                  fieldErrors.annual_revenue_range ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Select revenue range</option>
                {revenueRanges.map((range) => (
                  <option key={range} value={range}>{range}</option>
                ))}
              </select>
              {fieldErrors.annual_revenue_range && (
                <p className="text-sm text-red-600 mt-1">{fieldErrors.annual_revenue_range}</p>
              )}
            </div>
          </div>

          {/* Error Summary */}
          {Object.keys(fieldErrors).length > 0 && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-sm font-medium text-red-800 mb-2">Please fix the following errors:</h3>
              <ul className="text-sm text-red-700 space-y-1">
                {Object.values(fieldErrors).map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 mt-8">
            <TaxPoyntButton
              variant="primary"
              onClick={handleContinue}
              loading={isLoading}
              disabled={isLoading}
              className="flex-1 max-w-xs"
            >
              Continue to FIRS Setup
            </TaxPoyntButton>
            
            <TaxPoyntButton
              variant="secondary"
              onClick={handleSkipForNow}
              disabled={isLoading}
              className="flex-1 max-w-xs"
            >
              Complete Later
            </TaxPoyntButton>
          </div>

          {/* Help Text */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">🔒 Data Security</h3>
            <p className="text-sm text-blue-700">
              This information is securely encrypted and used only for FIRS compliance and tax processing.
              We follow strict NDPR guidelines to protect your business data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
