import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useIdleTelemetry } from '../useIdleTelemetry';

const TestComponent: React.FC<{ enabled: boolean; timeoutMs: number; onIdle: () => void }> = ({
  enabled,
  timeoutMs,
  onIdle,
}) => {
  useIdleTelemetry({ enabled, timeoutMs, onIdle });
  return <div data-testid="idle-test" />;
};

describe('useIdleTelemetry', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('fires onIdle after timeout when enabled', () => {
    const handler = jest.fn();
    render(<TestComponent enabled timeoutMs={1000} onIdle={handler} />);

    expect(handler).not.toHaveBeenCalled();
    jest.advanceTimersByTime(999);
    expect(handler).not.toHaveBeenCalled();
    jest.advanceTimersByTime(1);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not fire when disabled', () => {
    const handler = jest.fn();
    render(<TestComponent enabled={false} timeoutMs={1000} onIdle={handler} />);
    jest.advanceTimersByTime(5000);
    expect(handler).not.toHaveBeenCalled();
  });
});
