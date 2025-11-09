import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  SIDashboardHero,
  type HeroStatusChipConfig,
  type ManualPullConfig,
} from '../components/SIDashboardHero';

const status = (overrides?: Partial<HeroStatusChipConfig>): HeroStatusChipConfig => ({
  label: 'Bank feeds',
  helper: 'Not connected',
  tone: 'muted',
  ...overrides,
});

const manualPull = (overrides?: Partial<ManualPullConfig>): ManualPullConfig => ({
  modeLabel: 'Manual',
  status: 'idle',
  helper: 'Ready to run a pull',
  onRun: jest.fn(),
  ...overrides,
});

describe('SIDashboardHero', () => {
  it('renders status chips and CTA copy', () => {
    render(
      <SIDashboardHero
        userName="Ada"
        bankingStatus={status({ helper: 'Connected via Mono', tone: 'success' })}
        erpStatus={status({ label: 'ERP adapters', helper: 'Demo workspace', tone: 'demo' })}
        bankingManualPull={manualPull()}
        erpManualPull={manualPull()}
        onPrimaryAction={() => {}}
        onSecondaryAction={() => {}}
        onDismiss={() => {}}
      />,
    );

    expect(screen.getByText(/Welcome back, Ada/i)).toBeInTheDocument();
    expect(screen.getByTestId('banking-status-chip')).toHaveTextContent('Connected via Mono');
    expect(screen.getByTestId('erp-status-chip')).toHaveTextContent('Demo workspace');
    expect(screen.getByTestId('hero-primary-cta')).toHaveTextContent('Upload first invoices');
    expect(screen.getByTestId('hero-secondary-cta')).toHaveTextContent('Invite a teammate');
    expect(screen.getAllByText(/Next pull/i).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Run now/i }).length).toBeGreaterThan(0);
  });

  it('invokes callbacks when CTAs or manual pull buttons are clicked', () => {
    const primary = jest.fn();
    const secondary = jest.fn();
    const dismiss = jest.fn();
    const manual = manualPull();

    render(
      <SIDashboardHero
        userName="QA"
        bankingStatus={status()}
        erpStatus={status()}
        erpManualPull={manual}
        onPrimaryAction={primary}
        onSecondaryAction={secondary}
        onDismiss={dismiss}
      />,
    );

    fireEvent.click(screen.getByTestId('hero-primary-cta'));
    fireEvent.click(screen.getByTestId('hero-secondary-cta'));
    fireEvent.click(screen.getByTestId('hero-dismiss'));
    fireEvent.click(screen.getByTestId('erp-status-chip-manual-run'));

    expect(primary).toHaveBeenCalledTimes(1);
    expect(secondary).toHaveBeenCalledTimes(1);
    expect(dismiss).toHaveBeenCalledTimes(1);
    expect(manual.onRun).toHaveBeenCalledTimes(1);
  });
});
