import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SIDashboardSummary } from '../components/SIDashboardSummary';
import { HeroStatusChipConfig, ManualPullConfig } from '../components/SIDashboardHero';

const chip = (helper: string, tone: HeroStatusChipConfig['tone']): HeroStatusChipConfig => ({
  label: 'Status',
  helper,
  tone,
});

const manualPull = (overrides?: Partial<ManualPullConfig>): ManualPullConfig => ({
  modeLabel: 'Manual',
  status: 'idle',
  helper: 'Ready to run a pull',
  onRun: jest.fn(),
  ...overrides,
});

describe('SIDashboardSummary', () => {
  it('renders status chips and checklist data', () => {
    render(
      <SIDashboardSummary
        userName="Ada"
        bankingStatus={chip('Connected', 'success')}
        erpStatus={chip('Demo', 'demo')}
        bankingManualPull={manualPull()}
        erpManualPull={manualPull()}
        checklist={{ remainingPhases: 1, nextPhaseTitle: 'Invite team', lastUpdated: 'today' }}
        onResumeOnboarding={() => {}}
        onPrimaryAction={() => {}}
        onSecondaryAction={() => {}}
        onOpenAdvanced={() => {}}
      />,
    );

    expect(screen.getByText(/Welcome back, Ada/i)).toBeInTheDocument();
    expect(screen.getByTestId('summary-banking-chip')).toHaveTextContent('Connected');
    expect(screen.getByTestId('summary-erp-chip')).toHaveTextContent('Demo');
    expect(screen.getByText(/1 phase remaining/i)).toBeInTheDocument();
    expect(screen.getByText(/Next: Invite team/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Next pull/i).length).toBeGreaterThan(0);
  });

  it('invokes handlers', () => {
    const resume = jest.fn();
    const primary = jest.fn();
    const secondary = jest.fn();
    const advanced = jest.fn();
    const manual = manualPull();

    render(
      <SIDashboardSummary
        userName="QA"
        bankingStatus={chip('Pending', 'warning')}
        erpStatus={chip('Not connected', 'muted')}
        erpManualPull={manual}
        checklist={{ remainingPhases: 0 }}
        onResumeOnboarding={resume}
        onPrimaryAction={primary}
        onSecondaryAction={secondary}
        onOpenAdvanced={advanced}
      />,
    );

    fireEvent.click(screen.getByTestId('summary-resume-btn'));
    fireEvent.click(screen.getByTestId('summary-primary'));
    fireEvent.click(screen.getByTestId('summary-secondary'));
    fireEvent.click(screen.getByTestId('summary-open-advanced'));
    fireEvent.click(screen.getByTestId('summary-erp-chip-manual-run'));

    expect(resume).toHaveBeenCalledTimes(1);
    expect(primary).toHaveBeenCalledTimes(1);
    expect(secondary).toHaveBeenCalledTimes(1);
    expect(advanced).toHaveBeenCalledTimes(1);
    expect(manual.onRun).toHaveBeenCalledTimes(1);
  });
});
