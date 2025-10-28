import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import VerifyEmailPage from '../verify-email/page';

const mockPush = jest.fn();

const searchParamsMap = new Map<string, string | undefined>([
  ['email', 'user@example.com'],
  ['service', 'si'],
  ['onboarding_token', 'token-123'],
  ['next', '/onboarding/si/integration-choice'],
]);

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({
    get: (key: string) => searchParamsMap.get(key) ?? null,
  }),
}));

const verifyEmailMock = jest.fn();

jest.mock('../../../shared_components/services/auth', () => ({
  authService: {
    verifyEmail: (...args: unknown[]) => verifyEmailMock(...args),
  },
}));

const updateStepMock = jest.fn();

jest.mock('../../../shared_components/services/onboardingApi', () => ({
  OnboardingStateManager: {
    updateStep: (...args: unknown[]) => updateStepMock(...args),
  },
}));

if (typeof window.matchMedia !== 'function') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).matchMedia = jest.fn().mockImplementation(() => ({
    matches: false,
    media: '',
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    jest.useFakeTimers().setSystemTime(new Date('2024-01-01T12:00:00Z'));
    mockPush.mockReset();
    verifyEmailMock.mockReset().mockResolvedValue({
      access_token: 'access-token',
      token_type: 'bearer',
      user: {
        id: 'user-1',
        email: 'user@example.com',
        first_name: 'Ada',
        last_name: 'Okeke',
        role: 'system_integrator',
        service_package: 'si',
      },
    });
    updateStepMock.mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('verifies email, persists onboarding step, and redirects to integration choice', async () => {
    render(<VerifyEmailPage />);

    fireEvent.change(screen.getByPlaceholderText(/Enter the 6-digit code/i), {
      target: { value: '123456' },
    });

    fireEvent.click(screen.getByRole('checkbox', { name: /Terms of Service/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /Privacy Policy/i }));

    fireEvent.click(screen.getByRole('button', { name: /Verify email/i }));

    await waitFor(() => {
      expect(verifyEmailMock).toHaveBeenCalledWith({
        email: 'user@example.com',
        code: '123456',
        service_package: 'si',
        onboarding_token: 'token-123',
        terms_accepted: true,
        privacy_accepted: true,
        metadata: expect.objectContaining({
          consent_accepted_at: expect.any(String),
        }),
      });
    });

    await waitFor(() => {
      expect(updateStepMock).toHaveBeenNthCalledWith(1, 'user-1', 'email_verification', true);
      expect(updateStepMock).toHaveBeenNthCalledWith(2, 'user-1', 'terms_acceptance', true);
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/onboarding/si/integration-choice');
    });

    expect(await screen.findByText(/Saved at/i)).toBeInTheDocument();
  });
});
