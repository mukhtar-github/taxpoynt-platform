import siBankingApi from '../siBankingApi';
import apiClient from '../../api/client';

jest.mock('../../api/client', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

const mockedClient = apiClient as unknown as {
  post: jest.Mock;
  get: jest.Mock;
};

describe('siBankingApi', () => {
  beforeEach(() => {
    mockedClient.post.mockReset();
    mockedClient.get.mockReset();
  });

  it('requests Mono accounts with provider filter', async () => {
    mockedClient.get.mockResolvedValue({ success: true, action: 'list', data: { items: [] } });

    await siBankingApi.listAccounts({ provider: 'mono' });

    expect(mockedClient.get).toHaveBeenCalledWith('/si/banking/accounts?provider=mono');
  });

  it('sends sync payload with account identifiers', async () => {
    mockedClient.post.mockResolvedValue({ success: true, action: 'sync', data: {} });

    await siBankingApi.syncTransactions({
      accountDbId: 'acc-123',
      monoAccountId: 'mono-abc',
      connectionId: 'conn-456',
    });

    expect(mockedClient.post).toHaveBeenCalledWith(
      '/si/banking/transactions/sync',
      {
        account_db_id: 'acc-123',
        account_id: 'acc-123',
        mono_account_id: 'mono-abc',
        connection_id: 'conn-456',
      },
    );
  });
});
