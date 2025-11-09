'use client';

import React from 'react';
import { TaxPoyntButton } from '../../design_system';

export type HeroStatusTone = 'success' | 'warning' | 'info' | 'muted' | 'danger' | 'demo';

export interface HeroStatusChipConfig {
  label: string;
  helper: string;
  tone: HeroStatusTone;
}

export type ManualPullStatus = 'idle' | 'running' | 'success' | 'error';

export interface ManualPullConfig {
  modeLabel?: string;
  ctaLabel?: string;
  helper?: string;
  status?: ManualPullStatus;
  isDisabled?: boolean;
  onRun: () => Promise<void> | void;
}

export interface SIDashboardHeroProps {
  userName: string;
  bankingStatus: HeroStatusChipConfig;
  erpStatus: HeroStatusChipConfig;
  bankingManualPull?: ManualPullConfig;
  erpManualPull?: ManualPullConfig;
  onPrimaryAction: () => void;
  onSecondaryAction: () => void;
  onDismiss: () => void;
  primaryLabel?: string;
  secondaryLabel?: string;
}

const toneClasses: Record<HeroStatusTone, string> = {
  success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  muted: 'bg-slate-100 text-slate-700 border-slate-200',
  danger: 'bg-red-100 text-red-800 border-red-200',
  demo: 'bg-purple-100 text-purple-800 border-purple-200',
};

export const HeroStatusChip: React.FC<{
  config: HeroStatusChipConfig;
  icon: string;
  manualPull?: ManualPullConfig;
  'data-testid'?: string;
}> = ({ config, icon, manualPull, 'data-testid': dataTestId }) => {
  const manualStatus = manualPull?.status ?? 'idle';
  const isRunning = manualStatus === 'running';

  return (
  <div
    data-testid={dataTestId}
    className={`inline-flex min-w-[180px] flex-col rounded-2xl border px-4 py-3 text-left text-sm shadow-sm ${toneClasses[config.tone]}`}
  >
    <span className="text-xs font-semibold uppercase tracking-wide opacity-80">{icon} {config.label}</span>
    <span className="mt-1 text-sm font-medium">{config.helper}</span>
    {manualPull && (
      <div className="mt-3 rounded-xl bg-white/80 px-3 py-2 text-slate-700 shadow-inner" data-testid={dataTestId ? `${dataTestId}-manual` : undefined}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[0.6rem] font-semibold uppercase tracking-wide text-slate-500">Next pull</p>
            <p className="text-sm font-semibold text-slate-900">
              {manualPull.modeLabel ?? 'Manual'}
              {isRunning ? ' - running' : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void manualPull.onRun()}
            disabled={isRunning || manualPull.isDisabled}
            className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-70"
            data-testid={dataTestId ? `${dataTestId}-manual-run` : undefined}
          >
            {isRunning ? 'Running...' : manualPull.ctaLabel ?? 'Run now'}
          </button>
        </div>
        {manualPull.helper && (
          <p className="mt-2 text-xs text-slate-600" aria-live="polite">
            {manualPull.helper}
          </p>
        )}
      </div>
    )}
  </div>
  );
};

export const SIDashboardHero: React.FC<SIDashboardHeroProps> = ({
  userName,
  bankingStatus,
  erpStatus,
  bankingManualPull,
  erpManualPull,
  onPrimaryAction,
  onSecondaryAction,
  onDismiss,
  primaryLabel = 'Upload first invoices',
  secondaryLabel = 'Invite a teammate',
}) => {
  return (
    <section
      data-testid="si-dashboard-hero"
      className="rounded-3xl bg-gradient-to-br from-indigo-900 via-blue-900 to-slate-900 p-8 text-white shadow-2xl"
    >
      <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl space-y-4">
          <p className="text-sm uppercase tracking-[0.3em] text-indigo-200">Workspace ready</p>
          <h1 className="text-3xl font-bold sm:text-4xl">Welcome back, {userName}</h1>
          <p className="text-base text-indigo-100">
            You’ve completed onboarding. Start automating invoices, invite your finance teammates, or continue configuring
            connections—all from this workspace hub.
          </p>
          <div className="flex flex-wrap gap-3">
            <HeroStatusChip config={bankingStatus} icon="🔌" manualPull={bankingManualPull} data-testid="banking-status-chip" />
            <HeroStatusChip config={erpStatus} icon="🧩" manualPull={erpManualPull} data-testid="erp-status-chip" />
          </div>
          <p className="text-xs text-indigo-200">
            Manual pulls stay enabled in this workspace. Production will expose a 15-minute auto-sync toggle per{' '}
            <a
              href="https://github.com/mukhtar-github/taxpoynt-platform/blob/main/docs/development/sync_cadence_notes.md"
              target="_blank"
              rel="noreferrer"
              className="font-semibold underline underline-offset-2"
            >
              the sync cadence plan
            </a>
            .
          </p>
        </div>
        <div className="flex flex-col gap-4 rounded-2xl bg-white/10 p-6 backdrop-blur">
          <h2 className="text-lg font-semibold">Next actions</h2>
          <p className="text-sm text-indigo-100">
            Keep momentum going by sending your first batch or inviting collaborators.
          </p>
          <div className="flex flex-col gap-3">
            <TaxPoyntButton variant="primary" onClick={onPrimaryAction} data-testid="hero-primary-cta">
              {primaryLabel}
            </TaxPoyntButton>
            <TaxPoyntButton variant="outline" onClick={onSecondaryAction} data-testid="hero-secondary-cta">
              {secondaryLabel}
            </TaxPoyntButton>
          </div>
          <button
            type="button"
            onClick={onDismiss}
            data-testid="hero-dismiss"
            className="text-sm font-semibold text-indigo-200 hover:text-white"
          >
            View full dashboard →
          </button>
        </div>
      </div>
    </section>
  );
};
