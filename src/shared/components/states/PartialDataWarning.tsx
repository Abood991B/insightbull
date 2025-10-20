import { Clock } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Progress } from '@/shared/components/ui/progress';

interface PartialDataWarningProps {
  dataPoints: number;
  minRequired: number;
  dataQuality?: number;
  message?: string;
}

/**
 * Partial Data Warning Component
 * 
 * Display when some data exists but not enough for optimal analysis
 * Still allows rendering with available data, but warns user
 * 
 * Usage:
 * - Charts with < 5 data points
 * - Analysis pages with limited historical data
 * - Any feature that works with partial data but is better with more
 */
export function PartialDataWarning({ 
  dataPoints, 
  minRequired, 
  dataQuality,
  message 
}: PartialDataWarningProps) {
  const percentage = Math.min((dataPoints / minRequired) * 100, 100);
  
  return (
    <Alert className="mb-4 border-yellow-200 bg-yellow-50">
      <Clock className="h-4 w-4 text-yellow-600" />
      <AlertTitle>Limited Data Available</AlertTitle>
      <AlertDescription>
        <div className="space-y-2">
          <p>
            {message || `Only ${dataPoints} of ${minRequired} recommended data points available. 
            Results may be less accurate with limited data.`}
          </p>
          <Progress value={percentage} className="h-2" />
          {dataQuality && (
            <p className="text-xs">
              Data Coverage: <strong>{dataQuality.toFixed(0)}%</strong>
            </p>
          )}
          <p className="text-xs mt-2">
            💡 <strong>Tip:</strong> Try a shorter time range or wait for the next pipeline run 
            to collect more data points.
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );
}
