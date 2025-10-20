import { ListPlus } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Link } from 'react-router-dom';

/**
 * Empty Watchlist State Component
 * 
 * Display when the watchlist has no stocks added
 * 
 * Usage:
 * - Stock selection dropdowns when watchlist is empty
 * - Analysis pages that require stock selection
 * - Any feature dependent on tracked stocks
 */
export function EmptyWatchlistState() {
  return (
    <Alert className="max-w-2xl mx-auto border-orange-200 bg-orange-50">
      <ListPlus className="h-5 w-5 text-orange-600" />
      <AlertTitle className="text-lg text-orange-900">
        No Stocks in Watchlist
      </AlertTitle>
      <AlertDescription className="mt-2 text-orange-800">
        <p className="mb-3">
          Add stocks to the watchlist to start tracking sentiment. 
          The dashboard supports Top 20 IXT Technology stocks including:
        </p>
        <div className="mb-4 text-sm">
          <strong>Magnificent Seven:</strong> AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA
          <br />
          <strong>Plus:</strong> INTC, CSCO, AMD, AVGO, ORCL, PLTR, IBM, CRM, INTU, and more
        </div>
        <Button asChild>
          <Link to="/admin/watchlist">
            <ListPlus className="mr-2 h-4 w-4" />
            Manage Watchlist
          </Link>
        </Button>
      </AlertDescription>
    </Alert>
  );
}
