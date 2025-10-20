import { TrendingUp } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';

interface InsufficientCorrelationDataProps {
  currentPoints: number;
  requiredPoints?: number;
}

/**
 * Insufficient Correlation Data Component
 * 
 * Display when correlation analysis cannot be performed due to insufficient data
 * Requires minimum 3 data points for basic statistical analysis
 * 
 * Usage:
 * - Correlation Analysis page with < 3 data points
 * - Scatter plots without enough samples
 * - Statistical significance calculations
 */
export function InsufficientCorrelationData({ 
  currentPoints, 
  requiredPoints = 3 
}: InsufficientCorrelationDataProps) {
  return (
    <Alert variant="destructive">
      <TrendingUp className="h-4 w-4" />
      <AlertTitle>Insufficient Data for Correlation Analysis</AlertTitle>
      <AlertDescription>
        <p className="mb-3">
          At least <strong>{requiredPoints} data points</strong> are needed for meaningful 
          statistical correlation analysis. Currently have <strong>{currentPoints} points</strong>.
        </p>
        <div className="space-y-1 text-sm">
          <p className="font-semibold">Suggestions:</p>
          <ul className="ml-4 list-disc space-y-1">
            <li>Wait for more pipeline runs to collect additional data</li>
            <li>Try selecting a longer time range (14 days instead of 1 day)</li>
            <li>Ensure the stock is in the active watchlist</li>
            <li>Check that data collection is running successfully</li>
          </ul>
        </div>
        <p className="text-xs mt-3 opacity-80">
          Note: Even with sufficient data points, correlation may not be statistically 
          significant (p-value &gt; 0.05) if there's no clear relationship.
        </p>
      </AlertDescription>
    </Alert>
  );
}
