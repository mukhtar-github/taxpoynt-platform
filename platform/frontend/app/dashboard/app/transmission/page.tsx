'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../../../shared_components/services/auth';
import { DashboardLayout } from '../../../../shared_components/layouts/DashboardLayout';
import { TaxPoyntButton, TaxPoyntInput } from '../../../../design_system';
import apiClient from '../../../../shared_components/api/client';
import { APIResponse } from '../../../../si_interface/types';

interface InvoiceData {
  id: string;
  invoice_number: string;
  customer_name?: string;
  amount?: number;
  tax_amount?: number;
  total_amount?: number;
  date?: string;
  status: string;
  firs_reference?: string;
  error_message?: string;
  retry_count?: number;
}

interface TransmissionBatch {
  id: string;
  created_at?: string;
  invoice_count: number;
  total_amount?: number;
  status: string;
  success_count?: number;
  failed_count?: number;
  firs_batch_id?: string;
  error_summary?: string;
  first_seen?: string;
  last_seen?: string;
}

interface ValidationBatchRecord {
  batchId?: string;
  status?: string;
  totals?: {
    total?: number;
    passed?: number;
    failed?: number;
  };
  createdAt?: string;
  errorSummary?: string;
}

interface ValidationHistorySnapshot {
  summary?: {
    totalBatches?: number;
    statusCounts?: Record<string, number>;
    totals?: {
      total?: number;
      passed?: number;
      failed?: number;
    };
    lastRunAt?: string;
  };
  recentBatches: ValidationBatchRecord[];
  slaHours?: number;
}

interface AuthUser {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  [key: string]: unknown;
}

interface InvoiceSummary {
  total: number;
  ready: number;
  validated: number;
  pending: number;
}

interface BatchSummary {
  total?: number;
  ready?: number;
  processing?: number;
  transmitting?: number;
  completed?: number;
  failed?: number;
}

interface PendingInvoicesResponse {
  invoices?: unknown;
  summary?: Record<string, unknown>;
  totals?: Record<string, unknown>;
  total?: number;
  ready?: number;
  pending_validation?: number;
  validated?: number;
  [key: string]: unknown;
}

interface TransmissionBatchesResponse {
  batches?: unknown;
  summary?: Record<string, unknown>;
  totals?: Record<string, unknown>;
  total?: number;
  ready?: number;
  processing?: number;
  completed?: number;
  failed?: number;
  transmitting?: number;
  [key: string]: unknown;
}

const normalizeStatusValue = (status?: string): string =>
  typeof status === 'string' ? status.trim().toLowerCase() : '';

