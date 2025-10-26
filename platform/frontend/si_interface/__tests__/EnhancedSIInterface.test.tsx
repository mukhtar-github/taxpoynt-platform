import React from 'react';
import { describe, it, expect, beforeEach, beforeAll, jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { EnhancedSIInterface } from '../EnhancedSIInterface';
import { onboardingChecklistApi } from '../../shared_components/services/onboardingChecklistApi';

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

describe('EnhancedSIInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    pushMock.mockReset();
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

    expect(await screen.findByTestId('checklist-guidance-panel')).toBeInTheDocument();
  });
});
