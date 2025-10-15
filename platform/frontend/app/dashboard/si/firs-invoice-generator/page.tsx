'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService, type User } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton } from '../../../../design_system';
import apiClient from '../../../../shared_components/api/client';

type V1Response<T> = {
  success: boolean;
  action: string;
  data: T;
  meta?: Record<string, any> | null;
};

interface ApiTransaction {
  id: string;
  source_type: string;
  source_name: string;
  transaction_id: string;
  date: string;
  customer_name: string;
  customer_email?: string | null;
  amount: number;
  currency: string;
  description: string;
  tax_amount: number;
  payment_status: string;
  payment_method?: string | null;
  firs_status: string;
  confidence: number;
  irn?: string | null;
}

interface SearchTransactionsResponse {
  transactions: ApiTransaction[];
  total_count: number;
  filters_applied: Record<string, any>;
}

interface ErpConnectionRecord {
  connection_id: string;
  erp_system: string;
  connection_name?: string;
  environment: string;
  status?: string;
  connection_config?: {
    auto_sync?: boolean;
    polling_interval?: number;
    [key: string]: any;
  };
  metadata?: Record<string, any>;
  last_status_at?: string | null;
}

interface ListErpConnectionsResponse {
  connections: ErpConnectionRecord[];
  total_count: number;
}

interface GenerationStats {
  invoices_generated?: number;
  consolidation_used?: boolean;
  total_transactions?: number;
  processing_time_seconds?: number;
  [key: string]: any;
}

interface GeneratedInvoice {
  irn: string;
  invoice_number: string;
  customer_name: string;
  total_amount: number;
  tax_amount: number;
  currency: string;
  invoice_date: string;
  status: string;
}

interface GenerationResult {
  success: boolean;
  invoices: GeneratedInvoice[];
  total_amount: number;
  errors: string[];
  warnings: string[];
  generation_stats: GenerationStats;
}

interface BusinessTransaction {
  id: string;
  sourceType: string;
  sourceName: string;
  transactionId: string;
  date: string;
  customerName: string;
  customerEmail?: string;
  amount: number;
  currency: string;
  description: string;
  taxAmount: number;
  paymentStatus: string;
  paymentMethod?: string;
  firsStatus: string;
  confidence: number;
  irn?: string | null;
}

const statusClasses: Record<string, string> = {
  not_generated: 'text-orange-600 bg-orange-50 border border-orange-200',
  generated: 'text-blue-600 bg-blue-50 border border-blue-200',
  submitted: 'text-purple-600 bg-purple-50 border border-purple-200',
  accepted: 'text-green-600 bg-green-50 border border-green-200',
  rejected: 'text-red-600 bg-red-50 border border-red-200',
};

const paymentStatusClasses: Record<string, string> = {
  paid: 'text-green-600 bg-green-50 border border-green-200',
  pending: 'text-orange-600 bg-orange-50 border border-orange-200',
  partial: 'text-blue-600 bg-blue-50 border border-blue-200',
  failed: 'text-red-600 bg-red-50 border border-red-200',
};