const SELECTABLE_INVOICE_STATUSES = ['validated', 'valid', 'pending'];
const ACTIVE_BATCH_STATUSES = ['preparing', 'validating', 'transmitting', 'pending', 'submitted', 'acknowledged'];
const BATCH_STATUS_GROUPS: Record<string, string[]> = {
  ready: ['ready', 'queued', 'pending', 'preparing'],
  processing: ['processing', 'validating'],
  transmitting: ['transmitting', 'submitted', 'acknowledged'],
  completed: ['completed', 'success', 'accepted'],
  failed: ['failed', 'error', 'rejected', 'cancelled'],
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const isAuthUser = (value: unknown): value is AuthUser =>
  isRecord(value) &&
  typeof value.first_name === 'string' &&
  typeof value.last_name === 'string' &&
  typeof value.email === 'string' &&
  typeof value.role === 'string';

const getString = (value: unknown): string | undefined =>
  typeof value === 'string' ? value : undefined;

const toNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

const pickNumber = (...values: unknown[]): number | undefined => {
  for (const value of values) {
    const numeric = toNumber(value);
    if (numeric !== undefined) {
      return numeric;
    }
  }
  return undefined;
};

const recordValue = (
  record: Record<string, unknown> | undefined,
  key: string
): unknown => (record && key in record ? record[key] : undefined);

const normalizeInvoices = (rawInvoices: unknown): InvoiceData[] => {
  if (!Array.isArray(rawInvoices)) {
    return [];
  }

  return rawInvoices.map((invoice, index) => {
    if (!isRecord(invoice)) {
      return {
        id: `invoice-${index}`,
        invoice_number: `Invoice ${index + 1}`,
        status: 'pending',
      };
    }

    const invoiceId =
      getString(invoice.id) ??
      getString(invoice.transmission_id) ??
      getString(invoice.invoice_number) ??
      `invoice-${index}`;

    const invoiceNumber = getString(invoice.invoice_number) ?? invoiceId ?? `Invoice ${index + 1}`;
    const subtotal = toNumber(invoice.amount ?? invoice.subtotal);
    const total = toNumber(invoice.total_amount ?? invoice.amount ?? invoice.subtotal);
    const tax = toNumber(invoice.tax_amount ?? invoice.tax);
    const statusValue = getString(invoice.status) ?? 'pending';
    const dateValue =
      getString(invoice.date) ??
      getString(invoice.submitted_at) ??
      getString(invoice.created_at) ??
      getString(invoice.last_seen) ??
      getString(invoice.first_seen);

    return {
      id: String(invoiceId),
      invoice_number: String(invoiceNumber),
      customer_name:
        getString(invoice.customer_name) ??
        getString(invoice.customer) ??
        getString(invoice.client_name) ??
        getString(invoice.client) ??
        undefined,
      amount: subtotal,
      tax_amount: tax,
      total_amount: total,
      date: dateValue,
      status: statusValue,
      firs_reference:
        getString(invoice.firs_reference) ??
        getString(invoice.irn) ??
        getString(invoice.firs_submission_id) ??
        undefined,
      error_message:
        getString(invoice.error_message) ??
        getString(invoice.error) ??
        getString(invoice.error_summary) ??
        undefined,
      retry_count: typeof invoice.retry_count === 'number' ? invoice.retry_count : undefined,
    };
  });
};

const normalizeBatches = (rawBatches: unknown): TransmissionBatch[] => {
  if (Array.isArray(rawBatches)) {
    return rawBatches.map((batch, index) => {
      if (!isRecord(batch)) {
        return {
          id: `batch-${index}`,
          invoice_count: 0,
          status: 'pending',
        };
      }

      const invoiceCount = toNumber(batch.invoice_count ?? batch.count) ?? 0;
      return {
        id: String(getString(batch.id) ?? getString(batch.batch_id) ?? `batch-${index}`),
        created_at:
          getString(batch.created_at) ??
          getString(batch.first_seen) ??
          getString(batch.last_seen) ??
          undefined,
        invoice_count: invoiceCount,
        total_amount: toNumber(batch.total_amount),
        status: String(getString(batch.status) ?? getString(batch.status_label) ?? 'pending'),
        success_count: toNumber(batch.success_count),
        failed_count: toNumber(batch.failed_count ?? batch.error_count),
        firs_batch_id: getString(batch.firs_batch_id) ?? getString(batch.firs_reference) ?? undefined,
        error_summary: getString(batch.error_summary) ?? getString(batch.error) ?? undefined,
        first_seen: getString(batch.first_seen),
        last_seen: getString(batch.last_seen),
      };
    });
  }

  if (isRecord(rawBatches)) {
    return Object.entries(rawBatches).map(([statusKey, summary], index) => {
      if (!isRecord(summary)) {
        return {
          id: `status-${statusKey}-${index}`,
          invoice_count: 0,
          status: statusKey,
        };
      }

      const invoiceCount = toNumber(summary.invoice_count ?? summary.count) ?? 0;
      return {
        id: String(getString(summary.batch_id) ?? `status-${statusKey}-${index}`),
        created_at:
          getString(summary.last_seen) ??
          getString(summary.first_seen) ??
          undefined,
        invoice_count: invoiceCount,
        total_amount: toNumber(summary.total_amount),
        status: statusKey,
        success_count: toNumber(summary.success_count),
        failed_count: toNumber(summary.failed_count ?? summary.error_count),
        firs_batch_id: getString(summary.firs_batch_id) ?? undefined,
        error_summary: getString(summary.error_summary) ?? getString(summary.error) ?? undefined,
        first_seen: getString(summary.first_seen),
        last_seen: getString(summary.last_seen),
      };
    });
  }

  return [];
};

const extractInvoiceSource = (payload: unknown): unknown => {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (isRecord(payload)) {
    const invoices = payload['invoices'];
    if (Array.isArray(invoices)) {
      return invoices;
    }

    const pendingInvoices = payload['pending_invoices'];
    if (Array.isArray(pendingInvoices)) {
      return pendingInvoices;
    }
  }

  return payload;
};

const deriveInvoiceSummary = (
  payload: PendingInvoicesResponse | undefined,
  normalizedInvoices: InvoiceData[]
): InvoiceSummary => {
  const summaryRecord = isRecord(payload?.summary) ? (payload?.summary as Record<string, unknown>) : undefined;
  const totalsRecord = isRecord(payload?.totals) ? (payload?.totals as Record<string, unknown>) : undefined;

  const total = pickNumber(
    payload?.total,
    recordValue(summaryRecord, 'total'),
    recordValue(totalsRecord, 'total'),
    normalizedInvoices.length
  ) ?? normalizedInvoices.length;

  const readyFromPayload = pickNumber(
    payload?.ready,
    recordValue(summaryRecord, 'ready'),
    recordValue(totalsRecord, 'ready')
  );

  const validatedFromPayload = pickNumber(
    payload?.validated,
    recordValue(summaryRecord, 'validated'),
    recordValue(totalsRecord, 'validated')
  );

  const pendingFromPayload = pickNumber(
    payload?.pending_validation,
    recordValue(summaryRecord, 'pending_validation'),
    recordValue(summaryRecord, 'pending'),
    recordValue(totalsRecord, 'pending')
  );

  const readyComputed = normalizedInvoices.filter(inv =>
    SELECTABLE_INVOICE_STATUSES.some(status => normalizeStatusValue(inv.status) === status)
  ).length;

  const validatedComputed = normalizedInvoices.filter(inv => {
    const normalized = normalizeStatusValue(inv.status);
    return ['validated', 'valid', 'approved', 'accepted', 'submitted'].includes(normalized);
  }).length;

  const ready = readyFromPayload ?? readyComputed;
  const validated = validatedFromPayload ?? validatedComputed;
  const pending = pendingFromPayload ?? Math.max(total - validated, 0);

  return {
    total,
    ready,
    validated,
    pending,
  };
};

const deriveBatchSummary = (
  payload: TransmissionBatchesResponse | undefined,
  normalizedBatches: TransmissionBatch[]
): BatchSummary => {
  const summaryRecord = isRecord(payload?.summary) ? (payload?.summary as Record<string, unknown>) : undefined;
  const totalsRecord = isRecord(payload?.totals) ? (payload?.totals as Record<string, unknown>) : undefined;

  const total = pickNumber(
    payload?.total,
    recordValue(summaryRecord, 'total'),
    recordValue(totalsRecord, 'total'),
    normalizedBatches.length
  );

  const ready = pickNumber(
    payload?.ready,
    recordValue(summaryRecord, 'ready'),
    recordValue(totalsRecord, 'ready')
  );

  const processing = pickNumber(
    payload?.processing,
    recordValue(summaryRecord, 'processing'),
    recordValue(totalsRecord, 'processing')
  );

  const transmitting = pickNumber(
    payload?.transmitting,
    recordValue(summaryRecord, 'transmitting'),
    recordValue(totalsRecord, 'transmitting')
  );

  const completed = pickNumber(
    payload?.completed,
    recordValue(summaryRecord, 'completed'),
    recordValue(totalsRecord, 'completed')
  );

  const failed = pickNumber(
    payload?.failed,
    recordValue(summaryRecord, 'failed'),
    recordValue(totalsRecord, 'failed')
  );

  const statusCounts = normalizedBatches.reduce<Record<string, number>>((acc, batch) => {
    const status = normalizeStatusValue(batch.status);
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});

  const countForGroup = (group: string[]): number =>
    group.reduce((sum, status) => sum + (statusCounts[status] ?? 0), 0);

  return {
    total,
    ready: ready ?? countForGroup(BATCH_STATUS_GROUPS.ready),
    processing: processing ?? countForGroup(BATCH_STATUS_GROUPS.processing),
    transmitting: transmitting ?? countForGroup(BATCH_STATUS_GROUPS.transmitting),
    completed: completed ?? countForGroup(BATCH_STATUS_GROUPS.completed),
    failed: failed ?? countForGroup(BATCH_STATUS_GROUPS.failed),
  };
};

const extractBatchSource = (payload: unknown): unknown => {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (isRecord(payload)) {
    const batches = payload['batches'];
    if (Array.isArray(batches) || isRecord(batches)) {
      return batches;
    }
    return payload;
  }

  return payload;
};

export default function APPTransmissionPage() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'batches' | 'history'>('submit');
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);
  const [invoices, setInvoices] = useState<InvoiceData[]>([]);
  const [invoiceSummary, setInvoiceSummary] = useState<InvoiceSummary | null>(null);
  const [batches, setBatches] = useState<TransmissionBatch[]>([]);
  const [batchSummary, setBatchSummary] = useState<BatchSummary | null>(null);
  const [validationHistory, setValidationHistory] = useState<ValidationHistorySnapshot | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [transmissionStatus, setTransmissionStatus] = useState<'idle' | 'validating' | 'transmitting' | 'success' | 'error'>('idle');
  const [isDemo, setIsDemo] = useState(false);

  const normalizeStatus = normalizeStatusValue;
  const isInvoiceSelectable = (status?: string) =>
    SELECTABLE_INVOICE_STATUSES.some(item => normalizeStatus(status) === item);
  const isBatchActive = (status?: string) =>
    ACTIVE_BATCH_STATUSES.some(item => normalizeStatus(status) === item);

  useEffect(() => {
    const storedUser = authService.getStoredUser();
    if (!authService.isAuthenticated() || !isAuthUser(storedUser)) {
      router.push('/auth/signin');
      return;
    }

    if (storedUser.role !== 'access_point_provider') {
      router.push('/dashboard');
      return;
    }

    setUser(storedUser);
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [invoicesResult, batchesResult, validationResult] = await Promise.allSettled([
        apiClient.get<APIResponse<PendingInvoicesResponse>>('/app/invoices/pending'),
        apiClient.get<APIResponse<TransmissionBatchesResponse>>('/app/transmission/batches'),
        apiClient.get<APIResponse<ValidationHistorySnapshot>>('/app/validation/recent-batches?limit=8'),
      ]);

      if (invoicesResult.status !== 'fulfilled' || !invoicesResult.value?.success) {
        throw new Error('Failed to fetch pending invoices');
      }

      if (batchesResult.status !== 'fulfilled' || !batchesResult.value?.success) {
        throw new Error('Failed to fetch transmission batches');
      }

      const pendingPayload = invoicesResult.value.data as PendingInvoicesResponse | undefined;
      const invoicesSource = extractInvoiceSource(pendingPayload?.invoices ?? pendingPayload);
      const normalizedInvoices = normalizeInvoices(invoicesSource);
      setInvoices(normalizedInvoices);
      setInvoiceSummary(deriveInvoiceSummary(pendingPayload, normalizedInvoices));

      const batchesPayload = batchesResult.value.data as TransmissionBatchesResponse | undefined;
      const batchesSource = extractBatchSource(batchesPayload?.batches ?? batchesPayload);
      const normalizedBatches = normalizeBatches(batchesSource);
      setBatches(normalizedBatches);
      setBatchSummary(deriveBatchSummary(batchesPayload, normalizedBatches));

      if (
        validationResult.status === 'fulfilled' &&
        validationResult.value?.success &&
        validationResult.value.data
      ) {
        const data = validationResult.value.data as ValidationHistorySnapshot;
        setValidationHistory({
          summary: data.summary,
          recentBatches: Array.isArray(data.recentBatches) ? data.recentBatches : [],
          slaHours: typeof data.slaHours === 'number' ? data.slaHours : undefined,
        });
      } else {
        setValidationHistory(null);
      }

      setIsDemo(false);
    } catch (error) {
      console.error('Failed to load data, using demo data:', error);
      setIsDemo(true);

      const fallbackInvoices: InvoiceData[] = [
        {
          id: '1',
          invoice_number: 'INV-2024-001',
          customer_name: 'ABC Corporation Ltd',
          amount: 1000000,
          tax_amount: 75000,
          total_amount: 1075000,
          date: '2024-12-31',
          status: 'validated',
        },
        {
          id: '2',
          invoice_number: 'INV-2024-002',
          customer_name: 'XYZ Enterprises',
          amount: 750000,
          tax_amount: 56250,
          total_amount: 806250,
          date: '2024-12-31',
          status: 'validated',
        },
        {
          id: '3',
          invoice_number: 'INV-2024-003',
          customer_name: 'Tech Solutions Nigeria',
          amount: 2500000,
          tax_amount: 187500,
          total_amount: 2687500,
          date: '2024-12-30',
          status: 'draft',
        },
      ];

      setInvoices(fallbackInvoices);
      setInvoiceSummary(deriveInvoiceSummary(undefined, fallbackInvoices));

      const fallbackBatches: TransmissionBatch[] = [
        {
          id: 'BATCH-001',
          created_at: '2024-12-31T10:30:00Z',
          invoice_count: 25,
          total_amount: 45000000,
          status: 'completed',
          success_count: 25,
          failed_count: 0,
          firs_batch_id: 'FIRS-BATCH-20241231-001',
        },
        {
          id: 'BATCH-002',
          created_at: '2024-12-31T08:15:00Z',
          invoice_count: 18,
          total_amount: 32000000,
          status: 'transmitting',
          success_count: 0,
          failed_count: 0,
        },
      ];

      setBatches(fallbackBatches);
      setBatchSummary(deriveBatchSummary(undefined, fallbackBatches));

      setValidationHistory({
        summary: {
          totalBatches: 2,
          statusCounts: { completed: 1, transmitting: 1 },
          totals: { total: 43, passed: 25, failed: 0 },
          lastRunAt: new Date().toISOString(),
        },
        recentBatches: [
          {
            batchId: 'VAL-DEMO-001',
            status: 'completed',
            totals: { total: 25, passed: 25, failed: 0 },
            createdAt: '2024-12-31T10:30:00Z',
          },
          {
            batchId: 'VAL-DEMO-002',
            status: 'transmitting',
            totals: { total: 18, passed: 0, failed: 0 },
            createdAt: '2024-12-31T08:15:00Z',
          },
        ],
        slaHours: 4,
      });
    }
  };

  const handleInvoiceSelect = (invoiceId: string) => {
    const targetInvoice = invoices.find(inv => inv.id === invoiceId);
    if (targetInvoice && !isInvoiceSelectable(targetInvoice.status)) {
      return;
    }

    setSelectedInvoices(prev => 
      prev.includes(invoiceId) 
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const handleSelectAll = () => {
    const selectableInvoices = invoices
      .filter(inv => isInvoiceSelectable(inv.status))
      .map(inv => inv.id);

    setSelectedInvoices(
      selectedInvoices.length === selectableInvoices.length ? [] : selectableInvoices
    );
  };

  const submitToFIRS = async () => {
    if (selectedInvoices.length === 0) return;

    setIsLoading(true);
    setTransmissionStatus('validating');

    try {
      // First validate invoices
      const validationResponse = await apiClient.post<APIResponse<unknown>>('/app/firs/validate-batch', {
        invoice_ids: selectedInvoices
      });

      if (!validationResponse.success) {
        setTransmissionStatus('error');
        return;
      }

      setTransmissionStatus('transmitting');

      // Submit to FIRS
      const transmissionResponse = await apiClient.post<APIResponse<unknown>>('/app/firs/submit-batch', {
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

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredInvoices = invoices.filter(invoice => {
    const invoiceNumber = invoice.invoice_number?.toLowerCase() ?? '';
    const customerName = invoice.customer_name?.toLowerCase() ?? '';
    if (!normalizedQuery) {
      return true;
    }
    return invoiceNumber.includes(normalizedQuery) || customerName.includes(normalizedQuery);
  });

  const formatCurrency = (amount?: number) => {
    if (amount === undefined || amount === null || Number.isNaN(amount)) {
      return '--';
    }

    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN'
    }).format(amount);
  };

  const formatDate = (value?: string) => {
    if (!value) {
      return 'N/A';
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toLocaleString();
  };

  const getStatusColor = (status: string) => {
    const normalized = normalizeStatus(status);
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      pending: 'bg-yellow-100 text-yellow-800',
      valid: 'bg-green-100 text-green-800',
      validated: 'bg-green-100 text-green-800',
      submitted: 'bg-blue-100 text-blue-800',
      processing: 'bg-blue-100 text-blue-800',
      acknowledged: 'bg-blue-100 text-blue-800',
      approved: 'bg-emerald-100 text-emerald-800',
      accepted: 'bg-emerald-100 text-emerald-800',
      rejected: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-200 text-gray-600',
      timeout: 'bg-orange-100 text-orange-800',
      preparing: 'bg-yellow-100 text-yellow-800',
      validating: 'bg-blue-100 text-blue-800',
      transmitting: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800'
    };
    return colors[normalized] || 'bg-gray-100 text-gray-800';
  };

  const historySummary = validationHistory?.summary;
  const historyTotals = historySummary?.totals ?? { total: 0, passed: 0, failed: 0 };
  const historyPassRate = historyTotals.total
    ? Math.round(((historyTotals.passed ?? 0) / historyTotals.total) * 100)
    : 0;
  const historyFailRate = historyTotals.total
    ? Math.round(((historyTotals.failed ?? 0) / historyTotals.total) * 100)
    : 0;
  const statusEntries = Object.entries(historySummary?.statusCounts ?? {});
  const historySlaHours = validationHistory?.slaHours ?? 4;
  const validationPassRateDisplay = historyTotals.total ? `${historyPassRate}%` : 'N/A';

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
              {
                label: 'Ready to Submit',
                value:
                  invoiceSummary?.ready ??
                  invoices.filter(i => isInvoiceSelectable(i.status)).length,
                color: 'green',
              },
              { label: 'Selected', value: selectedInvoices.length, color: 'blue' },
              {
                label: 'Active Batches',
                value:
                  batchSummary
                    ? (batchSummary.processing ?? 0) +
                      (batchSummary.transmitting ?? 0) +
                      (batchSummary.ready ?? 0)
                    : batches.filter(b => isBatchActive(b.status)).length,
                color: 'purple',
              },
              {
                label: 'Validation Pass Rate',
                value: validationPassRateDisplay,
                color: 'emerald',
              },
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
                      {selectedInvoices.length === invoices.filter(i => isInvoiceSelectable(i.status)).length ? 'Deselect All' : 'Select All'}
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
                          disabled={!isInvoiceSelectable(invoice.status)}
                          className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500 disabled:opacity-50"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{invoice.invoice_number}</div>
                        <div className="text-sm text-gray-500">{formatDate(invoice.date)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {invoice.customer_name || 'N/A'}
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
                              {invoice.status || 'unknown'}
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
                              .reduce((sum, i) => sum + (i.total_amount ?? 0), 0)
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
                  {batches.map((batch) => {
                    const statusLabel = batch.status || 'unknown';
                    const normalizedBatchStatus = normalizeStatus(batch.status);

                    return (
                      <div key={batch.id} className="bg-gray-50 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <h3 className="text-lg font-medium text-gray-900">{batch.id}</h3>
                            <p className="text-sm text-gray-600">
                              Created: {formatDate(batch.created_at)}
                            </p>
                          </div>
                          <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(statusLabel)}`}>
                            {statusLabel}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <div className="text-sm text-gray-600">Invoices</div>
                            <div className="text-lg font-medium text-gray-900">{batch.invoice_count ?? 0}</div>
                          </div>
                          <div>
                            <div className="text-sm text-gray-600">Total Amount</div>
                            <div className="text-lg font-medium text-gray-900">{formatCurrency(batch.total_amount)}</div>
                          </div>
                          <div>
                            <div className="text-sm text-gray-600">Successful</div>
                            <div className="text-lg font-medium text-green-600">{batch.success_count ?? 0}</div>
                          </div>
                          <div>
                            <div className="text-sm text-gray-600">Failed</div>
                            <div className="text-lg font-medium text-red-600">{batch.failed_count ?? 0}</div>
                          </div>
                        </div>

                        {batch.firs_batch_id && (
                          <div className="bg-white border border-gray-200 rounded p-3">
                            <div className="text-sm text-gray-600">FIRS Batch ID</div>
                            <div className="text-sm font-mono text-gray-900">{batch.firs_batch_id}</div>
                          </div>
                        )}

                        {batch.error_summary && (
                          <div className="mt-4 bg-red-50 border border-red-200 rounded p-3">
                            <div className="text-sm text-red-700">{batch.error_summary}</div>
                          </div>
                        )}

                        {normalizedBatchStatus === 'transmitting' && (
                          <div className="mt-4">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                            </div>
                            <p className="text-sm text-blue-600 mt-2">Transmitting to FIRS...</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Validation & Transmission History</h2>

                {validationHistory ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-xs uppercase text-gray-500">Total Batches</div>
                        <div className="text-2xl font-bold text-gray-900">
                          {validationHistory.summary?.totalBatches ?? 0}
                        </div>
                        <div className="text-xs text-gray-500">All time</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-xs uppercase text-gray-500">Pass Rate</div>
                        <div className="text-2xl font-bold text-emerald-600">
                          {historyTotals.total ? `${historyPassRate}%` : 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500">Failed {historyFailRate}%</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-xs uppercase text-gray-500">Last Run</div>
                        <div className="text-sm font-medium text-gray-800">
                          {historySummary?.lastRunAt ? formatDate(historySummary.lastRunAt) : 'No runs yet'}
                        </div>
                        <div className="text-xs text-gray-500">SLA {historySlaHours}h</div>
                      </div>
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-xs uppercase text-gray-500">Status Mix</div>
                        <div className="mt-2 space-y-1 text-sm text-gray-700">
                          {statusEntries.length > 0 ? (
                            statusEntries.map(([status, value]) => (
                              <div key={status} className="flex items-center justify-between">
                                <span className="capitalize">{status}</span>
                                <span>{value}</span>
                              </div>
                            ))
                          ) : (
                            <span className="text-gray-500">No history yet</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-gray-900">Recent Validation Batches</h3>
                        <div className="text-sm text-gray-500">
                          SLA threshold: {historySlaHours} hours
                        </div>
                      </div>

                      {validationHistory.recentBatches.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Batch</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Totals</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {validationHistory.recentBatches.map((batch, index) => {
                                const totals = batch.totals ?? {};
                                return (
                                  <tr key={`${batch.batchId ?? 'batch'}-${index}`}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                      {batch.batchId ?? 'Unknown'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                      {batch.createdAt ? formatDate(batch.createdAt) : 'N/A'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {totals.total ?? 0} total · {totals.passed ?? 0} passed · {totals.failed ?? 0} failed
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(batch.status ?? 'unknown')}`}>
                                        {batch.status ?? 'unknown'}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600">
                                      {batch.errorSummary ?? '—'}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="text-center text-gray-500 py-12">No validation runs recorded yet.</div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="bg-gray-50 rounded-lg p-8 text-center">
                    <div className="text-4xl mb-4">📊</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Transmission Analytics</h3>
                    <p className="text-gray-600 mb-4">
                      Detailed transmission history will appear once validation batches have been processed.
                    </p>
                    <TaxPoyntButton
                      variant="outline"
                      onClick={() => router.push('/dashboard/app/reports')}
                    >
                      View Reports
                    </TaxPoyntButton>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
