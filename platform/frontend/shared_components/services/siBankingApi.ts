import apiClient from '../api/client';

interface MonoLinkPayload {
  customer: {
    name: string;
    email: string;
  };
  scope: string;
  redirect_url: string;
  callback_url?: string;
  meta?: Record<string, unknown>;
}

interface MonoLinkResponse {
  data?: {
    mono_url?: string;
  };
  mono_url?: string;
}

interface V1Response<T> {
  success: boolean;
  action: string;
  data: T;
  meta?: Record<string, unknown>;
}

interface BankingSyncResponse {
  fetched_count?: number;
  last_synced_at?: string;
  connection_id?: string;
  account_id?: string;
  message?: string;
}

export interface BankingAccount {
  id: string;
  connection_id: string;
  provider_account_id?: string;
  account_number?: string;
  account_name?: string;
  account_type?: string;
  bank_name?: string;
  bank_code?: string;
  currency?: string;
  is_active?: boolean;
  balance?: number | null;
  available_balance?: number | null;
  last_balance_update?: string;
  account_metadata?: Record<string, unknown>;
  provider?: string | null;
  connection_status?: string | null;
  last_sync_at?: string | null;
  si_id?: string | null;
}

interface BankingAccountsResponse {
  items: BankingAccount[];
  count: number;
  limit: number;
  offset: number;
}

const siBankingApi = {
  async createMonoLink(payload: MonoLinkPayload): Promise<string> {
    const response = await apiClient.post<MonoLinkResponse>(
      '/si/banking/open-banking/mono/link',
      payload,
    );
    const monoUrl = response?.data?.mono_url ?? response?.mono_url;
    if (!monoUrl) {
      throw new Error('Mono link missing in response payload');
    }
    return monoUrl;
  },

  async listAccounts(params?: { provider?: string }): Promise<V1Response<BankingAccountsResponse>> {
    const search = new URLSearchParams();
    if (params?.provider) {
      search.set('provider', params.provider);
    }
    const query = search.toString();
    const path = `/si/banking/accounts${query ? `?${query}` : ''}`;
    return apiClient.get<V1Response<BankingAccountsResponse>>(path);
  },

  async syncTransactions(options?: {
    accountDbId?: string;
    monoAccountId?: string;
    connectionId?: string;
  }): Promise<V1Response<BankingSyncResponse>> {
    const payload = {
      account_db_id: options?.accountDbId,
      account_id: options?.accountDbId,
      mono_account_id: options?.monoAccountId,
      connection_id: options?.connectionId,
    };
    return apiClient.post<V1Response<BankingSyncResponse>>(
      '/si/banking/transactions/sync',
      payload,
    );
  },
};

export default siBankingApi;
