/**
 * Hook and Utility Tests - Phase 3
 * Test Cases: TC-FE036 to TC-FE050
 * 
 * Tests custom React hooks and utility functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import * as React from 'react';

// Mock utility functions for testing
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
};

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(2)}%`;
};

const formatDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString('en-US');
};

const calculateSentimentColor = (score: number): string => {
  if (score > 0.1) return 'green';
  if (score < -0.1) return 'red';
  return 'gray';
};

const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

const debounce = <T extends (...args: any[]) => any>(fn: T, delay: number) => {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

const validateStockSymbol = (symbol: string): boolean => {
  return /^[A-Z]{1,5}$/.test(symbol);
};

const calculateCorrelation = (x: number[], y: number[]): number => {
  if (x.length !== y.length || x.length < 2) return 0;
  
  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
  const sumX2 = x.reduce((acc, xi) => acc + xi * xi, 0);
  const sumY2 = y.reduce((acc, yi) => acc + yi * yi, 0);
  
  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumX2 - sumX ** 2) * (n * sumY2 - sumY ** 2));
  
  return denominator === 0 ? 0 : numerator / denominator;
};

// Utility Function Tests
describe('Utility Functions', () => {
  // TC-FE036: formatCurrency formats USD correctly
  it('TC-FE036: formatCurrency formats USD values correctly', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency(-50.25)).toBe('-$50.25');
  });

  // TC-FE037: formatPercentage converts decimal to percentage
  it('TC-FE037: formatPercentage converts decimals correctly', () => {
    expect(formatPercentage(0.1234)).toBe('12.34%');
    expect(formatPercentage(1)).toBe('100.00%');
    expect(formatPercentage(-0.05)).toBe('-5.00%');
  });

  // TC-FE038: formatDate handles various date formats
  it('TC-FE038: formatDate parses and formats dates', () => {
    expect(formatDate('2025-01-02')).toBe('1/2/2025');
    expect(formatDate(new Date('2025-12-25'))).toBe('12/25/2025');
  });

  // TC-FE039: calculateSentimentColor returns correct colors
  it('TC-FE039: calculateSentimentColor maps scores to colors', () => {
    expect(calculateSentimentColor(0.5)).toBe('green');
    expect(calculateSentimentColor(-0.5)).toBe('red');
    expect(calculateSentimentColor(0)).toBe('gray');
    expect(calculateSentimentColor(0.05)).toBe('gray');
  });

  // TC-FE040: truncateText handles long strings
  it('TC-FE040: truncateText shortens text with ellipsis', () => {
    expect(truncateText('Short', 10)).toBe('Short');
    expect(truncateText('This is a very long text', 10)).toBe('This is a ...');
    expect(truncateText('', 5)).toBe('');
  });

  // TC-FE041: validateStockSymbol validates format
  it('TC-FE041: validateStockSymbol checks symbol format', () => {
    expect(validateStockSymbol('AAPL')).toBe(true);
    expect(validateStockSymbol('A')).toBe(true);
    expect(validateStockSymbol('GOOGL')).toBe(true);
    expect(validateStockSymbol('aapl')).toBe(false);
    expect(validateStockSymbol('TOOLONG')).toBe(false);
    expect(validateStockSymbol('AA1')).toBe(false);
  });

  // TC-FE042: calculateCorrelation computes Pearson r
  it('TC-FE042: calculateCorrelation computes correct value', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [2, 4, 6, 8, 10];
    expect(calculateCorrelation(x, y)).toBeCloseTo(1, 5);
    
    const x2 = [1, 2, 3, 4, 5];
    const y2 = [5, 4, 3, 2, 1];
    expect(calculateCorrelation(x2, y2)).toBeCloseTo(-1, 5);
  });
});

// Custom Hook Mock Tests
describe('Custom Hooks', () => {
  // TC-FE043: useLocalStorage hook
  it('TC-FE043: useLocalStorage stores and retrieves values', () => {
    const useLocalStorage = <T,>(key: string, initialValue: T) => {
      const [storedValue, setStoredValue] = React.useState<T>(() => {
        try {
          const item = window.localStorage.getItem(key);
          return item ? JSON.parse(item) : initialValue;
        } catch {
          return initialValue;
        }
      });
      
      const setValue = (value: T) => {
        setStoredValue(value);
        window.localStorage.setItem(key, JSON.stringify(value));
      };
      
      return [storedValue, setValue] as const;
    };
    
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));
    
    expect(result.current[0]).toBe('initial');
    
    act(() => {
      result.current[1]('updated');
    });
    
    expect(result.current[0]).toBe('updated');
  });

  // TC-FE044: useDebounce hook
  it('TC-FE044: useDebounce delays value updates', async () => {
    vi.useFakeTimers();
    
    const useDebounce = <T,>(value: T, delay: number): T => {
      const [debouncedValue, setDebouncedValue] = React.useState(value);
      
      React.useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
      }, [value, delay]);
      
      return debouncedValue;
    };
    
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );
    
    expect(result.current).toBe('initial');
    
    rerender({ value: 'updated', delay: 500 });
    expect(result.current).toBe('initial');
    
    await act(async () => {
      vi.advanceTimersByTime(500);
    });
    
    expect(result.current).toBe('updated');
    vi.useRealTimers();
  });

  // TC-FE045: useToggle hook
  it('TC-FE045: useToggle toggles boolean state', () => {
    const useToggle = (initial = false) => {
      const [value, setValue] = React.useState(initial);
      const toggle = React.useCallback(() => setValue(v => !v), []);
      return [value, toggle] as const;
    };
    
    const { result } = renderHook(() => useToggle(false));
    
    expect(result.current[0]).toBe(false);
    
    act(() => {
      result.current[1]();
    });
    
    expect(result.current[0]).toBe(true);
  });

  // TC-FE046: usePrevious hook
  it('TC-FE046: usePrevious tracks previous value', () => {
    const usePrevious = <T,>(value: T): T | undefined => {
      const ref = React.useRef<T>();
      React.useEffect(() => {
        ref.current = value;
      });
      return ref.current;
    };
    
    const { result, rerender } = renderHook(
      ({ value }) => usePrevious(value),
      { initialProps: { value: 0 } }
    );
    
    expect(result.current).toBe(undefined);
    
    rerender({ value: 1 });
    expect(result.current).toBe(0);
    
    rerender({ value: 2 });
    expect(result.current).toBe(1);
  });

  // TC-FE047: useWindowSize hook
  it('TC-FE047: useWindowSize tracks window dimensions', () => {
    const useWindowSize = () => {
      const [size, setSize] = React.useState({
        width: window.innerWidth,
        height: window.innerHeight,
      });
      
      React.useEffect(() => {
        const handleResize = () => {
          setSize({ width: window.innerWidth, height: window.innerHeight });
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
      }, []);
      
      return size;
    };
    
    const { result } = renderHook(() => useWindowSize());
    
    expect(result.current).toHaveProperty('width');
    expect(result.current).toHaveProperty('height');
  });

  // TC-FE048: useInterval hook
  it('TC-FE048: useInterval calls callback repeatedly', () => {
    vi.useFakeTimers();
    const callback = vi.fn();
    
    const useInterval = (callback: () => void, delay: number | null) => {
      const savedCallback = React.useRef(callback);
      
      React.useEffect(() => {
        savedCallback.current = callback;
      }, [callback]);
      
      React.useEffect(() => {
        if (delay === null) return;
        const id = setInterval(() => savedCallback.current(), delay);
        return () => clearInterval(id);
      }, [delay]);
    };
    
    renderHook(() => useInterval(callback, 1000));
    
    expect(callback).not.toHaveBeenCalled();
    
    act(() => {
      vi.advanceTimersByTime(3000);
    });
    
    expect(callback).toHaveBeenCalledTimes(3);
    vi.useRealTimers();
  });

  // TC-FE049: useOnClickOutside hook
  it('TC-FE049: useOnClickOutside detects outside clicks', () => {
    const handler = vi.fn();
    
    const useOnClickOutside = (
      ref: React.RefObject<HTMLElement>,
      handler: () => void
    ) => {
      React.useEffect(() => {
        const listener = (event: MouseEvent) => {
          if (!ref.current || ref.current.contains(event.target as Node)) return;
          handler();
        };
        document.addEventListener('mousedown', listener);
        return () => document.removeEventListener('mousedown', listener);
      }, [ref, handler]);
    };
    
    const ref = { current: document.createElement('div') };
    renderHook(() => useOnClickOutside(ref, handler));
    
    // Simulate outside click
    const event = new MouseEvent('mousedown', { bubbles: true });
    document.dispatchEvent(event);
    
    expect(handler).toHaveBeenCalled();
  });

  // TC-FE050: useAsync hook
  it('TC-FE050: useAsync manages async state', async () => {
    const useAsync = <T,>(asyncFn: () => Promise<T>) => {
      const [state, setState] = React.useState<{
        loading: boolean;
        error: Error | null;
        data: T | null;
      }>({ loading: true, error: null, data: null });
      
      React.useEffect(() => {
        asyncFn()
          .then(data => setState({ loading: false, error: null, data }))
          .catch(error => setState({ loading: false, error, data: null }));
      }, []);
      
      return state;
    };
    
    const mockAsync = () => Promise.resolve({ success: true });
    
    const { result } = renderHook(() => useAsync(mockAsync));
    
    expect(result.current.loading).toBe(true);
    
    await act(async () => {
      await Promise.resolve();
    });
    
    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual({ success: true });
  });
});
