import React from 'react';
import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ERPOnboarding from '../erp_onboarding';
import { onboardingApi } from '../../../shared_components/services/onboardingApi';
import { onboardingStateQueue } from '../../../shared_components/services/onboardingStateQueue';
import type { OnboardingState } from '../../../shared_components/services/onboardingApi';

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

jest.mock('../../../shared_components/services/onboardingApi', () => {
  const originalModule = jest.requireActual('../../../shared_components/services/onboardingApi');
  return {
    __esModule: true,
    ...originalModule,
    onboardingApi: {
      getOnboardingState: jest.fn().mockResolvedValue(null),
      saveServiceSelection: jest.fn().mockResolvedValue(null),
      saveCompanyProfile: jest.fn().mockResolvedValue(null),
      updateOnboardingState: jest.fn().mockResolvedValue({
        user_id: 'user-123',
        current_step: 'company-profile',
        completed_steps: ['service-selection'],
        has_started: true,
        is_complete: false,
        last_active_date: new Date().toISOString(),
        metadata: {
          wizard: {},
          expected_steps: ['service-selection', 'company-profile', 'system-connectivity'],
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    },
  };
});

jest.mock('../../../shared_components/services/auth', () => ({
  authService: {
    isAuthenticated: () => true,
    getStoredUser: () => ({
      id: 'user-123',
      platform_role: 'system_integrator',
      organization: { id: 'org-789' },
    }),
    getToken: () => 'token',
    logout: jest.fn(),
  },
}));

jest.mock('../../../shared_components/utils/onboardingSessionPersistence', () => ({
  __esModule: true,
  default: {
    initializeSession: jest.fn(),
    hasValidSession: jest.fn(() => true),
    updateSession: jest.fn(),
    completeSession: jest.fn(),
  },
}));

jest.mock('../../../shared_components/services/onboardingStateQueue', () => {
  const enqueue = jest.fn().mockResolvedValue(undefined);
  const clear = jest.fn();
  const configureOnboardingStateDispatcher = jest.fn();
  return {
    onboardingStateQueue: { enqueue, clear },
    configureOnboardingStateDispatcher,
  };
});

const mockUpdateState = onboardingApi.updateOnboardingState as jest.MockedFunction<
  typeof onboardingApi.updateOnboardingState
>;
const mockGetState = onboardingApi.getOnboardingState as jest.MockedFunction<
  typeof onboardingApi.getOnboardingState
>;
const mockSaveServiceSelection = onboardingApi.saveServiceSelection as jest.MockedFunction<
  typeof onboardingApi.saveServiceSelection
>;
const mockSaveCompanyProfile = onboardingApi.saveCompanyProfile as jest.MockedFunction<
  typeof onboardingApi.saveCompanyProfile
>;
const mockQueueEnqueue = onboardingStateQueue.enqueue as jest.MockedFunction<
  typeof onboardingStateQueue.enqueue
>;

beforeEach(() => {
  jest.clearAllMocks();
  mockGetState.mockResolvedValue(null);
  mockQueueEnqueue.mockResolvedValue(undefined);
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

const buildState = (overrides: Partial<OnboardingState>): OnboardingState => ({
  user_id: 'user-123',
  current_step: 'service-selection',
  completed_steps: [],
  has_started: true,
  is_complete: false,
  last_active_date: new Date().toISOString(),
  metadata: {
    wizard: {},
    expected_steps: ['service-selection', 'company-profile', 'system-connectivity'],
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

test('renders service focus step by default', async () => {
  render(<ERPOnboarding />);
  expect(await screen.findByRole('heading', { name: 'Service Focus' })).toBeInTheDocument();
  expect(screen.getByText(/Step 1 of 3/i)).toBeInTheDocument();
});

test('advances to company profile after saving service focus', async () => {
  mockGetState
    .mockResolvedValueOnce(null) // initial load
    .mockResolvedValueOnce(
      buildState({
        current_step: 'company-profile',
        completed_steps: ['service-selection'],
      }),
    );

  render(<ERPOnboarding />);

  const continueButton = await screen.findByRole('button', { name: /save & continue/i });
  fireEvent.click(continueButton);

  await waitFor(() => {
    expect(screen.getByText('Company Profile')).toBeInTheDocument();
  });
  expect(mockQueueEnqueue).toHaveBeenCalled();
  expect(mockGetState).toHaveBeenCalled();
});

test('autosaves company profile changes', async () => {
  mockSaveCompanyProfile.mockResolvedValue(
    buildState({
      metadata: {
        wizard: {
          company_profile: { company_name: 'Example Ltd' },
        },
        expected_steps: ['service-selection', 'company-profile', 'system-connectivity'],
      },
    }),
  );

  render(<ERPOnboarding initialStepId="company-profile" />);

  const input = await screen.findByPlaceholderText('e.g. Example Integrations Ltd');
  fireEvent.change(input, { target: { value: 'Example Ltd' } });
  fireEvent.change(input, { target: { value: 'Example Integrations Ltd' } });

  await act(async () => {
    jest.advanceTimersByTime(1500);
  });

  expect(mockSaveCompanyProfile).toHaveBeenCalled();
});

test('complete later triggers skip callback', async () => {
  const onSkip = jest.fn();
  render(<ERPOnboarding onSkip={onSkip} />);

  const skipButton = await screen.findByText(/Complete later/i);
  fireEvent.click(skipButton);

  expect(onSkip).toHaveBeenCalled();
});
