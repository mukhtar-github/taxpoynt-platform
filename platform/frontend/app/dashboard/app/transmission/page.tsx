'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import { TaxPoyntAPIClient } from '../../../../shared_components/api/client';
import { APIResponse } from '../../../../si_interface/types';

interface InvoiceData {
  id: string;
  invoice_number: string;
  customer_name: string;
  amount: number;
  tax_amount: number;
  total_amount: number;
  date: string;
  status: 'draft' | 'validated' | 'submitted' | 'accepted' | 'rejected';
  firs_reference?: string;
  error_message?: string;
}

interface TransmissionBatch {
  id: string;
  created_at: string;
  invoice_count: number;
  total_amount: number;
  status: 'preparing' | 'validating' | 'transmitting' | 'completed' | 'failed';
  success_count: number;
  failed_count: number;
  firs_batch_id?: string;
  error_summary?: string;
}

export default function APPTransmissionPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'batches' | 'history'>('submit');
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);
  const [invoices, setInvoices] = useState<InvoiceData[]>([]);
  const [batches, setBatches] = useState<TransmissionBatch[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [transmissionStatus, setTransmissionStatus] = useState<'idle' | 'validating' | 'transmitting' | 'success' | 'error'>('idle');
  const [isDemo, setIsDemo] = useState(false);

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
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const apiClient = new TaxPoyntAPIClient();
      
      // Load pending invoices
      const invoicesResponse = await apiClient.get<APIResponse>('/api/v1/app/invoices/pending');
      const batchesResponse = await apiClient.get<APIResponse>('/api/v1/app/transmission/batches');
      
      if (invoicesResponse.success && batchesResponse.success) {
        setInvoices(invoicesResponse.data.invoices || []);
        setBatches(batchesResponse.data.batches || []);
        setIsDemo(false);
      } else {
        throw new Error('API response unsuccessful');
      }
    } catch (error) {
      console.error('Failed to load data, using demo data:', error);
      setIsDemo(true);
      // Set sample data for demonstration
      setInvoices([
        {
          id: '1',
          invoice_number: 'INV-2024-001',
          customer_name: 'ABC Corporation Ltd',
          amount: 1000000,
          tax_amount: 75000,
          total_amount: 1075000,
          date: '2024-12-31',
          status: 'validated'
        },
        {
          id: '2',
          invoice_number: 'INV-2024-002',
          customer_name: 'XYZ Enterprises',
          amount: 750000,
          tax_amount: 56250,
          total_amount: 806250,
          date: '2024-12-31',
          status: 'validated'
        },
        {
          id: '3',
          invoice_number: 'INV-2024-003',
          customer_name: 'Tech Solutions Nigeria',
          amount: 2500000,
          tax_amount: 187500,
          total_amount: 2687500,
          date: '2024-12-30',
          status: 'draft'
        }
      ]);

      setBatches([
        {
          id: 'BATCH-001',
          created_at: '2024-12-31T10:30:00Z',
          invoice_count: 25,
          total_amount: 45000000,
          status: 'completed',
          success_count: 25,
          failed_count: 0,
          firs_batch_id: 'FIRS-BATCH-20241231-001'
        },
        {
          id: 'BATCH-002',
          created_at: '2024-12-31T08:15:00Z',
          invoice_count: 18,
          total_amount: 32000000,
          status: 'transmitting',
          success_count: 0,
          failed_count: 0
        }
      ]);
    }
  };

  const handleInvoiceSelect = (invoiceId: string) => {
    setSelectedInvoices(prev => 
      prev.includes(invoiceId) 
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const handleSelectAll = () => {
    const validatedInvoices = invoices.filter(inv => inv.status === 'validated').map(inv => inv.id);
    setSelectedInvoices(
      selectedInvoices.length === validatedInvoices.length ? [] : validatedInvoices
    );
  };

  const submitToFIRS = async () => {
    if (selectedInvoices.length === 0) return;

    setIsLoading(true);
    setTransmissionStatus('validating');

    try {
      const apiClient = new TaxPoyntAPIClient();
      
      // First validate invoices
      const validationResponse = await apiClient.post<APIResponse>('/api/v1/app/firs/validate-batch', {
        invoice_ids: selectedInvoices
      });

      if (!validationResponse.success) {
        setTransmissionStatus('error');
        return;
      }

      setTransmissionStatus('transmitting');

      // Submit to FIRS
      const transmissionResponse = await apiClient.post<APIResponse>('/api/v1/app/firs/submit-batch', {
        invoice_ids: selectedInvoices,
        batch_settings: {
          environment: 'sandbox',
          auto_retry: true,
          webhook_notifications: true
        }
      });

      if (transmissionResponse.success) {
        setTransmissionStatus('success');
        setSelectedInvoices([]);
        
        // Refresh data
        await loadData();
        
        // Switch to batches tab to show progress
        setTimeout(() => setActiveTab('batches'), 2000);
      } else {
        setTransmissionStatus('error');
      }

    } catch (error) {
      console.error('FIRS submission failed:', error);
      setTransmissionStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredInvoices = invoices.filter(invoice =>
    invoice.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    invoice.customer_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN'
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      validated: 'bg-green-100 text-green-800',
      submitted: 'bg-blue-100 text-blue-800',
      accepted: 'bg-emerald-100 text-emerald-800',
      rejected: 'bg-red-100 text-red-800',
      preparing: 'bg-yellow-100 text-yellow-800',
      validating: 'bg-blue-100 text-blue-800',
      transmitting: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <DashboardLayout
      role="app"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="transmission"
    >
      <div className="min-h-full bg-gradient-to-br from-green-50 via-white to-emerald-50 p-6">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                FIRS Transmission Center 📤
              </h1>
              <p className="text-xl text-slate-600">
                Submit validated invoices to FIRS and monitor transmission status
                {isDemo && (
                  <span className="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
                    Demo Data
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex space-x-4">
              <TaxPoyntButton
                variant="outline"
                onClick={() => router.push('/dashboard/app/validation')}
                className="border-2 border-blue-300 text-blue-700 hover:bg-blue-50"
              >
                <span className="mr-2">✅</span>
                Validate Invoices
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={() => router.push('/dashboard/app/transmission/new')}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
              >
                <span className="mr-2">📋</span>
                New Transmission
              </TaxPoyntButton>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Ready to Submit', value: invoices.filter(i => i.status === 'validated').length, color: 'green' },
              { label: 'Selected', value: selectedInvoices.length, color: 'blue' },
              { label: 'Active Batches', value: batches.filter(b => ['preparing', 'validating', 'transmitting'].includes(b.status)).length, color: 'purple' },
              { label: 'Success Rate', value: '98.7%', color: 'emerald' }
            ].map((stat, index) => (
              <div key={index} className={`bg-white p-4 rounded-xl shadow-lg border border-${stat.color}-100`}>
                <div className={`text-2xl font-black text-${stat.color}-600 mb-1`}>
                  {stat.value}
                </div>
                <div className="text-sm text-slate-600 font-medium">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'submit', label: 'Submit Invoices', icon: '📤' },
                { id: 'batches', label: 'Transmission Batches', icon: '📦' },
                { id: 'history', label: 'History', icon: '📊' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-green-500 text-green-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            
            {/* Submit Tab */}
            {activeTab === 'submit' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Ready for FIRS Submission</h2>
                  <div className="flex items-center space-x-4">
                    <TaxPoyntInput
                      placeholder="Search invoices..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-64"
                    />
                    <TaxPoyntButton
                      variant="outline"
                      onClick={handleSelectAll}
                      size="sm"
                    >
                      {selectedInvoices.length === invoices.filter(i => i.status === 'validated').length ? 'Deselect All' : 'Select All'}
                    </TaxPoyntButton>
                  </div>
                </div>

                {transmissionStatus !== 'idle' && (
                  <div className={`mb-6 p-4 rounded-lg border ${
                    transmissionStatus === 'success' ? 'bg-green-50 border-green-200' :
                    transmissionStatus === 'error' ? 'bg-red-50 border-red-200' :
                    'bg-blue-50 border-blue-200'
                  }`}>
                    <div className="flex items-center">
                      {transmissionStatus === 'validating' && <span className="mr-2">🔍</span>}
                      {transmissionStatus === 'transmitting' && <span className="mr-2">📤</span>}
                      {transmissionStatus === 'success' && <span className="mr-2">✅</span>}
                      {transmissionStatus === 'error' && <span className="mr-2">❌</span>}
                      <span className={`font-medium ${
                        transmissionStatus === 'success' ? 'text-green-800' :
                        transmissionStatus === 'error' ? 'text-red-800' :
                        'text-blue-800'
                      }`}>
                        {transmissionStatus === 'validating' && 'Validating invoices against FIRS schema...'}
                        {transmissionStatus === 'transmitting' && 'Submitting to FIRS sandbox environment...'}
                        {transmissionStatus === 'success' && 'Successfully submitted to FIRS! Check Batches tab for details.'}
                        {transmissionStatus === 'error' && 'Transmission failed. Please check invoice data and try again.'}
                      </span>
                    </div>
                  </div>
                )}

                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <input
                            type="checkbox"
                            checked={selectedInvoices.length === invoices.filter(i => i.status === 'validated').length}
                            onChange={handleSelectAll}
                            className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tax</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredInvoices.map((invoice) => (
                        <tr key={invoice.id} className={`hover:bg-gray-50 ${selectedInvoices.includes(invoice.id) ? 'bg-green-50' : ''}`}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <input
                              type="checkbox"
                              checked={selectedInvoices.includes(invoice.id)}
                              onChange={() => handleInvoiceSelect(invoice.id)}
                              disabled={invoice.status !== 'validated'}
                              className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500 disabled:opacity-50"
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{invoice.invoice_number}</div>
                            <div className="text-sm text-gray-500">{invoice.date}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {invoice.customer_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(invoice.amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatCurrency(invoice.tax_amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {formatCurrency(invoice.total_amount)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>
                              {invoice.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {selectedInvoices.length > 0 && (
                  <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-green-800">
                          {selectedInvoices.length} invoices selected for FIRS submission
                        </h3>
                        <p className="text-sm text-green-600 mt-1">
                          Total value: {formatCurrency(
                            invoices
                              .filter(i => selectedInvoices.includes(i.id))
                              .reduce((sum, i) => sum + i.total_amount, 0)
                          )}
                        </p>
                      </div>
                      <TaxPoyntButton
                        variant="primary"
                        onClick={submitToFIRS}
                        loading={isLoading}
                        disabled={isLoading || transmissionStatus === 'transmitting'}
                        className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      >
                        Submit to FIRS Sandbox
                      </TaxPoyntButton>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Batches Tab */}
            {activeTab === 'batches' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Transmission Batches</h2>
                
                <div className="space-y-4">
                  {batches.map((batch) => (
                    <div key={batch.id} className="bg-gray-50 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{batch.id}</h3>
                          <p className="text-sm text-gray-600">
                            Created: {new Date(batch.created_at).toLocaleString()}
                          </p>
                        </div>
                        <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(batch.status)}`}>
                          {batch.status}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <div className="text-sm text-gray-600">Invoices</div>
                          <div className="text-lg font-medium text-gray-900">{batch.invoice_count}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Total Amount</div>
                          <div className="text-lg font-medium text-gray-900">{formatCurrency(batch.total_amount)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Successful</div>
                          <div className="text-lg font-medium text-green-600">{batch.success_count}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Failed</div>
                          <div className="text-lg font-medium text-red-600">{batch.failed_count}</div>
                        </div>
                      </div>

                      {batch.firs_batch_id && (
                        <div className="bg-white border border-gray-200 rounded p-3">
                          <div className="text-sm text-gray-600">FIRS Batch ID</div>
                          <div className="text-sm font-mono text-gray-900">{batch.firs_batch_id}</div>
                        </div>
                      )}

                      {batch.status === 'transmitting' && (
                        <div className="mt-4">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                          </div>
                          <p className="text-sm text-blue-600 mt-2">Transmitting to FIRS...</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Transmission History</h2>
                
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <div className="text-4xl mb-4">📊</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Transmission Analytics</h3>
                  <p className="text-gray-600 mb-4">
                    Detailed transmission history and analytics will be available here.
                  </p>
                  <TaxPoyntButton
                    variant="outline"
                    onClick={() => router.push('/dashboard/app/reports')}
                  >
                    View Reports
                  </TaxPoyntButton>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
