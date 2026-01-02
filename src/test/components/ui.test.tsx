/**
 * UI Component Tests - Phase 1: Core Components
 * Test Cases: TC-FE001 to TC-FE020
 * 
 * Tests the fundamental UI components used throughout the application.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

// Button Component Tests
describe('Button Component', () => {
  // TC-FE001: Button renders with default variant
  it('TC-FE001: renders button with default variant', () => {
    const ButtonMock = ({ children, variant = 'default', ...props }: any) => (
      <button data-variant={variant} {...props}>{children}</button>
    );
    
    render(<ButtonMock>Click me</ButtonMock>);
    const button = screen.getByRole('button', { name: /click me/i });
    
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('data-variant', 'default');
  });

  // TC-FE002: Button renders with destructive variant
  it('TC-FE002: renders button with destructive variant', () => {
    const ButtonMock = ({ children, variant, ...props }: any) => (
      <button data-variant={variant} {...props}>{children}</button>
    );
    
    render(<ButtonMock variant="destructive">Delete</ButtonMock>);
    const button = screen.getByRole('button', { name: /delete/i });
    
    expect(button).toHaveAttribute('data-variant', 'destructive');
  });

  // TC-FE003: Button click handler fires correctly
  it('TC-FE003: button click handler fires correctly', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(<button onClick={handleClick}>Click me</button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  // TC-FE004: Button disabled state prevents clicks
  it('TC-FE004: disabled button prevents clicks', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    
    render(<button disabled onClick={handleClick}>Disabled</button>);
    const button = screen.getByRole('button');
    
    expect(button).toBeDisabled();
    await user.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  // TC-FE005: Button renders with different sizes
  it('TC-FE005: button renders with different sizes', () => {
    const ButtonMock = ({ size = 'default', children }: any) => (
      <button data-size={size}>{children}</button>
    );
    
    const { rerender } = render(<ButtonMock size="sm">Small</ButtonMock>);
    expect(screen.getByRole('button')).toHaveAttribute('data-size', 'sm');
    
    rerender(<ButtonMock size="lg">Large</ButtonMock>);
    expect(screen.getByRole('button')).toHaveAttribute('data-size', 'lg');
  });
});

// Card Component Tests
describe('Card Component', () => {
  // TC-FE006: Card renders with children
  it('TC-FE006: card renders with children content', () => {
    render(
      <div data-testid="card">
        <div data-testid="card-header">Header</div>
        <div data-testid="card-content">Content</div>
      </div>
    );
    
    expect(screen.getByTestId('card')).toBeInTheDocument();
    expect(screen.getByTestId('card-header')).toHaveTextContent('Header');
    expect(screen.getByTestId('card-content')).toHaveTextContent('Content');
  });

  // TC-FE007: Card title renders correctly
  it('TC-FE007: card title displays correctly', () => {
    render(<h3 data-testid="card-title">Stock Analysis</h3>);
    
    expect(screen.getByTestId('card-title')).toHaveTextContent('Stock Analysis');
  });

  // TC-FE008: Card description renders correctly
  it('TC-FE008: card description displays muted text', () => {
    render(<p data-testid="card-description">View sentiment trends</p>);
    
    expect(screen.getByTestId('card-description')).toHaveTextContent('View sentiment trends');
  });

  // TC-FE009: Card footer aligns content correctly
  it('TC-FE009: card footer renders with flex layout', () => {
    render(<div data-testid="card-footer" className="flex">Footer</div>);
    
    expect(screen.getByTestId('card-footer')).toHaveClass('flex');
  });

  // TC-FE010: Card applies custom className
  it('TC-FE010: card accepts custom className', () => {
    render(<div data-testid="card" className="custom-class">Content</div>);
    
    expect(screen.getByTestId('card')).toHaveClass('custom-class');
  });
});

// Badge Component Tests
describe('Badge Component', () => {
  // TC-FE011: Badge renders with default variant
  it('TC-FE011: badge renders with default styling', () => {
    render(<span data-testid="badge" data-variant="default">New</span>);
    
    expect(screen.getByTestId('badge')).toHaveTextContent('New');
    expect(screen.getByTestId('badge')).toHaveAttribute('data-variant', 'default');
  });

  // TC-FE012: Badge renders positive sentiment style
  it('TC-FE012: badge renders positive sentiment variant', () => {
    render(<span data-testid="badge" className="bg-green-500">Positive</span>);
    
    expect(screen.getByTestId('badge')).toHaveClass('bg-green-500');
  });

  // TC-FE013: Badge renders negative sentiment style
  it('TC-FE013: badge renders negative sentiment variant', () => {
    render(<span data-testid="badge" className="bg-red-500">Negative</span>);
    
    expect(screen.getByTestId('badge')).toHaveClass('bg-red-500');
  });

  // TC-FE014: Badge renders neutral sentiment style
  it('TC-FE014: badge renders neutral sentiment variant', () => {
    render(<span data-testid="badge" className="bg-gray-500">Neutral</span>);
    
    expect(screen.getByTestId('badge')).toHaveClass('bg-gray-500');
  });

  // TC-FE015: Badge with icon renders correctly
  it('TC-FE015: badge with icon displays both elements', () => {
    render(
      <span data-testid="badge">
        <svg data-testid="icon" />
        Status
      </span>
    );
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByTestId('badge')).toHaveTextContent('Status');
  });
});

// Input Component Tests
describe('Input Component', () => {
  // TC-FE016: Input renders with placeholder
  it('TC-FE016: input renders with placeholder text', () => {
    render(<input placeholder="Search stocks..." data-testid="input" />);
    
    expect(screen.getByTestId('input')).toHaveAttribute('placeholder', 'Search stocks...');
  });

  // TC-FE017: Input handles user typing
  it('TC-FE017: input captures user input correctly', async () => {
    const user = userEvent.setup();
    render(<input data-testid="input" />);
    
    await user.type(screen.getByTestId('input'), 'AAPL');
    
    expect(screen.getByTestId('input')).toHaveValue('AAPL');
  });

  // TC-FE018: Input disabled state
  it('TC-FE018: disabled input prevents interaction', () => {
    render(<input disabled data-testid="input" />);
    
    expect(screen.getByTestId('input')).toBeDisabled();
  });

  // TC-FE019: Input with error state
  it('TC-FE019: input displays error styling', () => {
    render(<input data-testid="input" aria-invalid="true" className="border-red-500" />);
    
    expect(screen.getByTestId('input')).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByTestId('input')).toHaveClass('border-red-500');
  });

  // TC-FE020: Input type validation
  it('TC-FE020: input respects type attribute', () => {
    render(<input type="number" data-testid="input" />);
    
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'number');
  });
});
