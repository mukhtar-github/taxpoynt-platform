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
};

export default siBankingApi;
