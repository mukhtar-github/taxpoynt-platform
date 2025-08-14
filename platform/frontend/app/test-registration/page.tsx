/**
 * Registration Test Page
 * ======================
 * Simple test page to verify frontend-backend authentication integration.
 * Tests complete user registration flow with the API Gateway.
 */

'use client';

import React, { useState } from 'react';
import { authService, RegisterRequest } from '../../shared_components/services/auth';

export default function TestRegistrationPage() {
  const [formData, setFormData] = useState<RegisterRequest>({
    email: 'test@example.com',
    password: 'password123',
    first_name: 'Test',
    last_name: 'User',
    phone: '+2348012345678',
    service_package: 'app',
    business_name: 'Test Business Ltd',
    business_type: 'Technology',
    tin: '12345678-0001',
    rc_number: 'RC123456',
    address: '123 Test Street, Lagos',
    state: 'Lagos',
    lga: 'Lagos Island',
    terms_accepted: true,
    privacy_accepted: true,
    marketing_consent: false
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult('');
    setError('');

    try {
      const response = await authService.register(formData);
      setResult(JSON.stringify(response, null, 2));
      console.log('Registration successful:', response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  const testLogin = async () => {
    setLoading(true);
    setResult('');
    setError('');

    try {
      const response = await authService.login({
        email: formData.email,
        password: formData.password,
        remember_me: false
      });
      setResult(JSON.stringify(response, null, 2));
      console.log('Login successful:', response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const testCurrentUser = async () => {
    setLoading(true);
    setResult('');
    setError('');

    try {
      const user = authService.getStoredUser();
      setResult(JSON.stringify(user, null, 2));
      console.log('Current user:', user);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get current user';
      setError(errorMessage);
      console.error('Current user error:', err);
    } finally {
      setLoading(false);
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
      token: token ? token.substring(0, 20) + '...' : null
    }, null, 2));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            TaxPoynt Authentication Test
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Test Form */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Test Registration Data</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Business Name
                  </label>
                  <input
                    type="text"
                    value={formData.business_name}
                    onChange={(e) => setFormData({...formData, business_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Package
                  </label>
                  <select
                    value={formData.service_package}
                    onChange={(e) => setFormData({...formData, service_package: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="si">System Integrator</option>
                    <option value="app">Access Point Provider</option>
                    <option value="hybrid">Hybrid Premium</option>
                  </select>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3 pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Testing Registration...' : 'Test Registration'}
                  </button>

                  <button
                    type="button"
                    onClick={testLogin}
                    disabled={loading}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Test Login
                  </button>

                  <button
                    type="button"
                    onClick={testCurrentUser}
                    disabled={loading}
                    className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Test Current User
                  </button>

                  <button
                    type="button"
                    onClick={checkAuthStatus}
                    className="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700"
                  >
                    Check Auth Status
                  </button>
                </div>
              </form>
            </div>

            {/* Results */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Test Results</h2>
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <h3 className="font-medium text-red-800 mb-2">Error:</h3>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              )}

              {result && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-medium text-green-800 mb-2">Success Response:</h3>
                  <pre className="text-sm text-green-700 whitespace-pre-wrap overflow-auto max-h-96">
                    {result}
                  </pre>
                </div>
              )}

              {!result && !error && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                  <p className="text-gray-500">Click a test button to see results</p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-800 mb-2">Integration Status:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>✅ Frontend auth service created</li>
                <li>✅ Backend API endpoints available</li>
                <li>✅ JWT token management implemented</li>
                <li>🧪 Ready for end-to-end testing</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}