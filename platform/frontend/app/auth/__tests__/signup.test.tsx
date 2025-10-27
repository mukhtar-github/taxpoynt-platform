import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import SignUpPageWrapper from '../signup/page';

const mockPush = jest.fn();

const mockSearchParams = new URLSearchParams('service=si');

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key),
    toString: () => mockSearchParams.toString(),
  }),
}));

const registerMock = jest.fn();

jest.mock('../../../shared_components/services/auth', () => ({
  authService: {
    register: (...args: unknown[]) => registerMock(...args),
  },
}));

jest.mock('../../../business_interface/auth/StreamlinedRegistration', () => ({
  StreamlinedRegistration: ({ onCompleteRegistration }: any) => (
    <button
      type="button"
      onClick={() =>
        onCompleteRegistration({
          first_name: 'Ada ',
          last_name: 'Okeke',
          email: 'user@example.com ',
          password: 'Password123',
          business_name: 'Ada Ventures',
          companyType: 'system_integrator',
          companySize: '1-10',
          service_package: 'si',
          terms_accepted: true,
          privacy_accepted: true,
          trial_started: false,
          trial_start_date: '2024-01-01T00:00:00.000Z',
        })
      }
    >
      Complete Registration
    </button>
  ),
}));

describe('SignUpPage SI flow', () => {
  beforeEach(() => {
    mockPush.mockReset();
    registerMock.mockReset().mockResolvedValue({ user: { service_package: 'si' } });
  });

  it('registers and redirects SI users to the integration-choice step', async () => {
    render(<SignUpPageWrapper />);

    fireEvent.click(screen.getByRole('button', { name: /complete registration/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'Password123',
        first_name: 'Ada',
        last_name: 'Okeke',
        phone: undefined,
        service_package: 'si',
        business_name: 'Ada Ventures',
        business_type: 'system_integrator',
        terms_accepted: true,
        privacy_accepted: true,
        marketing_consent: false,
        consents: {
          company_size: '1-10',
          company_type: 'system_integrator',
          trial_started: false,
          trial_start_date: '2024-01-01T00:00:00.000Z',
        },
      });
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/onboarding/si/integration-choice');
    });
  });
});
