'use client';

import { onboardingApi } from './onboardingApi';
import { authService } from './auth';

export interface QueuePayload {
  step: string;
  completed?: boolean;
  completedSteps?: string[];
  metadata?: Record<string, any>;
  userId?: string;
  source?: string;
}

interface QueueEntry {
  payload: QueuePayload;
  fallback?: () => Promise<void>;
}

const VOLATILE_KEYS = new Set([
  'step_updated_at',
  'lastUpdate',
  'last_update',
  'lastActiveDate',
  'last_active_date',
  'timestamp',
]);

const normalizeMetadata = (value: any): any => {
  if (value === null || value === undefined) {
    return null;
  }
  if (Array.isArray(value)) {
    return value.map(normalizeMetadata);
  }
  if (typeof value === 'object') {
    return Object.entries(value)
      .filter(([key]) => !VOLATILE_KEYS.has(key))
      .sort(([a], [b]) => a.localeCompare(b))
      .reduce<Record<string, any>>((acc, [key, val]) => {
        acc[key] = normalizeMetadata(val);
        return acc;
      }, {});
  }
  return value;
};

const buildSignature = (payload: QueuePayload): string => {
  const steps = [...new Set(payload.completedSteps || [])].sort().join('|');
  const metadata = payload.metadata ? JSON.stringify(normalizeMetadata(payload.metadata)) : '';
  return `${payload.step}|${steps}|${metadata}`;
};

class OnboardingStateQueue {
  private pending = new Map<string, QueueEntry>();
  private processing = new Set<string>();
  private lastDispatched = new Map<string, string>();

  private resolveUserId(explicit?: string): string {
    if (explicit) {
      return explicit;
    }
    const user = authService.getStoredUser();
    return user?.id ?? 'anonymous';
  }

  private mergeEntries(current: QueueEntry | undefined, next: QueueEntry): QueueEntry {
    if (!current) {
      return next;
    }

    return {
      payload: {
        step: next.payload.step,
        completed: next.payload.completed ?? current.payload.completed,
        completedSteps: next.payload.completedSteps ?? current.payload.completedSteps,
        metadata: {
          ...(current.payload.metadata || {}),
          ...(next.payload.metadata || {}),
        },
        userId: next.payload.userId ?? current.payload.userId,
        source: next.payload.source || current.payload.source,
      },
      fallback: next.fallback ?? current.fallback,
    };
  }

  private async processQueue(userKey: string): Promise<void> {
    if (this.processing.has(userKey)) {
      return;
    }

    this.processing.add(userKey);
    try {
      while (this.pending.has(userKey)) {
        const entry = this.pending.get(userKey);
        if (!entry) {
          break;
        }
        this.pending.delete(userKey);

        const signature = buildSignature(entry.payload);
        if (this.lastDispatched.get(userKey) === signature) {
          continue;
        }

        const request = {
          current_step: entry.payload.step,
          completed_steps: entry.payload.completedSteps,
          metadata: entry.payload.metadata,
        };

        try {
          await onboardingApi.updateOnboardingState(request);
          this.lastDispatched.set(userKey, signature);
        } catch (error) {
          console.error('[OnboardingStateQueue] Failed to persist onboarding state:', error);
          if (entry.fallback) {
            try {
              await entry.fallback();
              this.lastDispatched.set(userKey, signature);
              continue;
            } catch (fallbackError) {
              console.error('[OnboardingStateQueue] Fallback also failed:', fallbackError);
            }
          }
          this.pending.set(userKey, entry);
          break;
        }
      }
    } finally {
      this.processing.delete(userKey);
    }
  }

  public async enqueue(payload: QueuePayload, options?: { fallback?: () => Promise<void> }): Promise<void> {
    if (!authService.isAuthenticated()) {
      console.info('[OnboardingStateQueue] Skip enqueue: user not authenticated.');
      return;
    }

    const userKey = this.resolveUserId(payload.userId);
    const entry: QueueEntry = { payload, fallback: options?.fallback };
    const merged = this.mergeEntries(this.pending.get(userKey), entry);
    this.pending.set(userKey, merged);
    await this.processQueue(userKey);
  }

  public clear(userId?: string): void {
    const key = this.resolveUserId(userId);
    this.pending.delete(key);
    this.processing.delete(key);
    this.lastDispatched.delete(key);
  }
}

export const onboardingStateQueue = new OnboardingStateQueue();