const formatCurrency = (amount: number, currency: string) => {
  try {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: currency || 'NGN',
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
};

const formatDate = (iso: string) => {
  try {
    const date = new Date(iso);
    return new Intl.DateTimeFormat('en-NG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  } catch {
    return iso;
  }
};

const statusBadge = (status: string, classes: Record<string, string>) => {
  const key = status?.toLowerCase();
  const base = classes[key] || 'text-slate-600 bg-slate-100 border border-slate-200';
  const label = status.replace(/_/g, ' ');
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${base}`}>
      {label}
    </span>
  );
};

export default function FIRSInvoiceGeneratorPage(): JSX.Element | null {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<BusinessTransaction[]>([]);
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  const [connections, setConnections] = useState<ErpConnectionRecord[]>([]);

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
    loadInitialData(currentUser);
  }, [router]);

  const loadInitialData = async (currentUser: User) => {
    setIsLoading(true);
    setError(null);
    try {
      const transactionPromise = apiClient.post<V1Response<SearchTransactionsResponse>>(
        '/si/firs/invoices/transactions/search',
        {}
      );
      const connectionPromise = currentUser.organization?.id
        ? apiClient.get<V1Response<ListErpConnectionsResponse>>(
            `/si/business/erp/connections?organization_id=${encodeURIComponent(
              currentUser.organization.id
            )}`
          )
        : Promise.resolve<V1Response<ListErpConnectionsResponse>>({
            success: true,
            action: 'erp_connections_listed',
            data: { connections: [], total_count: 0 },
            meta: null,
          });

      const [transactionsResponse, connectionsResponse] = await Promise.all([
        transactionPromise,
        connectionPromise,
      ]);

      const txItems = transactionsResponse.data?.transactions ?? [];
      const mappedTransactions: BusinessTransaction[] = txItems.map((item) => ({
        id: item.id,
        sourceType: item.source_type,
        sourceName: item.source_name,
        transactionId: item.transaction_id,
        date: item.date,
        customerName: item.customer_name,
        customerEmail: item.customer_email || undefined,
        amount: item.amount,
        currency: item.currency || 'NGN',
        description: item.description,
        taxAmount: item.tax_amount,
        paymentStatus: item.payment_status,
        paymentMethod: item.payment_method || undefined,
        firsStatus: item.firs_status,
        confidence: item.confidence,
        irn: item.irn,
      }));

      setTransactions(mappedTransactions);
      setConnections(connectionsResponse.data?.connections ?? []);
    } catch (err: any) {
      console.error('Failed to load invoice generator data:', err);
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'Unable to load business transactions. Try refreshing the page.';
      setError(message);
      setTransactions([]);
    } finally {
      setIsLoading(false);
      setSelectedTransactions([]);
    }
  };

  const toggleTransactionSelection = (transactionId: string) => {
    setSelectedTransactions((prev) =>
      prev.includes(transactionId) ? prev.filter((id) => id !== transactionId) : [...prev, transactionId]
    );
  };

  const toggleAllTransactions = () => {
    if (selectedTransactions.length === transactions.length) {
      setSelectedTransactions([]);
    } else {
      setSelectedTransactions(transactions.map((transaction) => transaction.id));
    }
  };

  const handleGenerateInvoices = async () => {
    if (!selectedTransactions.length) {
      setGenerationResult({
        success: false,
        invoices: [],
        total_amount: 0,
        errors: ['Select at least one transaction before generating.'],
        warnings: [],
        generation_stats: {},
      });
      return;
    }

    setIsGenerating(true);
    setGenerationResult(null);
    try {
      const response = await apiClient.post<V1Response<GenerationResult>>('/si/firs/invoices/generate', {
        transaction_ids: selectedTransactions,
        include_digital_signature: true,
        consolidate: false,
      });
      setGenerationResult(response.data);
      await loadInitialData(user!);
    } catch (err: any) {
      console.error('Invoice generation failed:', err);
      setGenerationResult({
        success: false,
        invoices: [],
        total_amount: 0,
        errors: [
          err?.response?.data?.detail ||
            err?.message ||
            'Unable to generate invoices. Please try again later.',
        ],
        warnings: [],
        generation_stats: {},
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const summary = useMemo(() => {
    const totals = {
      total: transactions.length,
      pending: transactions.filter((t) => t.firsStatus === 'not_generated').length,
      amountPending: transactions
        .filter((t) => t.firsStatus === 'not_generated')
        .reduce((sum, t) => sum + t.amount, 0),
      selectedAmount: transactions
        .filter((t) => selectedTransactions.includes(t.id))
        .reduce((sum, t) => sum + t.amount, 0),
    };
    return totals;
  }, [transactions, selectedTransactions]);

  if (!user) {
    return null;
  }

  return (
    <DashboardLayout
      role="si"
      userName={`${user.first_name} ${user.last_name}`}
      userEmail={user.email}
      activeTab="firs-invoice-generator"
    >
      <div className="space-y-8">
        <header className="rounded-3xl border border-indigo-100 bg-white/80 p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-indigo-900">FIRS Invoice Generator</h1>
              <p className="mt-1 text-sm text-slate-600">
                Review synced transactions, select the invoices you want to clear, and generate IRNs
                with a single workflow.
              </p>
            </div>
            <div className="flex gap-3">
              <TaxPoyntButton variant="outline" onClick={() => router.push('/dashboard/si/business-systems')}>
                Manage integrations
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="primary"
                onClick={handleGenerateInvoices}
                disabled={!transactions.length || !selectedTransactions.length || isGenerating}
              >
                {isGenerating ? 'Generating…' : `Generate IRNs (${selectedTransactions.length})`}
              </TaxPoyntButton>
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Transactions loaded</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.total}</p>
            <p className="mt-1 text-sm text-slate-600">Across all connected ERP sources.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Pending IRN</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.pending}</p>
            <p className="mt-1 text-sm text-slate-600">
              {formatCurrency(summary.amountPending, 'NGN')} awaiting generation.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Selected amount</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {formatCurrency(summary.selectedAmount, 'NGN')}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              {selectedTransactions.length} transaction{selectedTransactions.length === 1 ? '' : 's'} ready.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-500">Auto-sync connections</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {
                connections.filter(
                  (conn) =>
                    conn.connection_config?.auto_sync ||
                    conn.metadata?.auto_sync ||
                    conn.connection_config?.enable_auto_sync
                ).length
              }
            </p>
            <p className="mt-1 text-sm text-slate-600">
              Out of {connections.length} total ERP connections.
            </p>
          </div>
        </section>

        {generationResult && (
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Latest generation result</h2>
            <div
              className={`mt-4 rounded-xl border p-4 text-sm ${
                generationResult.success
                  ? 'border-green-200 bg-green-50 text-green-700'
                  : 'border-red-200 bg-red-50 text-red-700'
              }`}
            >
              {generationResult.success ? (
                <>
                  <p className="font-medium">
                    Generated {generationResult.invoices.length} invoice
                    {generationResult.invoices.length === 1 ? '' : 's'} worth{' '}
                    {formatCurrency(generationResult.total_amount, 'NGN')}.
                  </p>
                  {generationResult.generation_stats?.processing_time_seconds && (
                    <p className="mt-1 text-xs text-slate-600">
                      Processing time:{' '}
                      {generationResult.generation_stats.processing_time_seconds.toFixed(1)}s
                    </p>
                  )}
                </>
              ) : (
                <>
                  <p className="font-medium">Generation failed.</p>
                  {generationResult.errors.map((error, idx) => (
                    <p key={idx} className="mt-1">
                      • {error}
                    </p>
                  ))}
                </>
              )}
              {generationResult.warnings?.length > 0 && (
                <div className="mt-2 text-xs text-amber-700">
                  <p className="font-medium">Warnings:</p>
                  {generationResult.warnings.map((warning, idx) => (
                    <p key={idx}>• {warning}</p>
                  ))}
                </div>
              )}
            </div>
            {generationResult.invoices.length > 0 && (
              <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                        Invoice #
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                        IRN
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                        Customer
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                        Amount
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white text-sm text-slate-700">
                    {generationResult.invoices.map((invoice) => (
                      <tr key={invoice.irn}>
                        <td className="px-4 py-2 font-medium text-slate-900">{invoice.invoice_number}</td>
                        <td className="px-4 py-2 text-xs text-slate-600 break-all">{invoice.irn}</td>
                        <td className="px-4 py-2">{invoice.customer_name}</td>
                        <td className="px-4 py-2">
                          {formatCurrency(invoice.total_amount, invoice.currency)}
                        </td>
                        <td className="px-4 py-2">
                          {statusBadge(invoice.status || 'generated', statusClasses)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Business transactions</h2>
              <p className="text-sm text-slate-600">
                Select the transactions you want to clear today. You can filter by status or payment method.
              </p>
            </div>
            <div className="flex gap-2">
              <TaxPoyntButton variant="outline" size="sm" onClick={toggleAllTransactions}>
                {selectedTransactions.length === transactions.length && transactions.length > 0
                  ? 'Clear selection'
                  : 'Select all'}
              </TaxPoyntButton>
              <TaxPoyntButton
                variant="outline"
                size="sm"
                onClick={() => user && loadInitialData(user)}
              >
                Refresh data
              </TaxPoyntButton>
            </div>
          </div>

          {isLoading ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
            </div>
          ) : error ? (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
              {error}
            </div>
          ) : transactions.length === 0 ? (
            <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-6 text-slate-600">
              <p className="font-medium text-slate-800">No synced transactions yet.</p>
              <p className="mt-2 text-sm">
                Connect an ERP system and run a sync from the Business Systems dashboard to populate
                transactions here.
              </p>
            </div>
          ) : (
            <div className="mt-6 overflow-hidden rounded-xl border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedTransactions.length === transactions.length && transactions.length > 0}
                        onChange={toggleAllTransactions}
                        className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      Transaction
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      Source
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium uppercase tracking-wide text-slate-500">
                      Amount
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      Payment
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      FIRS status
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      Confidence
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white text-sm text-slate-700">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedTransactions.includes(transaction.id)}
                          onChange={() => toggleTransactionSelection(transaction.id)}
                          className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{transaction.transactionId}</div>
                        <div className="text-xs text-slate-500">
                          {transaction.customerName} • {formatDate(transaction.date)}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium">{transaction.sourceName}</div>
                        <div className="text-xs uppercase text-slate-500">{transaction.sourceType}</div>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-900">
                        {formatCurrency(transaction.amount, transaction.currency)}
                      </td>
                      <td className="px-4 py-3">
                        {statusBadge(transaction.paymentStatus, paymentStatusClasses)}
                        {transaction.paymentMethod && (
                          <div className="mt-1 text-xs text-slate-500">{transaction.paymentMethod}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {statusBadge(transaction.firsStatus, statusClasses)}
                        {transaction.irn && (
                          <div className="mt-1 text-xs text-slate-500 break-all">IRN: {transaction.irn}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-slate-900">
                          {transaction.confidence.toFixed(1)}%
                        </div>
                        <div className="text-xs text-slate-500">Data confidence</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}
