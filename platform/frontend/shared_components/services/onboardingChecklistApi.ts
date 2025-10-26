import axios from 'axios';
import { authService } from './auth';

export interface ChecklistStep {
  id: string;
  canonical_id: string;
  title: string;
  description: string;
  success_criteria?: string;
  status: 'pending' | 'in_progress' | 'complete';
  completed: boolean;
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

const getBaseUrl = (): string => {
  const primaryApiUrl = process.env.NEXT_PUBLIC_API_URL;
  const legacyApiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (primaryApiUrl) {
    return primaryApiUrl.replace(/\/+$/, '');
  }
  if (legacyApiBase) {
    return `${legacyApiBase.replace(/\/+$/, '')}/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
};

const getAuthHeaders = () => {
  const token = authService.getToken();
  if (!token) {
    throw new Error('Authentication required');
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };

  const storedUser = authService.getStoredUser();
  if (storedUser?.id) {
    headers['X-User-Id'] = storedUser.id;
  }
  if (storedUser?.organization?.id) {
    headers['X-Organization-Id'] = storedUser.organization.id;
  }
  if (storedUser?.service_package) {
    headers['X-Service-Package'] = storedUser.service_package;
  }
  return headers;
};

export const onboardingChecklistApi = {
  async fetchChecklist(): Promise<ChecklistPayload> {
    const baseUrl = getBaseUrl();
    const headers = getAuthHeaders();
    const response = await axios.get(`${baseUrl}/si/onboarding/checklist`, { headers });
    const body = response.data ?? {};
    if (!body.success) {
      throw new Error(body.meta?.error || 'Failed to load onboarding checklist');
    }
    return body.data;
  },
};

export default onboardingChecklistApi;
