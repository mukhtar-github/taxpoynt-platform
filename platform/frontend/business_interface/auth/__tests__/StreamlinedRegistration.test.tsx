import React from 'react';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { StreamlinedRegistration } from '../StreamlinedRegistration';
import { resetBusinessEmailPolicyCache } from '../../../shared_components/utils/businessEmailPolicy';

const mockOnComplete = jest.fn().mockResolvedValue(undefined);

jest.mock('../../../shared_components/auth/AuthLayout', () => ({
  AuthLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('../../../design_system/components/FormField', () => ({
  FormField: ({
    label,
    name,
    type = 'text',
    value,
    onChange,
    error,
  }: {
    label: string;
    name: string;
    type?: string;
    value: string;
    onChange: (value: string) => void;
    error?: string;
  }) => (
    <div>
      <label>
        {label}
        <input
          aria-label={label}
          name={name}
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
      {error ? (
        <div role="alert" aria-live="assertive">
          {error}
        </div>
      ) : null}
    </div>
  ),
}));

jest.mock('../../../design_system/components/TaxPoyntButton', () => ({
  TaxPoyntButton: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
}));

jest.mock('../../../shared_components/utils/secureLogger', () => ({
  secureLogger: {
    userAction: jest.fn(),
  },
}));

const fillRequiredFields = (overrides?: { email?: string }) => {
  fireEvent.change(screen.getByLabelText(/First name/i), { target: { value: 'Ada' } });
  fireEvent.change(screen.getByLabelText(/Last name/i), { target: { value: 'Okeke' } });
  fireEvent.change(screen.getByLabelText(/Work email/i), {
    target: { value: overrides?.email ?? 'ada@enterprise.com' },
  });
  fireEvent.change(screen.getByLabelText(/Create password/i), { target: { value: 'Password123!' } });
  fireEvent.change(screen.getByLabelText(/Business or workspace name/i), {
    target: { value: 'Ada Ventures' },
  });
};

describe('StreamlinedRegistration business email validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    delete process.env.NEXT_PUBLIC_BUSINESS_EMAIL_POLICY_MODE;
    delete process.env.NEXT_PUBLIC_BUSINESS_EMAIL_DENYLIST;
    delete process.env.NEXT_PUBLIC_BUSINESS_EMAIL_ALLOWLIST;
    resetBusinessEmailPolicyCache();
  });

  it('prevents submitting with a free-email domain by default', async () => {
    render(<StreamlinedRegistration onCompleteRegistration={mockOnComplete} />);

    fillRequiredFields({ email: 'pilot@gmail.com' });

    fireEvent.click(screen.getByRole('button', { name: /continue to email verification/i }));

    await waitFor(() => {
      expect(mockOnComplete).not.toHaveBeenCalled();
    });

    expect(
      screen.getByText(/Use your business email \(for example, you@company\.com\) to continue\./i)
    ).toBeInTheDocument();
  });

  it('honours allowlisted domains when configured', async () => {
    process.env.NEXT_PUBLIC_BUSINESS_EMAIL_ALLOWLIST = 'gmail.com';
    resetBusinessEmailPolicyCache();

    render(<StreamlinedRegistration onCompleteRegistration={mockOnComplete} />);

    fillRequiredFields({ email: 'pilot@gmail.com' });

    fireEvent.click(screen.getByRole('button', { name: /continue to email verification/i }));

    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });
});
