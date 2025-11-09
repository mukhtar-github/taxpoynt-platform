'use client';

import React from 'react';
import { TaxPoyntButton } from '../../design_system';
import { HeroStatusChip, type HeroStatusChipConfig } from './SIDashboardHero';

interface ChecklistSummary {
  remainingPhases: number;
  nextPhaseTitle?: string;
  lastUpdated?: string;
}

interface SIDashboardSummaryProps {
  userName: string;
  bankingStatus: HeroStatusChipConfig;
  erpStatus: HeroStatusChipConfig;
  checklist: ChecklistSummary;
  onResumeOnboarding: () => void;
  onPrimaryAction: () => void;
  onSecondaryAction: () => void;
  onOpenAdvanced: () => void;
}

export const SIDashboardSummary: React.FC<SIDashboardSummaryProps> = ({
  userName,
  bankingStatus,
  erpStatus,
  checklist,
  onResumeOnboarding,
  onPrimaryAction,
  onSecondaryAction,
  onOpenAdvanced,
}) => {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm text-slate-500">Workspace overview</p>
            <h1 className="text-3xl font-semibold text-slate-900">Welcome back, {userName}</h1>
            <p className="text-sm text-slate-600">
              Keep automations on track by finishing the last checklist items and syncing data sources.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <HeroStatusChip config={bankingStatus} icon="🔌" data-testid="summary-banking-chip" />
            <HeroStatusChip config={erpStatus} icon="🧩" data-testid="summary-erp-chip" />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Checklist</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">
            {checklist.remainingPhases > 0
              ? `${checklist.remainingPhases} phase${checklist.remainingPhases === 1 ? '' : 's'} remaining`
              : 'All phases complete'}
          </h2>
          <p className="text-sm text-slate-600">
            {checklist.nextPhaseTitle
              ? `Next: ${checklist.nextPhaseTitle}`
              : 'Review your checklist anytime to keep the workspace compliant.'}
          </p>
          <TaxPoyntButton
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={onResumeOnboarding}
            data-testid="summary-resume-btn"
          >
            View checklist
          </TaxPoyntButton>
          {checklist.lastUpdated && (
            <p className="mt-2 text-xs text-slate-500">Updated {checklist.lastUpdated}</p>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Next actions</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Kick off your first batch</h2>
          <p className="text-sm text-slate-600">
            Send your first invoice batch or invite collaborators to help manage integrations.
          </p>
          <div className="mt-4 flex flex-col gap-2">
            <TaxPoyntButton variant="primary" onClick={onPrimaryAction} data-testid="summary-primary">
              Upload invoices
            </TaxPoyntButton>
            <TaxPoyntButton variant="outline" onClick={onSecondaryAction} data-testid="summary-secondary">
              Invite teammate
            </TaxPoyntButton>
          </div>
          <button
            type="button"
            onClick={onOpenAdvanced}
            className="mt-3 text-sm font-semibold text-indigo-600 hover:text-indigo-500"
            data-testid="summary-open-advanced"
          >
            Open advanced workspace →
          </button>
        </div>
      </section>
    </div>
  );
};
