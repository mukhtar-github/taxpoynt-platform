export type BankingConnectionStatus =
  | 'not_started'
  | 'link_created'
  | 'awaiting_consent'
  | 'connected'
  | 'error'
  | 'skipped'
  | 'demo';

export interface BankingConnectionState {
  status: BankingConnectionStatus;
  bankName?: string;
  lastMessage?: string;
  lastUpdated?: string;
}

export type ERPConnectionStatus = 'not_connected' | 'connecting' | 'connected' | 'error' | 'demo';

export interface ERPConnectionState {
  status: ERPConnectionStatus;
  connectionName?: string;
  lastMessage?: string;
  lastTestAt?: string;
  sampleInvoice?: Record<string, unknown> | null;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const toOptionalString = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed ? trimmed : undefined;
  }
  return undefined;
};

const toStringValue = (value: unknown): string => (typeof value === 'string' ? value : '');

export const sanitizeBankingConnection = (value: unknown): BankingConnectionState => {
  if (!isRecord(value)) {
    return { status: 'not_started' };
  }
  const normalizedStatus = toStringValue(value.status) as BankingConnectionStatus;
  const status: BankingConnectionStatus =
    ['not_started', 'link_created', 'awaiting_consent', 'connected', 'error', 'skipped', 'demo'].includes(
      normalizedStatus,
    )
      ? normalizedStatus
      : 'not_started';

  return {
    status,
    bankName: toOptionalString(value.bankName ?? value.bank_name),
    lastMessage: toOptionalString(value.lastMessage ?? value.last_message),
    lastUpdated: toOptionalString(value.lastUpdated ?? value.last_updated),
  };
};

export const sanitizeErpConnection = (value: unknown): ERPConnectionState => {
  if (!isRecord(value)) {
    return { status: 'not_connected', sampleInvoice: null };
  }
  const normalizedStatus = toStringValue(value.status) as ERPConnectionStatus;
  const status: ERPConnectionStatus =
    ['not_connected', 'connecting', 'connected', 'error', 'demo'].includes(normalizedStatus)
      ? normalizedStatus
      : 'not_connected';

  const sampleInvoiceCandidate = value.sampleInvoice ?? value.sample_invoice;
  const sampleInvoice = isRecord(sampleInvoiceCandidate)
    ? (sampleInvoiceCandidate as Record<string, unknown>)
    : null;

  return {
    status,
    connectionName: toOptionalString(value.connectionName ?? value.connection_name),
    lastMessage: toOptionalString(value.lastMessage ?? value.last_message),
    lastTestAt: toOptionalString(value.lastTestAt ?? value.last_test_at),
    sampleInvoice,
  };
};
