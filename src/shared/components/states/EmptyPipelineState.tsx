import { PlayCircle, Database, Info } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Card } from '@/shared/components/ui/card';
import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Link } from 'react-router-dom';

/**
 * Empty Pipeline State Component
 * 
 * CRITICAL: Display when backend has no sentiment data (pipeline not run yet)
 * This is the MOST IMPORTANT empty state as the database starts empty.
 * 
 * Usage:
 * - Dashboard when no stocks have data
 * - All analysis pages when no sentiment data exists
 * - Any page requiring sentiment analysis results
 */
export function EmptyPipelineState() {
  return (
    <Card className="max-w-2xl mx-auto mt-12 p-8">
      <div className="text-center">
        <Database className="w-20 h-20 text-blue-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          No Data Collected Yet
        </h2>
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          The sentiment analysis pipeline hasn't run yet. 
          Start data collection to populate the dashboard with 
          real-time sentiment analysis from Reddit, FinHub, NewsAPI, and Marketaux.
        </p>
        
        <div className="flex justify-center gap-4 mb-6">
          <Button asChild size="lg">
            <Link to="/admin/dashboard">
              <PlayCircle className="mr-2 h-4 w-4" />
              Run Data Collection
            </Link>
          </Button>
          <Button variant="outline" asChild size="lg">
            <Link to="/about">Learn More</Link>
          </Button>
        </div>
        
        <Alert className="bg-blue-50 border-blue-200">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <strong>Admin Access Required:</strong> Data collection requires 
            OAuth2 + TOTP authentication. The pipeline takes 5-10 minutes to complete.
          </AlertDescription>
        </Alert>
      </div>
    </Card>
  );
}
