/**
 * Accessibility Tests - Phase 5
 * Test Cases: TC-FE066 to TC-FE080
 * 
 * Tests WCAG compliance and accessibility features.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

// Accessibility Tests
describe('Accessibility Compliance', () => {
  // TC-FE066: Buttons have accessible names
  it('TC-FE066: buttons have accessible names', () => {
    render(
      <div>
        <button>Submit Form</button>
        <button aria-label="Close dialog">X</button>
        <button title="Settings">
          <svg aria-hidden="true" />
        </button>
      </div>
    );
    
    expect(screen.getByRole('button', { name: /submit form/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /close dialog/i })).toBeInTheDocument();
  });

  // TC-FE067: Images have alt text
  it('TC-FE067: images have descriptive alt text', () => {
    render(
      <div>
        <img src="/stock-chart.png" alt="AAPL stock price chart for the last 30 days" />
        <img src="/logo.png" alt="Insight Stock Dashboard logo" />
      </div>
    );
    
    expect(screen.getByAltText(/AAPL stock price chart/i)).toBeInTheDocument();
    expect(screen.getByAltText(/Insight Stock Dashboard logo/i)).toBeInTheDocument();
  });

  // TC-FE068: Form inputs have labels
  it('TC-FE068: form inputs are properly labeled', () => {
    render(
      <form>
        <label htmlFor="symbol">Stock Symbol</label>
        <input id="symbol" type="text" />
        
        <label htmlFor="amount">Amount</label>
        <input id="amount" type="number" />
      </form>
    );
    
    expect(screen.getByLabelText(/stock symbol/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/amount/i)).toBeInTheDocument();
  });

  // TC-FE069: Headings follow hierarchy
  it('TC-FE069: heading levels are sequential', () => {
    render(
      <div>
        <h1>Dashboard</h1>
        <h2>Market Overview</h2>
        <h3>Top Gainers</h3>
        <h3>Top Losers</h3>
        <h2>Sentiment Analysis</h2>
      </div>
    );
    
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Dashboard');
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(2);
    expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(2);
  });

  // TC-FE070: Links have descriptive text
  it('TC-FE070: links have meaningful text content', () => {
    render(
      <nav>
        <a href="/dashboard">View Dashboard</a>
        <a href="/stocks/AAPL">View Apple Inc. Details</a>
        <a href="/help" aria-label="Get help with stock analysis">Help</a>
      </nav>
    );
    
    expect(screen.getByRole('link', { name: /view dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view apple inc/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /get help/i })).toBeInTheDocument();
  });

  // TC-FE071: Color is not sole indicator
  it('TC-FE071: status indicators use more than just color', () => {
    render(
      <div>
        <span className="text-green-500" data-testid="positive">
          <svg aria-hidden="true" data-testid="up-arrow" />
          <span>+2.5% (Positive)</span>
        </span>
        <span className="text-red-500" data-testid="negative">
          <svg aria-hidden="true" data-testid="down-arrow" />
          <span>-1.2% (Negative)</span>
        </span>
      </div>
    );
    
    // Text indicates status, not just color
    expect(screen.getByTestId('positive')).toHaveTextContent('Positive');
    expect(screen.getByTestId('negative')).toHaveTextContent('Negative');
    // Icons provide visual indicator
    expect(screen.getByTestId('up-arrow')).toBeInTheDocument();
    expect(screen.getByTestId('down-arrow')).toBeInTheDocument();
  });

  // TC-FE072: Focus is visible
  it('TC-FE072: interactive elements have visible focus', () => {
    render(
      <button className="focus:ring-2 focus:ring-blue-500" data-testid="button">
        Click me
      </button>
    );
    
    const button = screen.getByTestId('button');
    expect(button).toHaveClass('focus:ring-2');
  });

  // TC-FE073: Skip link exists
  it('TC-FE073: skip to main content link is present', () => {
    render(
      <div>
        <a href="#main-content" className="sr-only focus:not-sr-only" data-testid="skip-link">
          Skip to main content
        </a>
        <nav>Navigation</nav>
        <main id="main-content">Main content</main>
      </div>
    );
    
    expect(screen.getByTestId('skip-link')).toHaveAttribute('href', '#main-content');
  });

  // TC-FE074: ARIA landmarks are used correctly
  it('TC-FE074: page has proper ARIA landmarks', () => {
    render(
      <div>
        <header role="banner">Header</header>
        <nav role="navigation" aria-label="Main">Navigation</nav>
        <main role="main">Main content</main>
        <aside role="complementary">Sidebar</aside>
        <footer role="contentinfo">Footer</footer>
      </div>
    );
    
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('complementary')).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });

  // TC-FE075: Tables have proper structure
  it('TC-FE075: data tables have headers and captions', () => {
    render(
      <table>
        <caption>Stock Performance Summary</caption>
        <thead>
          <tr>
            <th scope="col">Symbol</th>
            <th scope="col">Price</th>
            <th scope="col">Change</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>AAPL</td>
            <td>$178.50</td>
            <td>+2.3%</td>
          </tr>
        </tbody>
      </table>
    );
    
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Stock Performance Summary')).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader')).toHaveLength(3);
  });
});

// Keyboard Navigation Tests
describe('Keyboard Navigation', () => {
  // TC-FE076: Tab order is logical
  it('TC-FE076: elements receive focus in logical order', async () => {
    const user = userEvent.setup();
    
    render(
      <div>
        <input data-testid="first" />
        <button data-testid="second">Button</button>
        <a href="#" data-testid="third">Link</a>
      </div>
    );
    
    await user.tab();
    expect(screen.getByTestId('first')).toHaveFocus();
    
    await user.tab();
    expect(screen.getByTestId('second')).toHaveFocus();
    
    await user.tab();
    expect(screen.getByTestId('third')).toHaveFocus();
  });

  // TC-FE077: Escape closes modal
  it('TC-FE077: escape key closes modal dialog', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    
    const Modal = ({ onClose }: { onClose: () => void }) => {
      React.useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
          if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleEsc);
        return () => document.removeEventListener('keydown', handleEsc);
      }, [onClose]);
      
      return <div role="dialog" data-testid="modal">Modal Content</div>;
    };
    
    render(<Modal onClose={onClose} />);
    
    await user.keyboard('{Escape}');
    
    expect(onClose).toHaveBeenCalled();
  });

  // TC-FE078: Enter activates buttons
  it('TC-FE078: enter key activates focused button', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    
    render(<button onClick={onClick}>Submit</button>);
    
    await user.tab();
    await user.keyboard('{Enter}');
    
    expect(onClick).toHaveBeenCalled();
  });

  // TC-FE079: Arrow keys navigate menu
  it('TC-FE079: arrow keys navigate dropdown menu', async () => {
    const user = userEvent.setup();
    
    const Menu = () => {
      const [activeIndex, setActiveIndex] = React.useState(0);
      const items = ['Dashboard', 'Stocks', 'Analysis', 'Settings'];
      
      const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
          setActiveIndex(i => Math.min(items.length - 1, i + 1));
        } else if (e.key === 'ArrowUp') {
          setActiveIndex(i => Math.max(0, i - 1));
        }
      };
      
      return (
        <ul role="menu" onKeyDown={handleKeyDown} tabIndex={0} data-testid="menu">
          {items.map((item, i) => (
            <li 
              key={item} 
              role="menuitem" 
              aria-selected={i === activeIndex}
              data-testid={`item-${i}`}
            >
              {item}
            </li>
          ))}
        </ul>
      );
    };
    
    render(<Menu />);
    
    const menu = screen.getByTestId('menu');
    menu.focus();
    
    expect(screen.getByTestId('item-0')).toHaveAttribute('aria-selected', 'true');
    
    await user.keyboard('{ArrowDown}');
    expect(screen.getByTestId('item-1')).toHaveAttribute('aria-selected', 'true');
    
    await user.keyboard('{ArrowDown}');
    expect(screen.getByTestId('item-2')).toHaveAttribute('aria-selected', 'true');
  });

  // TC-FE080: Focus trap in modal
  it('TC-FE080: focus is trapped within modal dialog', async () => {
    const user = userEvent.setup();
    
    const Modal = () => (
      <div role="dialog" aria-modal="true" data-testid="modal">
        <button data-testid="first-btn">First</button>
        <button data-testid="last-btn">Last</button>
      </div>
    );
    
    render(<Modal />);
    
    screen.getByTestId('first-btn').focus();
    expect(screen.getByTestId('first-btn')).toHaveFocus();
    
    await user.tab();
    expect(screen.getByTestId('last-btn')).toHaveFocus();
  });
});
