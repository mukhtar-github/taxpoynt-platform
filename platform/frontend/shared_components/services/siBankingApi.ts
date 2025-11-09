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

  async syncTransactions(): Promise<V1Response<BankingSyncResponse>> {
    return apiClient.post<V1Response<BankingSyncResponse>>(
      '/si/banking/transactions/sync',
      {},
    );
  },
};

export default siBankingApi;
