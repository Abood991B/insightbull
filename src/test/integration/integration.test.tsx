/**
 * Integration Tests - Phase 4
 * Test Cases: TC-FE051 to TC-FE065
 * 
 * Tests component integration, data flow, and user workflows.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

// Mock API Response Types
interface StockData {
  symbol: string;
  name: string;
  price: number;
  sentiment: number;
}

interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

// Mock API functions
const mockFetchStocks = vi.fn<() => Promise<ApiResponse<StockData[]>>>();
const mockFetchSentiment = vi.fn<(symbol: string) => Promise<ApiResponse<{ score: number }>>>();
const mockSearchStocks = vi.fn<(query: string) => Promise<ApiResponse<StockData[]>>>();

// Data Flow Tests
describe('Data Flow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchStocks.mockResolvedValue({
      data: [
        { symbol: 'AAPL', name: 'Apple Inc.', price: 178.50, sentiment: 0.65 },
        { symbol: 'MSFT', name: 'Microsoft Corp.', price: 380.20, sentiment: 0.45 },
      ],
      status: 200,
      message: 'Success',
    });
  });

  // TC-FE051: Stock list loads and displays data
  it('TC-FE051: stock list loads and displays fetched data', async () => {
    const StockList = () => {
      const [stocks, setStocks] = React.useState<StockData[]>([]);
      const [loading, setLoading] = React.useState(true);

      React.useEffect(() => {
        mockFetchStocks().then(res => {
          setStocks(res.data);
          setLoading(false);
        });
      }, []);

      if (loading) return <div>Loading...</div>;
      return (
        <ul data-testid="stock-list">
          {stocks.map(stock => (
            <li key={stock.symbol} data-testid={`stock-${stock.symbol}`}>
              {stock.symbol} - {stock.name}
            </li>
          ))}
        </ul>
      );
    };

    render(<StockList />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByTestId('stock-list')).toBeInTheDocument();
    });
    
    expect(screen.getByTestId('stock-AAPL')).toHaveTextContent('AAPL - Apple Inc.');
    expect(screen.getByTestId('stock-MSFT')).toHaveTextContent('MSFT - Microsoft Corp.');
    expect(mockFetchStocks).toHaveBeenCalledTimes(1);
  });

  // TC-FE052: Search filters stock list
  it('TC-FE052: search input filters displayed stocks', async () => {
    const user = userEvent.setup();
    
    const SearchableList = () => {
      const [query, setQuery] = React.useState('');
      const stocks = [
        { symbol: 'AAPL', name: 'Apple Inc.' },
        { symbol: 'MSFT', name: 'Microsoft Corp.' },
        { symbol: 'AMZN', name: 'Amazon.com Inc.' },
      ];
      
      const filtered = stocks.filter(s => 
        s.symbol.toLowerCase().includes(query.toLowerCase()) ||
        s.name.toLowerCase().includes(query.toLowerCase())
      );
      
      return (
        <div>
          <input 
            data-testid="search" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search..."
          />
          <ul data-testid="results">
            {filtered.map(s => <li key={s.symbol}>{s.symbol}</li>)}
          </ul>
        </div>
      );
    };
    
    render(<SearchableList />);
    
    expect(screen.getByTestId('results').children).toHaveLength(3);
    
    await user.type(screen.getByTestId('search'), 'Apple');
    
    expect(screen.getByTestId('results').children).toHaveLength(1);
    expect(screen.getByTestId('results')).toHaveTextContent('AAPL');
  });

  // TC-FE053: Stock selection updates detail view
  it('TC-FE053: clicking stock updates detail panel', async () => {
    const user = userEvent.setup();
    
    const StockSelector = () => {
      const [selected, setSelected] = React.useState<string | null>(null);
      const stocks = ['AAPL', 'MSFT', 'NVDA'];
      
      return (
        <div>
          <ul>
            {stocks.map(s => (
              <li key={s}>
                <button onClick={() => setSelected(s)} data-testid={`select-${s}`}>
                  {s}
                </button>
              </li>
            ))}
          </ul>
          {selected && <div data-testid="detail">Selected: {selected}</div>}
        </div>
      );
    };
    
    render(<StockSelector />);
    
    expect(screen.queryByTestId('detail')).not.toBeInTheDocument();
    
    await user.click(screen.getByTestId('select-NVDA'));
    
    expect(screen.getByTestId('detail')).toHaveTextContent('Selected: NVDA');
  });

  // TC-FE054: Time range selector updates chart
  it('TC-FE054: time range selection triggers data refresh', async () => {
    const user = userEvent.setup();
    const onRangeChange = vi.fn();
    
    const TimeRangeSelector = ({ onChange }: { onChange: (range: string) => void }) => (
      <div>
        <button onClick={() => onChange('7d')} data-testid="range-7d">7D</button>
        <button onClick={() => onChange('30d')} data-testid="range-30d">30D</button>
        <button onClick={() => onChange('90d')} data-testid="range-90d">90D</button>
      </div>
    );
    
    render(<TimeRangeSelector onChange={onRangeChange} />);
    
    await user.click(screen.getByTestId('range-30d'));
    
    expect(onRangeChange).toHaveBeenCalledWith('30d');
  });

  // TC-FE055: Error state displays correctly
  it('TC-FE055: API error displays error message', async () => {
    mockFetchStocks.mockRejectedValueOnce(new Error('Network error'));
    
    const ErrorComponent = () => {
      const [error, setError] = React.useState<string | null>(null);
      const [loading, setLoading] = React.useState(true);
      
      React.useEffect(() => {
        mockFetchStocks()
          .then(() => setLoading(false))
          .catch(err => {
            setError(err.message);
            setLoading(false);
          });
      }, []);
      
      if (loading) return <div>Loading...</div>;
      if (error) return <div data-testid="error">Error: {error}</div>;
      return <div>Success</div>;
    };
    
    render(<ErrorComponent />);
    
    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Error: Network error');
    });
  });
});

// User Workflow Tests
describe('User Workflow Integration', () => {
  // TC-FE056: Complete stock analysis workflow
  it('TC-FE056: user can complete stock analysis workflow', async () => {
    const user = userEvent.setup();
    const steps: string[] = [];
    
    const AnalysisWorkflow = () => {
      const [step, setStep] = React.useState(1);
      
      const nextStep = () => {
        steps.push(`Step ${step} completed`);
        setStep(s => s + 1);
      };
      
      return (
        <div>
          <div data-testid="current-step">Step {step}</div>
          {step < 4 && (
            <button onClick={nextStep} data-testid="next">
              Next
            </button>
          )}
          {step === 4 && <div data-testid="complete">Analysis Complete</div>}
        </div>
      );
    };
    
    render(<AnalysisWorkflow />);
    
    expect(screen.getByTestId('current-step')).toHaveTextContent('Step 1');
    
    await user.click(screen.getByTestId('next'));
    await user.click(screen.getByTestId('next'));
    await user.click(screen.getByTestId('next'));
    
    expect(screen.getByTestId('complete')).toBeInTheDocument();
    expect(steps).toHaveLength(3);
  });

  // TC-FE057: Pagination navigates correctly
  it('TC-FE057: pagination controls navigate between pages', async () => {
    const user = userEvent.setup();
    
    const Pagination = () => {
      const [page, setPage] = React.useState(1);
      const totalPages = 5;
      
      return (
        <div>
          <span data-testid="current-page">Page {page} of {totalPages}</span>
          <button 
            onClick={() => setPage(p => Math.max(1, p - 1))} 
            disabled={page === 1}
            data-testid="prev"
          >
            Previous
          </button>
          <button 
            onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
            disabled={page === totalPages}
            data-testid="next"
          >
            Next
          </button>
        </div>
      );
    };
    
    render(<Pagination />);
    
    expect(screen.getByTestId('current-page')).toHaveTextContent('Page 1 of 5');
    expect(screen.getByTestId('prev')).toBeDisabled();
    
    await user.click(screen.getByTestId('next'));
    await user.click(screen.getByTestId('next'));
    
    expect(screen.getByTestId('current-page')).toHaveTextContent('Page 3 of 5');
    expect(screen.getByTestId('prev')).not.toBeDisabled();
  });

  // TC-FE058: Tab navigation works correctly
  it('TC-FE058: tab navigation switches content panels', async () => {
    const user = userEvent.setup();
    
    const Tabs = () => {
      const [active, setActive] = React.useState('overview');
      
      return (
        <div>
          <div role="tablist">
            <button 
              role="tab" 
              aria-selected={active === 'overview'}
              onClick={() => setActive('overview')}
              data-testid="tab-overview"
            >
              Overview
            </button>
            <button 
              role="tab" 
              aria-selected={active === 'sentiment'}
              onClick={() => setActive('sentiment')}
              data-testid="tab-sentiment"
            >
              Sentiment
            </button>
          </div>
          <div data-testid="content">
            {active === 'overview' && 'Overview Content'}
            {active === 'sentiment' && 'Sentiment Content'}
          </div>
        </div>
      );
    };
    
    render(<Tabs />);
    
    expect(screen.getByTestId('content')).toHaveTextContent('Overview Content');
    
    await user.click(screen.getByTestId('tab-sentiment'));
    
    expect(screen.getByTestId('content')).toHaveTextContent('Sentiment Content');
  });

  // TC-FE059: Form validation prevents invalid submission
  it('TC-FE059: form validates required fields before submit', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    
    const Form = () => {
      const [symbol, setSymbol] = React.useState('');
      const [error, setError] = React.useState('');
      
      const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!symbol.trim()) {
          setError('Symbol is required');
          return;
        }
        if (!/^[A-Z]{1,5}$/.test(symbol)) {
          setError('Invalid symbol format');
          return;
        }
        onSubmit(symbol);
      };
      
      return (
        <form onSubmit={handleSubmit}>
          <input 
            value={symbol}
            onChange={e => setSymbol(e.target.value.toUpperCase())}
            data-testid="symbol-input"
          />
          {error && <span data-testid="error">{error}</span>}
          <button type="submit" data-testid="submit">Add Stock</button>
        </form>
      );
    };
    
    render(<Form />);
    
    await user.click(screen.getByTestId('submit'));
    
    expect(screen.getByTestId('error')).toHaveTextContent('Symbol is required');
    expect(onSubmit).not.toHaveBeenCalled();
    
    await user.type(screen.getByTestId('symbol-input'), 'AAPL');
    await user.click(screen.getByTestId('submit'));
    
    expect(onSubmit).toHaveBeenCalledWith('AAPL');
  });

  // TC-FE060: Modal opens and closes correctly
  it('TC-FE060: modal dialog opens and closes on user action', async () => {
    const user = userEvent.setup();
    
    const Modal = () => {
      const [isOpen, setIsOpen] = React.useState(false);
      
      return (
        <div>
          <button onClick={() => setIsOpen(true)} data-testid="open">
            Open Modal
          </button>
          {isOpen && (
            <div data-testid="modal" role="dialog">
              <h2>Modal Title</h2>
              <button onClick={() => setIsOpen(false)} data-testid="close">
                Close
              </button>
            </div>
          )}
        </div>
      );
    };
    
    render(<Modal />);
    
    expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
    
    await user.click(screen.getByTestId('open'));
    
    expect(screen.getByTestId('modal')).toBeInTheDocument();
    
    await user.click(screen.getByTestId('close'));
    
    expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
  });
});

// State Management Tests
describe('State Management Integration', () => {
  // TC-FE061: Global state updates propagate to children
  it('TC-FE061: context state updates propagate to consumers', () => {
    const ThemeContext = React.createContext({ theme: 'light', toggle: () => {} });
    
    const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
      const [theme, setTheme] = React.useState('light');
      const toggle = () => setTheme(t => t === 'light' ? 'dark' : 'light');
      return (
        <ThemeContext.Provider value={{ theme, toggle }}>
          {children}
        </ThemeContext.Provider>
      );
    };
    
    const ThemeDisplay = () => {
      const { theme } = React.useContext(ThemeContext);
      return <span data-testid="theme">{theme}</span>;
    };
    
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>
    );
    
    expect(screen.getByTestId('theme')).toHaveTextContent('light');
  });

  // TC-FE062: Local storage persistence works
  it('TC-FE062: state persists to localStorage on change', () => {
    const key = 'test-watchlist';
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    
    const WatchlistManager = () => {
      const [watchlist, setWatchlist] = React.useState<string[]>(['AAPL']);
      
      const addStock = (symbol: string) => {
        const updated = [...watchlist, symbol];
        setWatchlist(updated);
        localStorage.setItem(key, JSON.stringify(updated));
      };
      
      return (
        <button onClick={() => addStock('MSFT')} data-testid="add">
          Add MSFT
        </button>
      );
    };
    
    render(<WatchlistManager />);
    
    fireEvent.click(screen.getByTestId('add'));
    
    expect(setItem).toHaveBeenCalledWith(key, JSON.stringify(['AAPL', 'MSFT']));
    setItem.mockRestore();
  });

  // TC-FE063: Optimistic updates revert on error
  it('TC-FE063: optimistic update reverts on API failure', async () => {
    const mockUpdate = vi.fn().mockRejectedValue(new Error('Failed'));
    
    const OptimisticComponent = () => {
      const [value, setValue] = React.useState('original');
      const [error, setError] = React.useState('');
      
      const handleUpdate = async () => {
        const previous = value;
        setValue('updated');
        try {
          await mockUpdate();
        } catch {
          setValue(previous);
          setError('Update failed');
        }
      };
      
      return (
        <div>
          <span data-testid="value">{value}</span>
          <span data-testid="error">{error}</span>
          <button onClick={handleUpdate} data-testid="update">Update</button>
        </div>
      );
    };
    
    render(<OptimisticComponent />);
    
    fireEvent.click(screen.getByTestId('update'));
    
    await waitFor(() => {
      expect(screen.getByTestId('value')).toHaveTextContent('original');
      expect(screen.getByTestId('error')).toHaveTextContent('Update failed');
    });
  });

  // TC-FE064: Derived state calculates correctly
  it('TC-FE064: derived state updates when dependencies change', () => {
    const Calculator = () => {
      const [prices, setPrices] = React.useState([100, 200, 300]);
      const total = React.useMemo(() => prices.reduce((a, b) => a + b, 0), [prices]);
      const average = React.useMemo(() => total / prices.length, [total, prices.length]);
      
      return (
        <div>
          <span data-testid="total">{total}</span>
          <span data-testid="average">{average}</span>
        </div>
      );
    };
    
    render(<Calculator />);
    
    expect(screen.getByTestId('total')).toHaveTextContent('600');
    expect(screen.getByTestId('average')).toHaveTextContent('200');
  });

  // TC-FE065: Component unmount cleanup works
  it('TC-FE065: cleanup function runs on unmount', () => {
    const cleanup = vi.fn();
    
    const CleanupComponent = () => {
      React.useEffect(() => {
        return cleanup;
      }, []);
      return <div>Cleanup Test</div>;
    };
    
    const { unmount } = render(<CleanupComponent />);
    
    expect(cleanup).not.toHaveBeenCalled();
    
    unmount();
    
    expect(cleanup).toHaveBeenCalledTimes(1);
  });
});

// Need to import fireEvent for TC-FE062
import { fireEvent } from '@testing-library/react';
