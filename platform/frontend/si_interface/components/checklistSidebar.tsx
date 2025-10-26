import React, { useMemo } from 'react';
import { Info } from 'lucide-react';

const cn = (...classes: Array<string | false | null | undefined>) =>
  classes.filter(Boolean).join(' ');

export interface ChecklistStep {
  id: string;
  canonical_id: string;
  title: string;
  description: string;
  success_criteria?: string;
  status: 'pending' | 'in_progress' | 'complete';
}

export interface ChecklistPhase {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'complete';
  steps: ChecklistStep[];
}

export interface ChecklistSummary {
  completed_phases: string[];
  remaining_phases: string[];
  completion_percentage: number;
}

export interface ChecklistPayload {
  user_id: string;
  service_package: string;
  current_phase?: string | null;
  phases: ChecklistPhase[];
  summary: ChecklistSummary;
  updated_at: string;
}

interface ChecklistSidebarProps {
  checklist: ChecklistPayload | null;
  onResume?: () => void;
  onViewGuidance?: (phaseId: string) => void;
  className?: string;
}

const STATUS_CLASSES: Record<ChecklistStep['status'], string> = {
  pending: 'bg-gray-100 text-gray-600 border border-gray-200',
  in_progress: 'bg-blue-50 text-blue-700 border border-blue-300',
  complete: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
};

const STATUS_DOT_CLASSES: Record<ChecklistStep['status'], string> = {
  pending: 'bg-gray-300',
  in_progress: 'bg-blue-500 animate-pulse',
  complete: 'bg-emerald-500',
};

export const ChecklistSidebar: React.FC<ChecklistSidebarProps> = ({
  checklist,
  onResume,
  onViewGuidance,
  className,
}) => {
  const completionPercentage = checklist?.summary?.completion_percentage ?? 0;

  const sortedPhases = useMemo(() => {
    if (!checklist) {
      return [];
    }
    return [...checklist.phases];
  }, [checklist]);

  return (
    <aside className={cn('rounded-xl border border-gray-200 bg-white p-4 shadow-sm', className)}>
      <header className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
          Onboarding checklist
        </p>
        <h3 className="mt-1 text-lg font-semibold text-gray-900">
          Complete your setup
        </h3>
        <p className="text-sm text-gray-600">
          Progress through the key milestones to unlock the full System Integrator experience.
        </p>
      </header>

      <div className="mb-4">
        <div className="flex items-center justify-between text-xs font-medium text-gray-600">
          <span>{completionPercentage}% complete</span>
          <span>
            {checklist?.summary?.completed_phases.length ?? 0} /
            {sortedPhases.length} phases
          </span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
          <div
            className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${Math.max(completionPercentage, 5)}%` }}
            aria-hidden="true"
          />
        </div>
      </div>

      <ul className="space-y-4">
    {sortedPhases.map(phase => {
        const isCurrent = phase.id === checklist?.current_phase;
          const hasInProgressStep = phase.steps.some(step => step.status === 'in_progress');
          const phaseClass =
            phase.status === 'complete'
              ? 'bg-emerald-50 border border-emerald-200'
              : isCurrent || hasInProgressStep
              ? 'bg-blue-50 border border-blue-200'
              : 'bg-gray-50 border border-gray-100';

          return (
            <li
              key={phase.id}
              className={cn(
                'rounded-lg p-3 transition focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2',
                phaseClass,
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{phase.title}</p>
                  <p className="text-xs text-gray-600">{phase.description}</p>
                </div>
                {onViewGuidance && (
                  <button
                    type="button"
                    className="text-xs font-medium text-blue-600 hover:text-blue-500"
                    onClick={() => onViewGuidance(phase.id)}
                  >
                    Guidance
                  </button>
                )}
              </div>

              <ul className="mt-3 space-y-2">
                {phase.steps.map(step => (
                  <li
                    key={step.id}
                    className={cn(
                      'flex items-start gap-3 rounded-md border px-3 py-2 text-sm',
                      STATUS_CLASSES[step.status],
                    )}
                  >
                    <span
                      className={cn(
                        'mt-1 inline-block h-2 w-2 rounded-full',
                        STATUS_DOT_CLASSES[step.status],
                      )}
                      aria-hidden="true"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{step.title}</span>
                        {step.success_criteria && (
                          <span
                            className="inline-flex items-center gap-1 text-xs text-blue-600"
                            title={step.success_criteria}
                          >
                            <Info className="h-3 w-3" aria-hidden="true" />
                            Success criteria
                          </span>
                        )}
                      </div>
                      {step.description && (
                        <p className="text-xs text-gray-600">{step.description}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>

      {onResume && (
        <button
          type="button"
          className="mt-4 w-full rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 transition hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          onClick={onResume}
        >
          Resume onboarding wizard
        </button>
      )}
    </aside>
  );
};

export default ChecklistSidebar;
