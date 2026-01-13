import * as React from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/shared/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { cn } from "@/shared/utils/utils";

/**
 * Financial terminology definitions for user education.
 * These tooltips help non-financial users understand key metrics.
 */
export const FINANCIAL_TERMS = {
  // High Priority: Core Metrics
  sentimentScore: {
    term: "Sentiment Score",
    definition: "A numerical measure of market sentiment ranging from -1.0 (extremely negative/bearish) to +1.0 (extremely positive/bullish). Scores near 0 indicate neutral sentiment. Derived from AI analysis of news articles and social media.",
  },
  averageSentiment: {
    term: "Average Sentiment",
    definition: "The mean sentiment score across all analyzed content for a stock or market. Calculated by averaging individual sentiment scores from news and social media analysis.",
  },
  marketCap: {
    term: "Market Cap",
    definition: "Market Capitalization - the total market value of a company's outstanding shares. Calculated as: Stock Price × Total Shares Outstanding. Used to measure company size (e.g., $1T = trillion, $1B = billion).",
  },
  correlation: {
    term: "Correlation (r)",
    definition: "Pearson correlation coefficient measuring the linear relationship between sentiment and price. Ranges from -1 to +1. Values near ±1 indicate strong correlation, near 0 means weak/no correlation. Positive values mean both move together; negative means they move opposite.",
  },
  rSquared: {
    term: "R² (R-Squared)",
    definition: "Coefficient of determination - the percentage of price variance explained by sentiment. For example, R² = 25% means sentiment explains 25% of price movements. Higher values indicate sentiment is a better predictor.",
  },
  pValue: {
    term: "P-Value",
    definition: "Statistical significance measure. P < 0.05 means the correlation is statistically significant (less than 5% chance it's random). P > 0.05 suggests the result may be due to chance rather than a real relationship.",
  },

  // Medium Priority: Industry-Specific
  volatility: {
    term: "Volatility",
    definition: "A measure of how much sentiment scores vary over time. High volatility indicates unstable, rapidly changing sentiment. Low volatility suggests consistent, stable market perception. Measured as standard deviation.",
  },
  momentum: {
    term: "Momentum",
    definition: "The strength and direction of a sentiment trend. Strong momentum indicates a clear directional bias (bullish or bearish). Weak momentum suggests mixed or uncertain market sentiment.",
  },
  bullish: {
    term: "Bullish",
    definition: "Positive market outlook - investors expect prices to rise. In sentiment analysis, bullish indicates predominantly positive news and social media content about a stock.",
  },
  bearish: {
    term: "Bearish",
    definition: "Negative market outlook - investors expect prices to fall. In sentiment analysis, bearish indicates predominantly negative news and social media content about a stock.",
  },
  sampleSize: {
    term: "Sample Size",
    definition: "The number of data points used in analysis. Larger sample sizes (30+) provide more reliable statistical results. Smaller samples may produce less accurate or unstable conclusions.",
  },
  confidenceInterval: {
    term: "Confidence Interval (CI)",
    definition: "A range of values within which the true correlation likely falls. A 95% CI means we're 95% confident the actual correlation is within this range. Narrower intervals indicate more precise estimates.",
  },

  // Additional Terms
  priceChange: {
    term: "Price Change (24h)",
    definition: "The percentage change in stock price over the last 24 hours. Positive values (green) indicate price increase; negative values (red) indicate decrease.",
  },
  dataPoints: {
    term: "Data Points",
    definition: "The total number of sentiment records analyzed. Each data point represents one analyzed news article or social media post. More data points generally lead to more reliable sentiment scores.",
  },
  dataCoverage: {
    term: "Data Coverage",
    definition: "The percentage of the selected time period that has sentiment data available. 100% means data exists for every time bucket in the range. Lower coverage may indicate gaps in data collection.",
  },
  sentimentDistribution: {
    term: "Sentiment Distribution",
    definition: "The breakdown of analyzed content into positive, neutral, and negative categories. Shows what proportion of news and social media was favorable, unfavorable, or neutral about a stock.",
  },
  standardDeviation: {
    term: "Standard Deviation (Std Dev)",
    definition: "A statistical measure of how spread out the sentiment scores are from the average. Higher values indicate more variation in sentiment; lower values mean sentiment is more consistent.",
  },
  timeframe: {
    term: "Timeframe",
    definition: "The period of historical data being analyzed. Options include 1D (last 24 hours), 7D (last week), 14D (last two weeks), and 30D (last month). Longer timeframes provide more context but may include outdated trends.",
  },
  watchlist: {
    term: "Watchlist",
    definition: "A curated list of stocks being monitored for sentiment analysis. The dashboard tracks the top 20 technology stocks including major companies like Apple, Microsoft, NVIDIA, and others.",
  },
  pipelineStatus: {
    term: "Pipeline Status",
    definition: "The operational state of the data collection system. 'Operational' means data is being collected normally. 'Delayed' or 'Stale' indicates potential issues with data freshness.",
  },
  sentimentTimeline: {
    term: "Sentiment Timeline",
    definition: "A chronological chart showing how sentiment scores change over time. Useful for identifying trends, sudden shifts in market perception, or correlating sentiment with news events.",
  },
  dailyImpact: {
    term: "Daily Impact",
    definition: "Analysis comparing daily sentiment averages with corresponding daily price changes. Helps identify whether positive/negative sentiment aligns with price movements on a day-by-day basis.",
  },
} as const;

