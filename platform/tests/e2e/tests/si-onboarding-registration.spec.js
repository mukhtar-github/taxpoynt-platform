// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('SI onboarding registration and verification', () => {
  test('registers, verifies email, and marks checklist verify account step complete', async ({ page }) => {
    const email = `si-onboarding-${Date.now()}@example.com`;
    const userId = 'user-si-123';
    const orgId = 'org-si-456';

    const onboardingState = {
      user_id: userId,
      current_step: 'terms_acceptance',
      completed_steps: ['registration', 'email_verification', 'terms_acceptance'],
      has_started: true,
      is_complete: false,
      last_active_date: '2024-01-03T00:00:00Z',
      metadata: {
        service_package: 'si',
        account_status: {
          verified_at: '2024-01-02T09:02:00Z',
          terms_accepted_at: '2024-01-02T09:00:00Z',
        },
      },
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
      terms_accepted_at: '2024-01-02T09:00:00Z',
      verified_at: '2024-01-02T09:02:00Z',
    };

    const checklistPayload = {
      user_id: userId,
      service_package: 'si',
      current_phase: 'account-readiness',
      phases: [
        {
          id: 'account-readiness',
          title: 'Account readiness',
          description: 'Confirm account setup tasks.',
          status: 'in_progress',
          steps: [
            {
              id: 'verify-account',
              canonical_id: 'verify-account',
              title: 'Verify account',
              description: 'Email confirmed and terms accepted.',
              status: 'complete',
            },
            {
              id: 'service-selection',
              canonical_id: 'service-selection',
              title: 'Service selection',
              description: 'Choose your integration path.',
              status: 'in_progress',
            },
          ],
        },
        {
          id: 'integration-readiness',
          title: 'Integration readiness',
          description: 'Prepare business systems.',
          status: 'pending',
          steps: [],
        },
      ],
      summary: {
        completed_phases: [],
        remaining_phases: ['account-readiness', 'integration-readiness'],
        completion_percentage: 20,
      },
      updated_at: new Date().toISOString(),
    };

    await page.route('**/api/v1/auth/register', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'pending',
          next: '/auth/verify-email',
          user: {
            id: userId,
            email,
            first_name: 'Ayo',
            last_name: 'Okonkwo',
            phone: null,
            role: 'system_integrator',
            service_package: 'si',
            is_email_verified: false,
            organization: {
              id: orgId,
              name: 'Okonkwo Systems',
              business_type: 'technology',
              tin: null,
              rc_number: null,
              status: 'active',
              service_packages: ['si'],
            },
          },
          onboarding_token: 'stub-onboarding-token',
        }),
      });
    });

    await page.route('**/api/v1/auth/verify-email', async (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'stub-access-token',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: userId,
            email,
            first_name: 'Ayo',
            last_name: 'Okonkwo',
            phone: null,
            role: 'system_integrator',
            service_package: 'si',
            is_email_verified: true,
            organization: {
              id: orgId,
              name: 'Okonkwo Systems',
              business_type: 'technology',
              tin: null,
              rc_number: null,
              status: 'active',
              service_packages: ['si'],
            },
          },
        }),
      });
    });

    await page.route('**/api/v1/si/onboarding/state', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          action: 'onboarding_state_retrieved',
          api_version: 'v1',
          timestamp: new Date().toISOString(),
          data: onboardingState,
        }),
      });
    });

    await page.route('**/api/v1/si/onboarding/checklist', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          action: 'onboarding_checklist_retrieved',
          api_version: 'v1',
          timestamp: new Date().toISOString(),
          data: checklistPayload,
        }),
      });
    });

    await page.route('**/api/v1/si/dashboard/metrics', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {},
        }),
      });
    });

    await page.goto('/auth/signup?service=si&next=%2Fdashboard%2Fsi');

    await page.getByLabel('First name').fill('Ayo');
    await page.getByLabel('Last name').fill('Okonkwo');
    await page.getByLabel('Work email').fill(email);
    await page.getByLabel('Create password').fill('SecurePass123!');
    await page.getByLabel('Business or workspace name').fill('Okonkwo Systems');

    await Promise.all([
      page.waitForURL(/auth\/verify-email/),
      page.getByRole('button', { name: /Continue to email verification/i }).click(),
    ]);

    await page.getByLabel('Verification code').fill('123456');
    await page.getByLabel(/I agree to the TaxPoynt Terms of Service/i).check();
    await page.getByLabel(/I acknowledge the Privacy Policy/i).check();

    await page.getByRole('button', { name: /Verify email and continue/i }).click();
    await expect(page.getByText('Saving…')).toBeVisible();
    await expect(page.getByText(/Saved at/i)).toBeVisible();
    await page.waitForURL('**/dashboard/si', { timeout: 10000 });

    await expect(page.getByText('Onboarding checklist')).toBeVisible();
    const verifyAccountItem = page.locator('li', { hasText: 'Verify account' }).first();
    await expect(verifyAccountItem).toHaveClass(/bg-emerald-50/);
    await expect(verifyAccountItem).toHaveClass(/text-emerald-700/);
  });
});
