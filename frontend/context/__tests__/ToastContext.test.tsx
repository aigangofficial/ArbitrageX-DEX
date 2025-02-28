import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { ToastProvider, useToast } from '../ToastContext';

const TestComponent = () => {
  const { showToast } = useToast();
  return (
    <button onClick={() => showToast('Test Message', 'success')}>
      Show Toast
    </button>
  );
};

describe('ToastContext', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  it('shows toast message when showToast is called', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText('Show Toast');
    await act(async () => {
      button.click();
    });

    expect(screen.getByText('Test Message')).toBeInTheDocument();
  });

  it('removes toast after duration', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText('Show Toast');
    await act(async () => {
      button.click();
    });

    expect(screen.getByText('Test Message')).toBeInTheDocument();

    await act(async () => {
      jest.advanceTimersByTime(5000); // Default duration
    });

    expect(screen.queryByText('Test Message')).not.toBeInTheDocument();
  });

  it('throws error when useToast is used outside provider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useToast must be used within a ToastProvider');

    consoleError.mockRestore();
  });

  it('can show multiple toasts', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText('Show Toast');
    
    await act(async () => {
      button.click();
      button.click();
    });

    const toasts = screen.getAllByText('Test Message');
    expect(toasts).toHaveLength(2);
  });
}); 