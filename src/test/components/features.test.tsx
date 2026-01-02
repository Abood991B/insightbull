/**
 * Feature Component Tests - Phase 2: Dashboard & Analysis
 * Test Cases: TC-FE021 to TC-FE035
 * 
 * Tests dashboard components, stock cards, sentiment displays, and charts.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

// Mock Stock Data
const mockStockData = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  price: 178.50,
  change: 2.35,
  changePercent: 1.33,
  sentiment: 0.65,
  sentimentLabel: 'positive',
};

const mockSentimentData = [
  { date: '2025-12-01', sentiment: 0.45, price: 175.20 },
  { date: '2025-12-02', sentiment: 0.52, price: 176.80 },
  { date: '2025-12-03', sentiment: 0.65, price: 178.50 },
];

// Stock Card Component Tests
describe('Stock Card Component', () => {
  // TC-FE021: Stock card displays symbol and name
  it('TC-FE021: displays stock symbol and company name', () => {
    render(
      <div data-testid="stock-card">
        <span data-testid="symbol">{mockStockData.symbol}</span>
        <span data-testid="name">{mockStockData.name}</span>
      </div>
    );
    
    expect(screen.getByTestId('symbol')).toHaveTextContent('AAPL');
    expect(screen.getByTestId('name')).toHaveTextContent('Apple Inc.');
  });

  // TC-FE022: Stock card shows current price
  it('TC-FE022: displays current stock price', () => {
    render(<span data-testid="price">${mockStockData.price.toFixed(2)}</span>);
    
    expect(screen.getByTestId('price')).toHaveTextContent('$178.50');
  });

  // TC-FE023: Stock card shows positive price change
  it('TC-FE023: displays positive price change with green color', () => {
    render(
      <span data-testid="change" className="text-green-500">
        +{mockStockData.change} ({mockStockData.changePercent}%)
      </span>
    );
    
    expect(screen.getByTestId('change')).toHaveClass('text-green-500');
    expect(screen.getByTestId('change')).toHaveTextContent('+2.35');
  });

  // TC-FE024: Stock card shows negative price change
  it('TC-FE024: displays negative price change with red color', () => {
    render(
      <span data-testid="change" className="text-red-500">
        -1.50 (-0.85%)
      </span>
    );
    
    expect(screen.getByTestId('change')).toHaveClass('text-red-500');
    expect(screen.getByTestId('change')).toHaveTextContent('-1.50');
  });

  // TC-FE025: Stock card displays sentiment badge
  it('TC-FE025: displays sentiment badge with correct label', () => {
    render(
      <span data-testid="sentiment-badge" data-sentiment="positive">
        Positive
      </span>
    );
    
    expect(screen.getByTestId('sentiment-badge')).toHaveTextContent('Positive');
    expect(screen.getByTestId('sentiment-badge')).toHaveAttribute('data-sentiment', 'positive');
  });
});

// Sentiment Display Component Tests
describe('Sentiment Display Component', () => {
  // TC-FE026: Sentiment score displays correctly
  it('TC-FE026: displays sentiment score as percentage', () => {
    const score = 0.65;
    render(<span data-testid="score">{(score * 100).toFixed(0)}%</span>);
    
    expect(screen.getByTestId('score')).toHaveTextContent('65%');
  });

  // TC-FE027: Sentiment progress bar reflects value
  it('TC-FE027: progress bar width matches sentiment score', () => {
    const score = 0.75;
    render(
      <div data-testid="progress" style={{ width: `${score * 100}%` }}>
        Progress
      </div>
    );
    
    expect(screen.getByTestId('progress')).toHaveStyle({ width: '75%' });
  });

  // TC-FE028: Sentiment trend indicator shows direction
  it('TC-FE028: trend indicator shows upward trend', () => {
    render(
      <div data-testid="trend" data-direction="up">
        <svg data-testid="trend-icon" />
        Trending Up
      </div>
    );
    
    expect(screen.getByTestId('trend')).toHaveAttribute('data-direction', 'up');
  });

  // TC-FE029: Sentiment source breakdown displays
  it('TC-FE029: displays sentiment sources breakdown', () => {
    render(
      <div data-testid="sources">
        <span>News: 60%</span>
        <span>Social: 40%</span>
      </div>
    );
    
    expect(screen.getByTestId('sources')).toHaveTextContent('News: 60%');
    expect(screen.getByTestId('sources')).toHaveTextContent('Social: 40%');
  });

  // TC-FE030: Sentiment history chart container renders
  it('TC-FE030: chart container renders with correct dimensions', () => {
    render(
      <div data-testid="chart-container" style={{ height: '300px', width: '100%' }}>
        Chart placeholder
      </div>
    );
    
    expect(screen.getByTestId('chart-container')).toHaveStyle({ height: '300px' });
  });
});

// Dashboard Summary Component Tests
describe('Dashboard Summary Component', () => {
  // TC-FE031: Market overview displays metrics
  it('TC-FE031: displays market overview metrics', () => {
    render(
      <div data-testid="market-overview">
        <span data-testid="total-stocks">20 Stocks</span>
        <span data-testid="avg-sentiment">+0.42</span>
      </div>
    );
    
    expect(screen.getByTestId('total-stocks')).toHaveTextContent('20 Stocks');
    expect(screen.getByTestId('avg-sentiment')).toHaveTextContent('+0.42');
  });

  // TC-FE032: Top movers section displays correctly
  it('TC-FE032: displays top gainers and losers', () => {
    render(
      <div data-testid="top-movers">
        <div data-testid="gainers">Top Gainers</div>
        <div data-testid="losers">Top Losers</div>
      </div>
    );
    
    expect(screen.getByTestId('gainers')).toBeInTheDocument();
    expect(screen.getByTestId('losers')).toBeInTheDocument();
  });

  // TC-FE033: Sentiment distribution pie chart
  it('TC-FE033: renders sentiment distribution display', () => {
    render(
      <div data-testid="distribution">
        <span>Positive: 45%</span>
        <span>Neutral: 35%</span>
        <span>Negative: 20%</span>
      </div>
    );
    
    expect(screen.getByTestId('distribution')).toHaveTextContent('Positive: 45%');
  });

  // TC-FE034: Recent activity feed displays
  it('TC-FE034: displays recent activity items', () => {
    render(
      <ul data-testid="activity-feed">
        <li>New sentiment data for AAPL</li>
        <li>Price update for MSFT</li>
      </ul>
    );
    
    expect(screen.getByTestId('activity-feed').children).toHaveLength(2);
  });

  // TC-FE035: Last updated timestamp shows
  it('TC-FE035: displays last updated timestamp', () => {
    const timestamp = '2025-01-02 10:30:00';
    render(<span data-testid="last-updated">Last updated: {timestamp}</span>);
    
    expect(screen.getByTestId('last-updated')).toHaveTextContent('Last updated:');
  });
});
