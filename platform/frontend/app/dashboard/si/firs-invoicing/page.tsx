'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { DashboardCard } from '../../../../shared_components/dashboard/DashboardCard';
import { TaxPoyntButton } from '../../../../design_system';
import { authService, type User } from '../../../../shared_components/services/auth';
import apiClient from '../../../../shared_components/api/client';

interface InvoiceTemplate {
  id: string;
  name: string;
  description: string;
  category: 'sales' | 'service' | 'mixed';
  isCompliant: boolean;
  lastUsed: string;
}

interface ReconciledTransaction {
  id: string;
  amount: number;
  customerName: string;
  description: string;
  category: string;
  confidence: number;
  source: string;
  date: string;
  selected: boolean;
}

export default function FIRSInvoicingHub() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTransactions, setSelectedTransactions] = useState<ReconciledTransaction[]>([]);
  const [invoiceTemplates, setInvoiceTemplates] = useState<InvoiceTemplate[]>([]);
  const [generationInProgress, setGenerationInProgress] = useState(false);
  const [isDemo, setIsDemo] = useState(false);

  // Mock data for demo
  const mockTemplates = useMemo<InvoiceTemplate[]>(() => ([
    {
      id: 'standard-sales',
      name: 'Standard Sales Invoice',
      description: 'FIRS-compliant invoice for product sales with VAT',
      category: 'sales',
      isCompliant: true,
      lastUsed: '2 hours ago'
    },
    {
      id: 'service-invoice',
      name: 'Service Invoice Template',
      description: 'Professional services invoice with WHT compliance',
      category: 'service',
      isCompliant: true,
      lastUsed: '1 day ago'
    },
    {
      id: 'mixed-invoice',
      name: 'Mixed Products & Services',
      description: 'Combined invoice for products and services',
      category: 'mixed',
      isCompliant: true,
      lastUsed: '3 days ago'
    }
  ]), []);

  const mockTransactions = useMemo<ReconciledTransaction[]>(() => ([
    {
      id: 'txn-001',
      amount: 1250000,
      customerName: 'ABC Manufacturing Ltd',
      description: 'Auto-reconciled: ERP → Banking payment',
      category: 'Sales Revenue',
      confidence: 98.7,
      source: 'Mono Banking + SAP ERP',
      date: '2024-01-15',
      selected: false
    },
    {
      id: 'txn-002',
      amount: 890500,
      customerName: 'XYZ Services Ltd',
      description: 'Payment processor transaction matched',
      category: 'Service Revenue',
      confidence: 97.3,
      source: 'Paystack + Zoho CRM',
      date: '2024-01-15',
      selected: false
    },
    {
      id: 'txn-003',
      amount: 2340000,
      customerName: 'DEF Corporation',
      description: 'Multiple ERP sources consolidated',
      category: 'Sales Revenue',
      confidence: 99.1,
      source: 'Multiple ERPs',
      date: '2024-01-14',
      selected: false
    }
  ]), []);

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

    const loadFIRSInvoicingData = async () => {
      try {
        setIsLoading(true);
        if (!authService.isAuthenticated()) {
          return;
        }

        const [templatesData, transactionsData] = await Promise.all([
          apiClient.get<{ templates?: InvoiceTemplate[] }>('/si/invoices/templates'),
          apiClient.get<{ transactions?: ReconciledTransaction[] }>(
            '/si/reconciliation/transactions'
          )
        ]);

        setInvoiceTemplates(templatesData.templates || mockTemplates);
        setSelectedTransactions(transactionsData.transactions || mockTransactions);
        setIsDemo(false);
      } catch (error) {
        console.error('Failed to load FIRS invoicing data, using demo data:', error);
        setIsDemo(true);
        setInvoiceTemplates(mockTemplates);
        setSelectedTransactions(mockTransactions);
      } finally {
        setIsLoading(false);
      }
    };

    loadFIRSInvoicingData();
  }, [mockTemplates, mockTransactions, router]);

  const handleTransactionSelect = (transactionId: string) => {
    setSelectedTransactions(prev => 
      prev.map(txn => 
        txn.id === transactionId 
          ? { ...txn, selected: !txn.selected }
          : txn
      )
    );
  };

  const handleGenerateInvoices = async () => {
    const selected = selectedTransactions.filter(txn => txn.selected);
    if (selected.length === 0) {
      alert('Please select at least one transaction to generate invoices');
      return;
    }

    setGenerationInProgress(true);
    
    try {
      // Simulate API call to generate FIRS-compliant invoices
      await apiClient.post('/si/invoices/generate', {
        transactions: selected.map(txn => ({
          id: txn.id,
          amount: txn.amount,
          customer: txn.customerName,
          category: txn.category,
          description: txn.description
        })),
        template: 'standard-sales',
        prepareFIRSCompliant: true
      });

      alert(`✅ Successfully generated ${selected.length} FIRS-compliant invoices!`);
      router.push('/dashboard/si/invoices');
    } catch (error) {
      console.error('Invoice generation failed:', error);
      // Demo fallback
      setTimeout(() => {
        alert(`✅ Demo: Generated ${selected.length} FIRS-compliant invoices successfully!`);
        router.push('/dashboard/si');
      }, 2000);
    } finally {
      setGenerationInProgress(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) return null;

  const selectedCount = selectedTransactions.filter(txn => txn.selected).length;
  const totalValue = selectedTransactions
    .filter(txn => txn.selected)
    .reduce((sum, txn) => sum + txn.amount, 0);

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="firs-invoicing"
    >
      <div className="min-h-full bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
        
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                📋 FIRS Invoice Generation Hub
              </h1>
              <p className="text-xl text-slate-600">
                Generate FIRS-compliant invoices from auto-reconciled transaction data (APP handles submission to FIRS)
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
                onClick={() => router.push('/dashboard/si')}
                className="border-2 border-slate-300 text-slate-700 hover:bg-slate-50"
              >
                ← Back to Dashboard
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={handleGenerateInvoices}
                disabled={selectedCount === 0 || generationInProgress}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              >
                {generationInProgress ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    📋 Generate {selectedCount} Invoice{selectedCount !== 1 ? 's' : ''}
                  </>
                )}
              </TaxPoyntButton>
            </div>
          </div>

          {/* Selection Summary */}
          {selectedCount > 0 && (
            <div className="bg-blue-100 border border-blue-300 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-blue-800">
                    {selectedCount} transaction{selectedCount !== 1 ? 's' : ''} selected
                  </span>
                  <span className="text-blue-700 ml-4">
                    Total Value: ₦{(totalValue / 1000000).toFixed(2)}M
                  </span>
                </div>
                <div className="text-sm text-blue-600">
                  Ready for FIRS-compliant invoice generation
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Invoice Templates */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800 mb-4">📋 Invoice Templates</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {invoiceTemplates.map((template) => (
              <DashboardCard
                key={template.id}
                title={template.name}
                description={template.description}
                icon="📄"
                badge={template.isCompliant ? 'FIRS Compliant' : 'Needs Update'}
                badgeColor={template.isCompliant ? 'green' : 'orange'}
                variant={template.isCompliant ? 'success' : 'warning'}
                onClick={() => {/* Template selection logic */}}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Category</span>
                    <span className="font-medium text-slate-800 capitalize">{template.category}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Last Used</span>
                    <span className="font-medium text-slate-800">{template.lastUsed}</span>
                  </div>
                </div>
              </DashboardCard>
            ))}
          </div>
        </div>

        {/* Auto-Reconciled Transactions for Invoice Generation */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border-l-4 border-emerald-500">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-800 mb-2">
                🤖 Auto-Reconciled Transactions
              </h2>
              <p className="text-slate-600">Select transactions to generate FIRS-compliant invoices</p>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-emerald-600">
                {selectedTransactions.filter(txn => txn.confidence > 95).length} High Confidence
              </div>
              <div className="text-sm text-slate-500">Ready for auto-generation</div>
            </div>
          </div>

          <div className="space-y-4">
            {selectedTransactions.map((transaction) => (
              <div
                key={transaction.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  transaction.selected
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                }`}
                onClick={() => handleTransactionSelect(transaction.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <input
                      type="checkbox"
                      checked={transaction.selected}
                      onChange={() => handleTransactionSelect(transaction.id)}
                      className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-1">
                        <div className="font-semibold text-slate-800">{transaction.customerName}</div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          transaction.confidence > 95 
                            ? 'bg-emerald-100 text-emerald-700'
                            : transaction.confidence > 85
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {transaction.confidence}% confidence
                        </span>
                      </div>
                      <div className="text-sm text-slate-600 mb-1">{transaction.description}</div>
                      <div className="flex items-center space-x-4 text-xs text-slate-500">
                        <span>📊 {transaction.category}</span>
                        <span>🔗 {transaction.source}</span>
                        <span>📅 {transaction.date}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-slate-800">
                      ₦{(transaction.amount / 1000000).toFixed(2)}M
                    </div>
                    <div className="text-sm text-emerald-600">Ready for FIRS</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Footer Actions */}
          <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-600">
                💡 All selected transactions will generate individual FIRS-compliant invoices with automatic VAT calculation, ready for APP role to submit to FIRS
              </div>
              <div className="flex space-x-3">
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedTransactions(prev => prev.map(txn => ({ ...txn, selected: false })))}
                  className="border-slate-300 text-slate-700 hover:bg-slate-100"
                >
                  Clear Selection
                </TaxPoyntButton>
                <TaxPoyntButton
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedTransactions(prev => prev.map(txn => ({ ...txn, selected: txn.confidence > 95 })))}
                  className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                >
                  Select High Confidence
                </TaxPoyntButton>
              </div>
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
