'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { OnboardingStateManager } from '../../../../shared_components/onboarding/ServiceOnboardingRouter';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';

interface ReconciliationRule {
  id: string;
  name: string;
  description: string;
  category: 'transaction_matching' | 'categorization' | 'fraud_detection' | 'compliance';
  enabled: boolean;
  config: {
    [key: string]: any;
  };
}

interface MatchingCriteria {
  amount_tolerance: number;
  date_range_days: number;
  reference_matching: boolean;
  narration_matching: boolean;
  account_matching: boolean;
}

export default function ReconciliationSetupPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState<'rules' | 'categories' | 'review'>('rules');
  const [matchingCriteria, setMatchingCriteria] = useState<MatchingCriteria>({
    amount_tolerance: 0.01,
    date_range_days: 3,
    reference_matching: true,
    narration_matching: true,
    account_matching: true
  });

  const [reconciliationRules, setReconciliationRules] = useState<ReconciliationRule[]>([
    {
      id: 'auto_match_exact',
      name: 'Exact Amount Matching',
      description: 'Automatically match transactions with identical amounts and dates',
      category: 'transaction_matching',
      enabled: true,
      config: { tolerance: 0, date_range: 1 }
    },
    {
      id: 'auto_match_tolerance',
      name: 'Tolerance-based Matching',
      description: 'Match transactions within specified amount tolerance and date range',
      category: 'transaction_matching',
      enabled: true,
      config: { tolerance: 0.01, date_range: 3 }
    },
    {
      id: 'reference_matching',
      name: 'Reference Number Matching',
      description: 'Match transactions using reference numbers and transaction IDs',
      category: 'transaction_matching',
      enabled: true,
      config: { strict: false }
    },
    {
      id: 'narration_keywords',
      name: 'Narration Keyword Matching',
      description: 'Use transaction descriptions to identify and categorize payments',
      category: 'categorization',
      enabled: true,
      config: { keywords: ['salary', 'invoice', 'payment', 'transfer'] }
    },
    {
      id: 'customer_matching',
      name: 'Customer-based Categorization',
      description: 'Automatically categorize transactions based on known customers',
      category: 'categorization',
      enabled: true,
      config: { customer_database: true }
    },
    {
      id: 'duplicate_detection',
      name: 'Duplicate Transaction Detection',
      description: 'Identify and flag potential duplicate transactions',
      category: 'fraud_detection',
      enabled: true,
      config: { time_window: 300 }
    },
    {
      id: 'amount_anomaly',
      name: 'Amount Anomaly Detection',
      description: 'Flag transactions with unusual amounts compared to historical patterns',
      category: 'fraud_detection',
      enabled: false,
      config: { threshold: 2.5 }
    },
    {
      id: 'compliance_monitoring',
      name: 'Compliance Rule Monitoring',
      description: 'Ensure transactions comply with Nigerian financial regulations',
      category: 'compliance',
      enabled: true,
      config: { cbn_rules: true, aml_checks: true }
    }
  ]);

  const [transactionCategories, setTransactionCategories] = useState([
    { id: 'sales_revenue', name: 'Sales Revenue', color: '#10B981', auto_rules: ['invoice', 'sale', 'payment received'] },
    { id: 'service_revenue', name: 'Service Revenue', color: '#3B82F6', auto_rules: ['service', 'consultation', 'subscription'] },
    { id: 'operating_expenses', name: 'Operating Expenses', color: '#EF4444', auto_rules: ['expense', 'cost', 'purchase'] },
    { id: 'salary_payments', name: 'Salary & Wages', color: '#8B5CF6', auto_rules: ['salary', 'wage', 'payroll'] },
    { id: 'tax_payments', name: 'Tax Payments', color: '#F59E0B', auto_rules: ['tax', 'vat', 'withholding'] },
    { id: 'loan_repayments', name: 'Loan Repayments', color: '#6B7280', auto_rules: ['loan', 'repayment', 'interest'] }
  ]);

  useEffect(() => {
    const currentUser = authService.getStoredUser();
    if (!currentUser || !authService.isAuthenticated()) {
      router.push('/auth/signin');
      return;
    }

    if (currentUser.service_package !== 'si') {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);
    OnboardingStateManager.updateStep(currentUser.id, 'reconciliation_setup');
  }, [router]);

  const handleRuleToggle = (ruleId: string) => {
    setReconciliationRules(prev => 
      prev.map(rule => 
        rule.id === ruleId 
          ? { ...rule, enabled: !rule.enabled }
          : rule
      )
    );
  };

  const handleMatchingCriteriaChange = (field: keyof MatchingCriteria, value: any) => {
    setMatchingCriteria(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNext = () => {
    if (currentStep === 'rules') {
      setCurrentStep('categories');
    } else if (currentStep === 'categories') {
      setCurrentStep('review');
    }
  };

  const handleBack = () => {
    if (currentStep === 'categories') {
      setCurrentStep('rules');
    } else if (currentStep === 'review') {
      setCurrentStep('categories');
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    
    try {
      console.log('🔧 Configuring reconciliation rules:', {
        rules: reconciliationRules.filter(r => r.enabled),
        matchingCriteria,
        categories: transactionCategories
      });

      // Simulate API call to save reconciliation configuration
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Update onboarding state
      OnboardingStateManager.updateStep(user.id, 'reconciliation_complete', true);
      OnboardingStateManager.completeOnboarding(user.id);

      // Navigate to dashboard
      router.push('/dashboard/si');
      
    } catch (error) {
      console.error('Reconciliation setup failed:', error);
      alert('Failed to configure reconciliation rules. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    OnboardingStateManager.completeOnboarding(user?.id);
    router.push('/dashboard/si');
  };

  const getRuleCategoryColor = (category: string) => {
    const colors = {
      'transaction_matching': 'bg-blue-100 text-blue-800',
      'categorization': 'bg-green-100 text-green-800',
      'fraud_detection': 'bg-red-100 text-red-800',
      'compliance': 'bg-purple-100 text-purple-800'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getStepProgress = () => {
    const steps = ['rules', 'categories', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    return ((currentIndex + 1) / steps.length) * 100;
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-purple-100 p-3 rounded-2xl mr-4">
              <span className="text-3xl">⚖️</span>
            </div>
            <div className="text-left">
              <h1 className="text-3xl font-bold text-gray-900">
                Auto-Reconciliation Setup
              </h1>
              <p className="text-purple-600 font-medium text-lg">Smart Transaction Matching & Categorization</p>
            </div>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Configure intelligent rules to automatically match, categorize, and reconcile your financial transactions
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Setup Progress</span>
            <span className="text-sm text-gray-600">{Math.round(getStepProgress())}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getStepProgress()}%` }}
            ></div>
          </div>
        </div>

        {/* Step Indicators */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center ${currentStep === 'rules' ? 'text-purple-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                currentStep === 'rules' ? 'bg-purple-600 text-white' : 'bg-gray-200'
              }`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium">Matching Rules</span>
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'categories' ? 'text-purple-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                currentStep === 'categories' ? 'bg-purple-600 text-white' : 'bg-gray-200'
              }`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium">Categories</span>
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'review' ? 'text-purple-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                currentStep === 'review' ? 'bg-purple-600 text-white' : 'bg-gray-200'
              }`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium">Review</span>
            </div>
          </div>
        </div>

        {/* Step 1: Matching Rules */}
        {currentStep === 'rules' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Transaction Matching Criteria</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TaxPoyntInput
                  label="Amount Tolerance (%)"
                  type="number"
                  value={matchingCriteria.amount_tolerance}
                  onChange={(e) => handleMatchingCriteriaChange('amount_tolerance', parseFloat(e.target.value))}
                  min="0"
                  max="10"
                  step="0.01"
                />
                <TaxPoyntInput
                  label="Date Range (Days)"
                  type="number"
                  value={matchingCriteria.date_range_days}
                  onChange={(e) => handleMatchingCriteriaChange('date_range_days', parseInt(e.target.value))}
                  min="1"
                  max="30"
                />
              </div>
              <div className="mt-6 space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={matchingCriteria.reference_matching}
                    onChange={(e) => handleMatchingCriteriaChange('reference_matching', e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  />
                  <span className="ml-3 text-gray-900">Enable reference number matching</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={matchingCriteria.narration_matching}
                    onChange={(e) => handleMatchingCriteriaChange('narration_matching', e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  />
                  <span className="ml-3 text-gray-900">Enable narration/description matching</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={matchingCriteria.account_matching}
                    onChange={(e) => handleMatchingCriteriaChange('account_matching', e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  />
                  <span className="ml-3 text-gray-900">Enable account-based matching</span>
                </label>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Reconciliation Rules</h3>
              <div className="space-y-4">
                {reconciliationRules.map((rule) => (
                  <div key={rule.id} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <input
                          type="checkbox"
                          checked={rule.enabled}
                          onChange={() => handleRuleToggle(rule.id)}
                          className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <div>
                          <h4 className="font-semibold text-gray-900">{rule.name}</h4>
                          <p className="text-sm text-gray-600">{rule.description}</p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 text-xs rounded-full font-medium ${getRuleCategoryColor(rule.category)}`}>
                        {rule.category.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Categories */}
        {currentStep === 'categories' && (
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Transaction Categories</h3>
            <p className="text-gray-600 mb-6">Configure automatic categorization rules for your transactions</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {transactionCategories.map((category) => (
                <div key={category.id} className="border border-gray-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div 
                        className="w-4 h-4 rounded-full mr-3"
                        style={{ backgroundColor: category.color }}
                      ></div>
                      <h4 className="font-semibold text-gray-900">{category.name}</h4>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Auto-detection keywords:</p>
                    <div className="flex flex-wrap gap-1">
                      {category.auto_rules.map((rule, index) => (
                        <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {rule}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {currentStep === 'review' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Configuration Summary</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Matching Criteria</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Amount tolerance: {matchingCriteria.amount_tolerance}%</li>
                    <li>• Date range: {matchingCriteria.date_range_days} days</li>
                    <li>• Reference matching: {matchingCriteria.reference_matching ? 'Enabled' : 'Disabled'}</li>
                    <li>• Narration matching: {matchingCriteria.narration_matching ? 'Enabled' : 'Disabled'}</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Active Rules</h4>
                  <p className="text-sm text-gray-600">
                    {reconciliationRules.filter(r => r.enabled).length} of {reconciliationRules.length} rules enabled
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
              <div className="flex items-start">
                <span className="text-green-500 mr-3 text-2xl">✅</span>
                <div>
                  <h3 className="text-green-900 font-semibold mb-2">Ready to Activate</h3>
                  <p className="text-green-800 text-sm leading-relaxed">
                    Your reconciliation rules are configured and ready to process transactions automatically. 
                    The system will start monitoring and matching transactions immediately after activation.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center mt-8">
          <div>
            {currentStep !== 'rules' && (
              <TaxPoyntButton
                variant="secondary"
                onClick={handleBack}
                disabled={isLoading}
              >
                Back
              </TaxPoyntButton>
            )}
          </div>
          
          <div className="flex space-x-4">
            <TaxPoyntButton
              variant="secondary"
              onClick={handleSkip}
              disabled={isLoading}
            >
              Skip for Now
            </TaxPoyntButton>
            
            {currentStep === 'review' ? (
              <TaxPoyntButton
                variant="primary"
                onClick={handleComplete}
                loading={isLoading}
                className="px-8"
              >
                Activate Reconciliation
              </TaxPoyntButton>
            ) : (
              <TaxPoyntButton
                variant="primary"
                onClick={handleNext}
                disabled={isLoading}
                className="px-8"
              >
                Continue
              </TaxPoyntButton>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
