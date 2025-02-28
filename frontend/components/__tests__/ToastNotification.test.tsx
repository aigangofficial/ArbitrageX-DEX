import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Toast } from '../ToastNotification';

describe('Toast Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders with correct message and type', () => {
    const onClose = jest.fn();
    render(
      <Toast
        message="Test message"
        type="success"
        onClose={onClose}
      />
    );

    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn();
    render(
      <Toast
        message="Test message"
        type="error"
        onClose={onClose}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('auto-closes after duration', () => {
    const onClose = jest.fn();
    render(
      <Toast
        message="Test message"
        type="info"
        onClose={onClose}
        duration={2000}
      />
    );

    act(() => {
      jest.advanceTimersByTime(2000);
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('applies correct styles based on type', () => {
    const { container, rerender } = render(
      <Toast
        message="Test message"
        type="success"
        onClose={() => {}}
      />
    );

    expect(container.firstChild).toHaveClass('bg-green-50');

    rerender(
      <Toast
        message="Test message"
        type="error"
        onClose={() => {}}
      />
    );

    expect(container.firstChild).toHaveClass('bg-red-50');
  });
}); 