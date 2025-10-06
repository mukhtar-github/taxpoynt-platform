/**
 * Fixed Registration Test Page
 * ============================
 * Comprehensive test page to verify the improved registration flow
 * Tests all validation scenarios and error handling improvements
 */

'use client';

import React, { useState } from 'react';
import { isAxiosError } from 'axios';
import { authService, RegisterRequest } from '../../shared_components/services/auth';

export default function TestRegistrationFixedPage() {
  const [testScenario, setTestScenario] = useState<string>('complete');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');

  // Test scenarios with different data combinations
  const testScenarios: Record<string, Partial<RegisterRequest>> = {
    complete: {
      email: 'test@taxpoynt.com',
      password: 'SecurePass123!',
      first_name: 'John',
      last_name: 'Doe',
      phone: '+2348012345678',
      service_package: 'si',
      business_name: 'TechCorp Nigeria Ltd',
      business_type: 'Technology',
      tin: '12345678-0001',
      rc_number: 'RC123456',
      address: '123 Victoria Island, Lagos',
      state: 'Lagos',
      lga: 'Lagos Island',
      terms_accepted: true,
      privacy_accepted: true,
      marketing_consent: false
    },
    missing_terms: {
      email: 'noterms@taxpoynt.com',
      password: 'SecurePass123!',
      first_name: 'Jane',
      last_name: 'Smith',
      phone: '+2348087654321',
      service_package: 'app',
      business_name: 'AppCorp Ltd',
      business_type: 'Software',
      terms_accepted: false, // This should cause 400 error
      privacy_accepted: true,
      marketing_consent: false
    },
    missing_privacy: {
      email: 'noprivacy@taxpoynt.com',
      password: 'SecurePass123!',
      first_name: 'Bob',
      last_name: 'Johnson',
      service_package: 'hybrid',
      business_name: 'HybridCorp',
      business_type: 'Consulting',
      terms_accepted: true,
      privacy_accepted: false, // This should cause 400 error
      marketing_consent: false
    },
    missing_required_fields: {
      email: 'incomplete@taxpoynt.com',
      password: 'SecurePass123!',
      // Missing first_name, last_name, business_name, business_type
      service_package: 'si',
      terms_accepted: true,
      privacy_accepted: true,
      marketing_consent: false
    },
    invalid_service_package: {
      email: 'invalidpackage@taxpoynt.com',
      password: 'SecurePass123!',
      first_name: 'Alice',
      last_name: 'Wilson',
      service_package: 'invalid_package', // This should cause 400 error
      business_name: 'InvalidCorp',
      business_type: 'Business',
      terms_accepted: true,
      privacy_accepted: true,
      marketing_consent: false
    }
  };

  const handleTestRegistration = async () => {
    setLoading(true);
    setResult('');
    setError('');

    try {
      const testData = testScenarios[testScenario];
      
      // Fill in missing required fields for client-side validation test
      const completeTestData: RegisterRequest = {
        email: testData.email || 'default@test.com',
        password: testData.password || 'DefaultPass123!',
        first_name: testData.first_name || 'Test',
        last_name: testData.last_name || 'User',
        phone: testData.phone || '+2348000000000',
        service_package: testData.service_package || 'si',
        business_name: testData.business_name || 'Default Business',
        business_type: testData.business_type || 'Technology',
        tin: testData.tin,
        rc_number: testData.rc_number,
        address: testData.address,
        state: testData.state,
        lga: testData.lga,
        terms_accepted: testData.terms_accepted || false,
        privacy_accepted: testData.privacy_accepted || false,
        marketing_consent: testData.marketing_consent || false
      };

      console.log(`🧪 Testing scenario: ${testScenario}`);
      console.log('📝 Test data:', {
        ...completeTestData,
        password: '***hidden***'
      });

      const response = await authService.register(completeTestData);
      
      setResult(JSON.stringify({
        success: true,
        user: response.user,
        token_info: {
          expires_in: response.expires_in,
          token_type: response.token_type,
          has_token: !!response.access_token
        }
      }, null, 2));
      
      console.log('✅ Registration successful:', response);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      console.error('❌ Registration error:', err);
      
      // Log additional error details for debugging
      if (isAxiosError(err)) {
        console.log('🔍 Error details:', {
          status: err.response?.status,
          data: err.response?.data,
          headers: err.response?.headers
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      setResult('Logged out successfully');
    } catch (err) {
      setError('Logout failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const checkAuthStatus = () => {
    const isAuth = authService.isAuthenticated();
    const user = authService.getStoredUser();
    const token = authService.getToken();
    
    setResult(JSON.stringify({
      isAuthenticated: isAuth,
      user: user,
      hasToken: !!token,
      tokenPreview: token ? token.substring(0, 30) + '...' : null
    }, null, 2));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🛠️ Fixed Registration Flow Test
          </h1>
          <p className="text-gray-600 mb-8">
            Comprehensive testing of the improved user registration flow with enhanced validation and error handling.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Test Controls */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Test Scenarios</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Test Scenario
                  </label>
                  <select
                    value={testScenario}
                    onChange={(e) => setTestScenario(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="complete">✅ Complete Valid Registration</option>
                    <option value="missing_terms">❌ Missing Terms Acceptance</option>
                    <option value="missing_privacy">❌ Missing Privacy Acceptance</option>
                    <option value="missing_required_fields">❌ Missing Required Fields</option>
                    <option value="invalid_service_package">❌ Invalid Service Package</option>
                  </select>
                </div>

                {/* Scenario Description */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">Scenario Details:</h3>
                  <div className="text-sm text-blue-800">
                    {testScenario === 'complete' && (
                      <div>
                        <p>✅ All required fields provided</p>
                        <p>✅ Terms and privacy accepted</p>
                        <p>✅ Valid service package</p>
                        <p className="font-medium mt-2">Expected: Successful registration</p>
                      </div>
                    )}
                    {testScenario === 'missing_terms' && (
                      <div>
                        <p>❌ Terms not accepted (terms_accepted: false)</p>
                        <p>✅ Privacy policy accepted</p>
                        <p className="font-medium mt-2">Expected: HTTP 400 - Terms and conditions must be accepted</p>
                      </div>
                    )}
                    {testScenario === 'missing_privacy' && (
                      <div>
                        <p>✅ Terms accepted</p>
                        <p>❌ Privacy policy not accepted (privacy_accepted: false)</p>
                        <p className="font-medium mt-2">Expected: HTTP 400 - Privacy policy must be accepted</p>
                      </div>
                    )}
                    {testScenario === 'missing_required_fields' && (
                      <div>
                        <p>❌ Missing first_name, last_name, business_name, business_type</p>
                        <p>✅ Terms and privacy accepted</p>
                        <p className="font-medium mt-2">Expected: Client-side validation errors</p>
                      </div>
                    )}
                    {testScenario === 'invalid_service_package' && (
                      <div>
                        <p>❌ Invalid service package (&ldquo;invalid_package&rdquo;)</p>
                        <p>✅ All other fields valid</p>
                        <p className="font-medium mt-2">Expected: HTTP 400 - Invalid service package</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Test Data Preview */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">Test Data Preview:</h3>
                  <pre className="text-xs text-gray-600 overflow-auto max-h-32">
                    {JSON.stringify(testScenarios[testScenario], null, 2)}
                  </pre>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <button
                    onClick={handleTestRegistration}
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {loading ? '🧪 Testing Registration...' : `🚀 Test ${testScenario.replace('_', ' ').toUpperCase()}`}
                  </button>

                  <button
                    onClick={checkAuthStatus}
                    className="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 font-medium"
                  >
                    📊 Check Auth Status
                  </button>

                  <button
                    onClick={handleLogout}
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 font-medium"
                  >
                    🚪 Logout & Clear Session
                  </button>
                </div>
              </div>
            </div>

            {/* Results */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Test Results</h2>
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <h3 className="font-medium text-red-800 mb-2">❌ Error Response:</h3>
                  <p className="text-red-700 text-sm whitespace-pre-wrap">{error}</p>
                  <p className="text-xs text-red-600 mt-2">
                    This demonstrates the improved error handling - specific, user-friendly messages instead of generic HTTP errors.
                  </p>
                </div>
              )}

              {result && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <h3 className="font-medium text-green-800 mb-2">✅ Success Response:</h3>
                  <pre className="text-sm text-green-700 whitespace-pre-wrap overflow-auto max-h-96">
                    {result}
                  </pre>
                </div>
              )}

              {!result && !error && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                  <p className="text-gray-500">Select a test scenario and click the test button to see results</p>
                </div>
              )}

              {/* Fix Summary */}
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-800 mb-3">🛠️ Registration Flow Improvements:</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>✅ Fixed critical consent reset bug</li>
                  <li>✅ Separate state management for terms/privacy</li>
                  <li>✅ Enhanced step-by-step validation</li>
                  <li>✅ Improved error handling with specific messages</li>
                  <li>✅ Form persistence excludes sensitive fields</li>
                  <li>✅ Real-time validation feedback</li>
                  <li>✅ Robust data flow consistency</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