type TermKey = keyof typeof FINANCIAL_TERMS;

interface TermTooltipProps {
  /** The term key from FINANCIAL_TERMS */
  term: TermKey;
  /** Optional: Custom display text (defaults to the term name) */
  children?: React.ReactNode;
  /** Show help icon indicator */
  showIcon?: boolean;
  /** Additional CSS classes for the trigger */
  className?: string;
  /** Whether to show underline decoration */
  underline?: boolean;
}

/**
 * TermTooltip - A reusable tooltip component for explaining financial terminology.
 * 
 * Usage:
 * ```tsx
 * <TermTooltip term="sentimentScore">Sentiment Score</TermTooltip>
 * <TermTooltip term="marketCap" showIcon />
 * <TermTooltip term="correlation" underline>r value</TermTooltip>
 * ```
 */
export const TermTooltip = ({
  term,
  children,
  showIcon = false,
  className,
  underline = false,
}: TermTooltipProps) => {
  const termData = FINANCIAL_TERMS[term];

  if (!termData) {
    console.warn(`TermTooltip: Unknown term "${term}"`);
    return <>{children}</>;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "cursor-help inline-flex items-center gap-1",
              underline && "border-b border-dashed border-current",
              className
            )}
          >
            {children || termData.term}
            {showIcon && (
              <HelpCircle className="h-3.5 w-3.5 text-muted-foreground opacity-70" />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="center"
          className="max-w-xs text-sm leading-relaxed"
        >
          <span className="font-semibold block mb-1">{termData.term}</span>
          <span className="text-muted-foreground block">{termData.definition}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

/**
 * InfoTooltip - A simpler tooltip with just an icon trigger.
 * Useful for adding help icons next to labels.
 * 
 * Usage:
 * ```tsx
 * <span>Market Cap <InfoTooltip term="marketCap" /></span>
 * ```
 */
export const InfoTooltip = ({
  term,
  className,
}: {
  term: TermKey;
  className?: string;
}) => {
  const termData = FINANCIAL_TERMS[term];

  if (!termData) {
    return null;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <HelpCircle
            className={cn(
              "h-3.5 w-3.5 text-muted-foreground opacity-70 cursor-help inline-block ml-1",
              className
            )}
          />
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="center"
          className="max-w-xs text-sm leading-relaxed"
        >
          <span className="font-semibold block mb-1">{termData.term}</span>
          <span className="text-muted-foreground block">{termData.definition}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default TermTooltip;
