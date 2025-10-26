import React from 'react';
import { describe, it, expect, beforeEach, beforeAll, jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { EnhancedSIInterface } from '../EnhancedSIInterface';
import { onboardingChecklistApi } from '../../shared_components/services/onboardingChecklistApi';
import apiClient from '../../shared_components/api/client';

const pushMock = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

jest.mock('../../shared_components/layouts/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-layout">{children}</div>,
}));

jest.mock('../../design_system/components/OptimizedImage', () => ({
  OptimizedImage: (props: any) => <img alt={props.alt ?? 'Optimized'} {...props} />,
}));

jest.mock('../../shared_components/api/client', () => ({
  __esModule: true,
  default: {
    get: jest.fn().mockResolvedValue({ success: true, data: {} }),
  },
}));

jest.mock('../../shared_components/services/onboardingChecklistApi', () => ({
  onboardingChecklistApi: {
    fetchChecklist: jest.fn(),
  },
}));

const apiGetMock = apiClient.get as jest.Mock;

beforeAll(() => {
  Object.defineProperty(window, 'IntersectionObserver', {
    writable: true,
    configurable: true,
    value: class {
      observe() {}
      disconnect() {}
      unobserve() {}
      takeRecords() { return []; }
    },
  });

  Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
    writable: true,
    value: () => null,
  });

  Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
    writable: true,
    value: () => '',
  });
});

const mockChecklist = {
  user_id: 'user-123',
  service_package: 'si',
  current_phase: 'service-foundation',
  phases: [
    {
      id: 'service-foundation',
      title: 'Company & Compliance Setup',
      description: 'Confirm service focus and capture company details.',
      status: 'in_progress',
      steps: [
        {
          id: 'service-selection',
          canonical_id: 'service-selection',
          title: 'Service selection',
          description: 'Confirm your service package.',
          status: 'complete',
          completed: true,
        },
        {
          id: 'company-profile',
          canonical_id: 'company-profile',
          title: 'Company profile',
          description: 'Provide company information.',
          status: 'in_progress',
          completed: false,
          success_criteria: 'Company name and contact captured',
        },
      ],
    },
    {
      id: 'integration-readiness',
      title: 'System Integration Setup',
      description: 'Prepare ERP connectivity.',
      status: 'pending',
      steps: [],
    },
  ],
  summary: {
    completed_phases: [],
    remaining_phases: ['service-foundation', 'integration-readiness'],
    completion_percentage: 25,
  },
  updated_at: new Date().toISOString(),
};

const mockChecklistComplete = {
  ...mockChecklist,
  phases: mockChecklist.phases.map((phase) => ({
    ...phase,
    status: 'complete',
    steps: phase.steps.map((step) => ({
      ...step,
      status: 'complete',
      completed: true,
    })),
  })),
  summary: {
    ...mockChecklist.summary,
    completed_phases: mockChecklist.phases.map((phase) => phase.id),
    remaining_phases: [],
    completion_percentage: 100,
  },
};

describe('EnhancedSIInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    pushMock.mockReset();
    apiGetMock.mockReset();
    apiGetMock.mockResolvedValue({ success: true, data: {} });
  });

  it('renders onboarding checklist data when loaded', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklist);

    render(<EnhancedSIInterface />);

    expect(await screen.findByText('Company & Compliance Setup')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Resume onboarding wizard/i })).toBeInTheDocument();
  });

  it('navigates to onboarding wizard when resume is clicked', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklist);

    render(<EnhancedSIInterface />);

    const resumeButton = await screen.findByRole('button', { name: /Resume onboarding wizard/i });
    fireEvent.click(resumeButton);

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/onboarding/si/integration-setup');
    });
  });

  it('shows phase guidance when requested', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklist);

    render(<EnhancedSIInterface />);

    const guidanceButtons = await screen.findAllByRole('button', { name: /Guidance/i });
    fireEvent.click(guidanceButtons[0]);

    expect(await screen.findByTestId('checklist-guidance-panel')).toBeInTheDocument();
  });

  it('shows post-onboarding focus actions when checklist is complete', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklistComplete);

    render(<EnhancedSIInterface />);

    const panel = await screen.findByTestId('checklist-guidance-panel');
    expect(panel).toHaveTextContent('Post-onboarding focus');
    expect(screen.getByText('Keep automations running smoothly')).toBeInTheDocument();
  });

  it('renders connect banking tile when cash flow data is absent', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklistComplete);
    apiGetMock.mockResolvedValue({ success: true, data: {} });

    render(<EnhancedSIInterface />);

    expect(await screen.findByText(/Connect banking to unlock insights/i)).toBeInTheDocument();
  });

  it('renders financial snapshot card when cash flow data is available', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklistComplete);
    apiGetMock.mockResolvedValue({
      success: true,
      data: {
        cashFlow: {
          netFlow: 4_500_000,
          categories: {
            Invoices: 3_000_000,
            Subscriptions: 1_500_000,
          },
        },
        financial: {
          banking: { connected: 1, totalAccounts: 2, providers: [] },
          payments: { connected: 1, monthlyVolume: 12_000_000, providers: [] },
        },
      },
    });

    render(<EnhancedSIInterface />);

    expect(await screen.findByText(/Top cash sources/i)).toBeInTheDocument();
    expect(screen.queryByText(/Connect banking to unlock insights/i)).not.toBeInTheDocument();
  });

  it('prioritises IRN activity and exposes validation log navigation', async () => {
    (onboardingChecklistApi.fetchChecklist as jest.Mock).mockResolvedValue(mockChecklistComplete);
    apiGetMock.mockResolvedValue({
      success: true,
      data: {
        irnStatus: {
          recent: [
            {
              irn: 'SUB-0001',
              status: 'submitted',
              createdAt: new Date().toISOString(),
            },
          ],
        },
        validationLogs: [
          {
            status: 'failed',
            createdAt: new Date().toISOString(),
            totals: { total: 10 },
          },
        ],
      },
    });

    render(<EnhancedSIInterface />);

    expect(await screen.findByText(/IRN SUB-0001/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /View validation logs/i })).toBeInTheDocument();
  });
});
