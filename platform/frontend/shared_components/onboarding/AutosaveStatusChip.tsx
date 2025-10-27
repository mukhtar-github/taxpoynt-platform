import React from 'react';

export type AutosaveStatus = 'idle' | 'saving' | 'saved' | 'error';

export interface AutosaveStatusChipProps {
  status: AutosaveStatus;
  lastSavedAt?: Date | null;
  message?: string | null;
  className?: string;
}

const formatSavedTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-NG', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export const AutosaveStatusChip: React.FC<AutosaveStatusChipProps> = ({
  status,
  lastSavedAt,
  message,
  className = '',
}) => {
  if (status === 'idle' && !lastSavedAt) {
    return null;
  }

  let content: React.ReactNode = null;
  let chipClass = 'bg-slate-100 text-slate-600 border border-slate-200';

  if (status === 'saving') {
    chipClass = 'bg-blue-50 text-blue-700 border border-blue-200';
    content = 'Saving…';
  } else if (status === 'error') {
    chipClass = 'bg-red-50 text-red-700 border border-red-200';
    content = message ?? 'Autosave failed';
  } else if (status === 'saved' && lastSavedAt) {
    chipClass = 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    content = `Saved at ${formatSavedTime(lastSavedAt)}`;
  } else if (lastSavedAt) {
    content = `Last saved at ${formatSavedTime(lastSavedAt)}`;
  }

  if (!content) {
    return null;
  }

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${chipClass} ${className}`}>
      {content}
    </span>
  );
};

export default AutosaveStatusChip;
