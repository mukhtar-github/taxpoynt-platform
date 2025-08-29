'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../design_system';

interface InvoiceSource {
  id: string;
  type: 'erp' | 'crm' | 'pos' | 'ecommerce' | 'banking' | 'payment';
  name: string;
  status: 'connected' | 'disconnected';
  lastSync: string;
  recordCount: number;
}

interface BusinessTransaction {
  id: string;
  source: InvoiceSource;
  transactionId: string;
  date: string;
  customerName: string;
  customerEmail?: string;
  amount: number;
  currency: string;
  description: string;
  lineItems: LineItem[];
  taxAmount: number;
  vatRate: number;
  paymentStatus: 'pending' | 'paid' | 'partial' | 'failed';
  paymentMethod?: string;
  firsStatus: 'not_generated' | 'generated' | 'submitted' | 'accepted' | 'rejected';
  irn?: string;
  confidence: number; // Auto-reconciliation confidence
}

interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  taxRate: number;
  taxAmount: number;
}

interface FIRSInvoiceRequest {
  transactionIds: string[];
  invoiceType: 'standard' | 'credit_note' | 'debit_note';
  consolidate: boolean;
  overrides?: {
    customerName?: string;
    customerEmail?: string;
    dueDate?: string;
  };
}

export default function FIRSInvoiceGeneratorPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [connectedSources, setConnectedSources] = useState<InvoiceSource[]>([]);
  const [transactions, setTransactions] = useState<BusinessTransaction[]>([]);
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);
  const [filterSource, setFilterSource] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('not_generated');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<any>(null);

  // Mock data for comprehensive business and financial system integration
  const mockSources: InvoiceSource[] = [
    { id: 'sap-erp', type: 'erp', name: 'SAP ERP', status: 'connected', lastSync: '5 minutes ago', recordCount: 1456 },
    { id: 'odoo-erp', type: 'erp', name: 'Odoo ERP', status: 'connected', lastSync: '12 minutes ago', recordCount: 758 },
    { id: 'salesforce-crm', type: 'crm', name: 'Salesforce CRM', status: 'connected', lastSync: '8 minutes ago', recordCount: 234 },
    { id: 'square-pos', type: 'pos', name: 'Square POS', status: 'connected', lastSync: '3 minutes ago', recordCount: 89 },
    { id: 'shopify-pos', type: 'pos', name: 'Shopify POS', status: 'connected', lastSync: '7 minutes ago', recordCount: 56 },
    { id: 'shopify-store', type: 'ecommerce', name: 'Shopify Store', status: 'connected', lastSync: '4 minutes ago', recordCount: 342 },
    { id: 'mono-banking', type: 'banking', name: 'Mono Banking', status: 'connected', lastSync: '2 minutes ago', recordCount: 2456 },
    { id: 'paystack', type: 'payment', name: 'Paystack', status: 'connected', lastSync: '1 minute ago', recordCount: 1234 },
    { id: 'flutterwave', type: 'payment', name: 'Flutterwave', status: 'connected', lastSync: '6 minutes ago', recordCount: 567 }
  ];

  const mockTransactions: BusinessTransaction[] = [
    {
      id: 'txn-001',
      source: mockSources[0], // SAP ERP
      transactionId: 'SAP-INV-2024-1456',
      date: '2024-01-15T10:30:00Z',
      customerName: 'Acme Corporation Ltd',
      customerEmail: 'finance@acmecorp.ng',
      amount: 2500000,
      currency: 'NGN',
      description: 'Software License and Support Services',
      lineItems: [
        { description: 'Software License (Annual)', quantity: 1, unitPrice: 2000000, total: 2000000, taxRate: 7.5, taxAmount: 150000 },
        { description: 'Support Services', quantity: 1, unitPrice: 350000, total: 350000, taxRate: 7.5, taxAmount: 26250 }
      ],
      taxAmount: 176250,
      vatRate: 7.5,
      paymentStatus: 'paid',
      paymentMethod: 'Bank Transfer',
      firsStatus: 'not_generated',
      confidence: 98.7
    },
    {
      id: 'txn-002',
      source: mockSources[2], // Salesforce CRM
      transactionId: 'SF-DEAL-789',
      date: '2024-01-15T14:45:00Z',
      customerName: 'Lagos Business Solutions',
      customerEmail: 'procurement@lbs.ng',
      amount: 1800000,
      currency: 'NGN',
      description: 'Business Consulting Services',
      lineItems: [
        { description: 'Strategy Consulting', quantity: 40, unitPrice: 35000, total: 1400000, taxRate: 7.5, taxAmount: 105000 },
        { description: 'Implementation Support', quantity: 8, unitPrice: 50000, total: 400000, taxRate: 7.5, taxAmount: 30000 }
      ],
      taxAmount: 135000,
      vatRate: 7.5,
      paymentStatus: 'paid',
      paymentMethod: 'Paystack',
      firsStatus: 'not_generated',
      confidence: 96.8
    },
    {
      id: 'txn-003',
      source: mockSources[3], // Square POS
      transactionId: 'SQ-SALE-456',
      date: '2024-01-15T16:20:00Z',
      customerName: 'Walk-in Customer',
      amount: 125000,
      currency: 'NGN',
      description: 'Retail Sale - Electronics',
      lineItems: [
        { description: 'Wireless Headphones', quantity: 2, unitPrice: 45000, total: 90000, taxRate: 7.5, taxAmount: 6750 },
        { description: 'Phone Case', quantity: 1, unitPrice: 35000, total: 35000, taxRate: 7.5, taxAmount: 2625 }
      ],
      taxAmount: 9375,
      vatRate: 7.5,
      paymentStatus: 'paid',
      paymentMethod: 'Card Payment',
      firsStatus: 'not_generated',
      confidence: 99.2
    },
    {
      id: 'txn-004',
      source: mockSources[5], // Shopify Store
      transactionId: 'SHOP-ORD-123',
      date: '2024-01-15T11:15:00Z',
      customerName: 'Online Customer',
      customerEmail: 'customer@email.com',
      amount: 89500,
      currency: 'NGN',
      description: 'E-commerce Order',
      lineItems: [
        { description: 'Product Bundle', quantity: 1, unitPrice: 75000, total: 75000, taxRate: 7.5, taxAmount: 5625 },
        { description: 'Shipping Fee', quantity: 1, unitPrice: 14500, total: 14500, taxRate: 7.5, taxAmount: 1087.5 }
      ],
      taxAmount: 6712.5,
      vatRate: 7.5,
      paymentStatus: 'paid',
      paymentMethod: 'Flutterwave',
      firsStatus: 'not_generated',
      confidence: 94.5
    },
    {
      id: 'txn-005',
      source: mockSources[6], // Mono Banking
      transactionId: 'MONO-TXN-890',
      date: '2024-01-15T09:30:00Z',
      customerName: 'Direct Bank Transfer Customer',
      amount: 450000,
      currency: 'NGN',
      description: 'Service Payment via Bank Transfer',
      lineItems: [
        { description: 'Professional Services', quantity: 1, unitPrice: 419000, total: 419000, taxRate: 7.5, taxAmount: 31425 }
      ],
      taxAmount: 31425,
      vatRate: 7.5,
      paymentStatus: 'paid',
      paymentMethod: 'Bank Transfer',
      firsStatus: 'not_generated',
      confidence: 87.3
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
    loadBusinessData();
  }, [router]);

  const loadBusinessData = async () => {
    setIsLoading(true);
    try {
      // In real implementation, fetch from APIs
      setConnectedSources(mockSources);
      setTransactions(mockTransactions);
    } catch (error) {
      console.error('Failed to load business data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSourceIcon = (type: string) => {
    const icons: Record<string, string> = {
      'erp': '🏢',
      'crm': '👥',
      'pos': '🛒',
      'ecommerce': '🌐',
      'banking': '🏦',
      'payment': '💳'
    };
    return icons[type] || '🔗';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'not_generated': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'generated': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'submitted': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'accepted': return 'text-green-600 bg-green-50 border-green-200';
      case 'rejected': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'text-green-600 bg-green-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'partial': return 'text-orange-600 bg-orange-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const filteredTransactions = transactions.filter(txn => {
    const sourceMatch = filterSource === 'all' || txn.source.type === filterSource;
    const statusMatch = filterStatus === 'all' || txn.firsStatus === filterStatus;
    return sourceMatch && statusMatch;
  });

  const handleTransactionSelect = (txnId: string) => {
    setSelectedTransactions(prev => 
      prev.includes(txnId) 
        ? prev.filter(id => id !== txnId)
        : [...prev, txnId]
    );
  };

  const generateFIRSInvoices = async () => {
    if (selectedTransactions.length === 0) {
      alert('Please select at least one transaction to generate FIRS invoice');
      return;
    }

    setIsGenerating(true);
    try {
      const selectedTxns = transactions.filter(txn => selectedTransactions.includes(txn.id));
      
      // Call FIRS invoice generation API
      const response = await fetch('/api/v1/si/firs/invoices/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transactionIds: selectedTransactions,
          invoiceType: 'standard',
          consolidate: selectedTransactions.length > 1,
          generateCompliant: true,
          includeDigitalSignature: true,
          sources: selectedTxns.map(txn => ({
            sourceId: txn.source.id,
            sourceType: txn.source.type,
            transactionId: txn.transactionId
          }))
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate FIRS invoice');
      }

      const result = await response.json();
      setGenerationResult(result);

      // Update transaction statuses
      setTransactions(prev => prev.map(txn => 
        selectedTransactions.includes(txn.id) 
          ? { ...txn, firsStatus: 'generated' as const, irn: result.invoices?.[0]?.irn }
          : txn
      ));

      setSelectedTransactions([]);
      alert(`✅ Successfully generated ${result.invoices?.length || 1} FIRS-compliant invoice(s)!`);

    } catch (error) {
      console.error('FIRS invoice generation failed:', error);
      alert('❌ Failed to generate FIRS invoice. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const totalSelectedAmount = transactions
    .filter(txn => selectedTransactions.includes(txn.id))
    .reduce((sum, txn) => sum + txn.amount, 0);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="firs-invoicing"
    >
      <div className="min-h-full bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-black text-slate-800 mb-2">
                📋 FIRS Invoice Generator
              </h1>
              <p className="text-xl text-slate-600">
                Generate FIRS-compliant invoices from aggregated business and financial system data
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
                onClick={generateFIRSInvoices}
                disabled={selectedTransactions.length === 0 || isGenerating}
                className={`${
                  selectedTransactions.length > 0 
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700' 
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    Generating...
                  </>
                ) : (
                  `🏛️ Generate FIRS Invoice${selectedTransactions.length > 1 ? 's' : ''} (${selectedTransactions.length})`
                )}
              </TaxPoyntButton>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-white p-4 rounded-xl shadow-md border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{connectedSources.length}</div>
              <div className="text-sm text-blue-700">Data Sources</div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-md border border-green-100">
              <div className="text-2xl font-bold text-green-600">{filteredTransactions.length}</div>
              <div className="text-sm text-green-700">Available Transactions</div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-md border border-purple-100">
              <div className="text-2xl font-bold text-purple-600">{selectedTransactions.length}</div>
              <div className="text-sm text-purple-700">Selected</div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-md border border-orange-100">
              <div className="text-2xl font-bold text-orange-600">
                ₦{(totalSelectedAmount / 1000000).toFixed(1)}M
              </div>
              <div className="text-sm text-orange-700">Total Value</div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-md border border-indigo-100">
              <div className="text-2xl font-bold text-indigo-600">
                {transactions.filter(t => t.firsStatus === 'not_generated').length}
              </div>
              <div className="text-sm text-indigo-700">Pending FIRS</div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex space-x-4 mb-6">
            <select 
              value={filterSource} 
              onChange={(e) => setFilterSource(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Sources</option>
              <option value="erp">ERP Systems</option>
              <option value="crm">CRM Systems</option>
              <option value="pos">POS Systems</option>
              <option value="ecommerce">E-commerce</option>
              <option value="banking">Banking</option>
              <option value="payment">Payment Processors</option>
            </select>
            
            <select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All FIRS Status</option>
              <option value="not_generated">Not Generated</option>
              <option value="generated">Generated</option>
              <option value="submitted">Submitted</option>
              <option value="accepted">Accepted</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>

        {/* Connected Sources Overview */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-gray-200">
          <h3 className="text-lg font-bold text-slate-800 mb-4">🔗 Connected Data Sources</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {connectedSources.map((source) => (
              <div key={source.id} className="text-center p-3 bg-gray-50 rounded-lg border">
                <div className="text-2xl mb-2">{getSourceIcon(source.type)}</div>
                <div className="text-sm font-medium text-slate-800">{source.name}</div>
                <div className="text-xs text-slate-600">{source.recordCount} records</div>
                <div className="text-xs text-green-600">{source.lastSync}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-bold text-slate-800">💼 Business Transactions Ready for FIRS</h3>
            <p className="text-sm text-slate-600">Select transactions to generate FIRS-compliant invoices</p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input 
                      type="checkbox" 
                      checked={selectedTransactions.length === filteredTransactions.length && filteredTransactions.length > 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedTransactions(filteredTransactions.map(t => t.id));
                        } else {
                          setSelectedTransactions([]);
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">FIRS Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input 
                        type="checkbox" 
                        checked={selectedTransactions.includes(transaction.id)}
                        onChange={() => handleTransactionSelect(transaction.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-lg mr-2">{getSourceIcon(transaction.source.type)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{transaction.source.name}</div>
                          <div className="text-xs text-gray-500 capitalize">{transaction.source.type}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{transaction.transactionId}</div>
                        <div className="text-xs text-gray-500">{new Date(transaction.date).toLocaleDateString()}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{transaction.customerName}</div>
                        {transaction.customerEmail && (
                          <div className="text-xs text-gray-500">{transaction.customerEmail}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">₦{transaction.amount.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">VAT: ₦{transaction.taxAmount.toLocaleString()}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getPaymentStatusColor(transaction.paymentStatus)}`}>
                        {transaction.paymentStatus}
                      </span>
                      {transaction.paymentMethod && (
                        <div className="text-xs text-gray-500 mt-1">{transaction.paymentMethod}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(transaction.firsStatus)}`}>
                        {transaction.firsStatus.replace('_', ' ')}
                      </span>
                      {transaction.irn && (
                        <div className="text-xs text-gray-500 mt-1">IRN: {transaction.irn}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{transaction.confidence}%</div>
                      <div className={`w-full bg-gray-200 rounded-full h-1 mt-1`}>
                        <div 
                          className={`h-1 rounded-full ${
                            transaction.confidence >= 95 ? 'bg-green-500' : 
                            transaction.confidence >= 85 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${transaction.confidence}%` }}
                        ></div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Generation Result Modal */}
        {generationResult && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl p-8 max-w-2xl w-full mx-4">
              <h3 className="text-2xl font-bold text-green-600 mb-4">✅ FIRS Invoice Generation Successful!</h3>
              
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-800 mb-2">Generated Invoices</h4>
                  {generationResult.invoices?.map((invoice: any, index: number) => (
                    <div key={index} className="text-sm text-green-700">
                      <div>IRN: <span className="font-mono">{invoice.irn}</span></div>
                      <div>Invoice Number: {invoice.invoiceNumber}</div>
                      <div>Amount: ₦{invoice.totalAmount?.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
                
                <div className="flex space-x-4">
                  <TaxPoyntButton
                    variant="primary"
                    onClick={() => setGenerationResult(null)}
                    className="flex-1"
                  >
                    Continue
                  </TaxPoyntButton>
                  <TaxPoyntButton
                    variant="outline"
                    onClick={() => {
                      // Download invoice logic
                      setGenerationResult(null);
                    }}
                    className="flex-1"
                  >
                    Download Invoice
                  </TaxPoyntButton>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </DashboardLayout>
  );
}
