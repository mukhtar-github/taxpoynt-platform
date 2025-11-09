import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SIDashboardHero, type HeroStatusChipConfig } from '../components/SIDashboardHero';

const status = (overrides?: Partial<HeroStatusChipConfig>): HeroStatusChipConfig => ({
  label: 'Bank feeds',
  helper: 'Not connected',
  tone: 'muted',
  ...overrides,
});

describe('SIDashboardHero', () => {
  it('renders status chips and CTA copy', () => {
    render(
      <SIDashboardHero
        userName="Ada"
        bankingStatus={status({ helper: 'Connected via Mono', tone: 'success' })}
        erpStatus={status({ label: 'ERP adapters', helper: 'Demo workspace', tone: 'demo' })}
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
  });

  it('invokes callbacks when CTAs are clicked', () => {
    const primary = jest.fn();
    const secondary = jest.fn();
    const dismiss = jest.fn();

    render(
      <SIDashboardHero
        userName="QA"
        bankingStatus={status()}
        erpStatus={status()}
        onPrimaryAction={primary}
        onSecondaryAction={secondary}
        onDismiss={dismiss}
      />,
    );

    fireEvent.click(screen.getByTestId('hero-primary-cta'));
    fireEvent.click(screen.getByTestId('hero-secondary-cta'));
    fireEvent.click(screen.getByTestId('hero-dismiss'));

    expect(primary).toHaveBeenCalledTimes(1);
    expect(secondary).toHaveBeenCalledTimes(1);
    expect(dismiss).toHaveBeenCalledTimes(1);
  });
});
