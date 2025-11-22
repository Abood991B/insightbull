import { useEffect, useState } from 'react';
import { Clock, TrendingUp, Moon, Sun, Sunrise } from 'lucide-react';
import { Badge } from '@/shared/components/ui/badge';

interface MarketCountdownProps {
  className?: string;
  variant?: 'compact' | 'detailed' | 'card';
}

type MarketPhase = 'closed' | 'pre-market' | 'market-open' | 'after-hours' | 'weekend';

interface MarketStatus {
  phase: MarketPhase;
  phaseLabel: string;
  countdown: string;
  nextPhase: string;
  nextPhaseTime: string;
  currentTime: string;
  isWeekend: boolean;
  progress?: number; // 0-100 for current phase progress
}

export const MarketCountdown = ({ 
  className = '', 
  variant = 'detailed' 
}: MarketCountdownProps) => {
  const [status, setStatus] = useState<MarketStatus>({
    phase: 'closed',
    phaseLabel: 'Calculating...',
    countdown: '',
    nextPhase: '',
    nextPhaseTime: '',
    currentTime: '',
    isWeekend: false
  });

  useEffect(() => {
    const updateMarketStatus = () => {
      const now = new Date();
      
      // Get ET time
      const etOptions: Intl.DateTimeFormatOptions = {
        timeZone: 'America/New_York',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      };

      const etParts = new Intl.DateTimeFormat('en-US', etOptions).formatToParts(now);
      const etTime = {
        year: parseInt(etParts.find(p => p.type === 'year')?.value || '0'),
        month: parseInt(etParts.find(p => p.type === 'month')?.value || '0') - 1,
        day: parseInt(etParts.find(p => p.type === 'day')?.value || '0'),
        hour: parseInt(etParts.find(p => p.type === 'hour')?.value || '0'),
        minute: parseInt(etParts.find(p => p.type === 'minute')?.value || '0'),
        second: parseInt(etParts.find(p => p.type === 'second')?.value || '0')
      };

      const etDate = new Date(etTime.year, etTime.month, etTime.day, etTime.hour, etTime.minute, etTime.second);
      const day = etDate.getDay();
      const totalMinutes = etTime.hour * 60 + etTime.minute;

      // Format current time in user's local timezone
      const userTime = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
      const currentTime = userTime;

      // Helper to convert ET time to user's local time using browser's dynamic timezone API
      const formatLocalTime = (etHour: number, etMinute: number = 0) => {
        // Create a date in ET timezone for the target time
        // We'll use the current ET date and set the specific hour/minute
        const etDateForTarget = new Date(Date.UTC(etTime.year, etTime.month, etTime.day, etHour, etMinute, 0));
        
        // Format this date as if it's in ET timezone to get the actual local date/time
        const etFormatter = new Intl.DateTimeFormat('en-US', {
          timeZone: 'America/New_York',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
        
        // Try UTC offsets to find the correct one
        const offsets = [0, 4, 5]; // UTC, EDT (UTC-4), EST (UTC-5)
        
        for (const offset of offsets) {
          const testDate = new Date(Date.UTC(etTime.year, etTime.month, etTime.day, etHour + offset, etMinute, 0));
          const formatted = etFormatter.formatToParts(testDate);
          
          const testHour = parseInt(formatted.find(p => p.type === 'hour')?.value || '0');
          const testMinute = parseInt(formatted.find(p => p.type === 'minute')?.value || '0');
          
          if (testHour === etHour && testMinute === etMinute) {
            // Found correct UTC time - convert to user's local timezone
            return testDate.toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true
            });
          }
        }
        
        // Fallback - shouldn't reach here
        return `${etHour}:${String(etMinute).padStart(2, '0')}`;
      };

      // Market hours (in minutes from midnight)
      const PRE_MARKET_START = 4 * 60; // 4:00 AM
      const MARKET_OPEN = 9 * 60 + 30; // 9:30 AM
      const MARKET_CLOSE = 16 * 60; // 4:00 PM
      const AFTER_HOURS_END = 20 * 60; // 8:00 PM

      const isWeekend = day === 0 || day === 6;
      
      let newStatus: MarketStatus = {
        phase: 'closed',
        phaseLabel: 'Market Closed',
        countdown: '',
        nextPhase: '',
        nextPhaseTime: '',
        currentTime,
        isWeekend
      };

      if (isWeekend) {
        // Weekend - calculate time until Monday pre-market
        const daysUntilMonday = day === 0 ? 1 : 2;
        const mondayPreMarket = new Date(
          etTime.year,
          etTime.month,
          etTime.day + daysUntilMonday,
          4, 0, 0
        );
        
        const diff = mondayPreMarket.getTime() - etDate.getTime();
        const countdown = formatCountdown(diff);

        const mondayLocalTime = formatLocalTime(4, 0);
        newStatus = {
          phase: 'weekend',
          phaseLabel: 'Weekend',
          countdown,
          nextPhase: 'Pre-Market Opens',
          nextPhaseTime: `Monday ${mondayLocalTime}`,
          currentTime,
          isWeekend: true
        };
      } else if (totalMinutes >= PRE_MARKET_START && totalMinutes < MARKET_OPEN) {
        // Pre-market phase
        const marketOpen = new Date(etTime.year, etTime.month, etTime.day, 9, 30, 0);
        const diff = marketOpen.getTime() - etDate.getTime();
        const countdown = formatCountdown(diff);
        
        const progress = ((totalMinutes - PRE_MARKET_START) / (MARKET_OPEN - PRE_MARKET_START)) * 100;

        const marketOpenLocalTime = formatLocalTime(9, 30);
        newStatus = {
          phase: 'pre-market',
          phaseLabel: 'Pre-Market',
          countdown,
          nextPhase: 'Market Opens',
          nextPhaseTime: marketOpenLocalTime,
          currentTime,
          isWeekend: false,
          progress
        };
      } else if (totalMinutes >= MARKET_OPEN && totalMinutes < MARKET_CLOSE) {
        // Regular market hours
        const marketClose = new Date(etTime.year, etTime.month, etTime.day, 16, 0, 0);
        const diff = marketClose.getTime() - etDate.getTime();
        const countdown = formatCountdown(diff);
        
        const progress = ((totalMinutes - MARKET_OPEN) / (MARKET_CLOSE - MARKET_OPEN)) * 100;

        const marketCloseLocalTime = formatLocalTime(16, 0);
        newStatus = {
          phase: 'market-open',
          phaseLabel: 'Market Open',
          countdown,
          nextPhase: 'Market Closes',
          nextPhaseTime: marketCloseLocalTime,
          currentTime,
          isWeekend: false,
          progress
        };
      } else if (totalMinutes >= MARKET_CLOSE && totalMinutes < AFTER_HOURS_END) {
        // After-hours trading
        const afterHoursEnd = new Date(etTime.year, etTime.month, etTime.day, 20, 0, 0);
        const diff = afterHoursEnd.getTime() - etDate.getTime();
        const countdown = formatCountdown(diff);
        
        const progress = ((totalMinutes - MARKET_CLOSE) / (AFTER_HOURS_END - MARKET_CLOSE)) * 100;

        const afterHoursEndLocalTime = formatLocalTime(20, 0);
        newStatus = {
          phase: 'after-hours',
          phaseLabel: 'After-Hours',
          countdown,
          nextPhase: 'After-Hours Ends',
          nextPhaseTime: afterHoursEndLocalTime,
          currentTime,
          isWeekend: false,
          progress
        };
      } else {
        // Market closed - calculate next pre-market
        let daysToAdd = 0;
        let nextDay = 'Tomorrow';
        
        if (day === 5 && totalMinutes >= AFTER_HOURS_END) {
          // Friday after hours ended
          daysToAdd = 3;
          nextDay = 'Monday';
        } else if (totalMinutes >= AFTER_HOURS_END) {
          // Weekday after hours ended
          daysToAdd = 1;
          nextDay = 'Tomorrow';
        } else {
          // Before pre-market opens today
          daysToAdd = 0;
          nextDay = 'Today';
        }

        const nextPreMarket = new Date(
          etTime.year,
          etTime.month,
          etTime.day + daysToAdd,
          4, 0, 0
        );
        
        const diff = nextPreMarket.getTime() - etDate.getTime();
        const countdown = formatCountdown(diff);

        const preMarketLocalTime = formatLocalTime(4, 0);
        newStatus = {
          phase: 'closed',
          phaseLabel: 'Market Closed',
          countdown,
          nextPhase: 'Pre-Market Opens',
          nextPhaseTime: `${nextDay} ${preMarketLocalTime}`,
          currentTime,
          isWeekend: false
        };
      }

      setStatus(newStatus);
    };

    const formatCountdown = (milliseconds: number): string => {
      const totalSeconds = Math.floor(milliseconds / 1000);
      const days = Math.floor(totalSeconds / (24 * 60 * 60));
      const hours = Math.floor((totalSeconds % (24 * 60 * 60)) / (60 * 60));
      const minutes = Math.floor((totalSeconds % (60 * 60)) / 60);
      const seconds = totalSeconds % 60;

      if (days > 0) {
        return `${days}d ${hours}h ${minutes}m ${seconds}s`;
      } else if (hours > 0) {
        return `${hours}h ${minutes}m ${seconds}s`;
      } else if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
      } else {
        return `${seconds}s`;
      }
    };

    updateMarketStatus();
    const interval = setInterval(updateMarketStatus, 1000);

    return () => clearInterval(interval);
  }, []);

  const getPhaseIcon = () => {
    switch (status.phase) {
      case 'pre-market':
        return <Sunrise className="h-5 w-5" />;
      case 'market-open':
        return <Sun className="h-5 w-5" />;
      case 'after-hours':
        return <Moon className="h-5 w-5" />;
      case 'weekend':
      case 'closed':
        return <Clock className="h-5 w-5" />;
    }
  };

  const getPhaseColor = () => {
    switch (status.phase) {
      case 'pre-market':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'market-open':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'after-hours':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'weekend':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'closed':
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusDotColor = () => {
    switch (status.phase) {
      case 'pre-market':
        return 'bg-blue-500';
      case 'market-open':
        return 'bg-green-500';
      case 'after-hours':
        return 'bg-purple-500';
      case 'weekend':
        return 'bg-orange-500';
      case 'closed':
        return 'bg-gray-500';
    }
  };

  if (variant === 'compact') {
    return (
      <div className={`flex flex-col items-center gap-1 ${className}`}>
        <div className={`p-2 rounded-lg ${getPhaseColor()}`}>
          {getPhaseIcon()}
        </div>
        <div className={`h-1.5 w-1.5 rounded-full ${getStatusDotColor()} animate-pulse`} />
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className={`${className}`}>
        <div className="space-y-4">
          {/* Current Phase */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${getPhaseColor()}`}>
                {getPhaseIcon()}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-lg text-gray-900">{status.phaseLabel}</span>
                  <div className={`h-2 w-2 rounded-full ${getStatusDotColor()} animate-pulse`} />
                </div>
                <p className="text-sm text-gray-500">{status.currentTime}</p>
              </div>
            </div>
            <Badge variant="outline" className="text-xs font-mono px-3 py-1">
              {status.countdown}
            </Badge>
          </div>

          {/* Progress Bar (only for active phases) */}
          {status.progress !== undefined && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>Phase Progress</span>
                <span>{Math.round(status.progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-1000 ease-linear ${
                    status.phase === 'pre-market' ? 'bg-blue-500' :
                    status.phase === 'market-open' ? 'bg-green-500' :
                    'bg-purple-500'
                  }`}
                  style={{ width: `${status.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-gray-200" />

          {/* Next Phase Info */}
          <div className="flex items-start gap-2">
            <TrendingUp className="h-4 w-4 text-gray-400 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-gray-700">{status.nextPhase}</p>
              <p className="text-xs text-gray-500 mt-0.5">{status.nextPhaseTime}</p>
            </div>
          </div>

          {/* Trading Phases Reference */}
          {!status.isWeekend && (
            <div className="pt-2 border-t border-gray-100">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                  <span className="text-gray-600">Pre: 4:00 AM</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  <span className="text-gray-600">Open: 9:30 AM</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-gray-500" />
                  <span className="text-gray-600">Close: 4:00 PM</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-purple-500" />
                  <span className="text-gray-600">After: 8:00 PM</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Default 'detailed' variant - optimized for sidebar
  return (
    <div className={`space-y-2.5 ${className}`}>
      {/* Status Header with Live Time */}
      <div className="flex items-center justify-between pb-2 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg ${getPhaseColor()}`}>
            {getPhaseIcon()}
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-gray-900">{status.phaseLabel}</span>
            <span className="text-[10px] text-gray-500">{status.currentTime}</span>
          </div>
        </div>
        <div className={`h-2 w-2 rounded-full ${getStatusDotColor()} animate-pulse`} />
      </div>

      {/* Next Phase Info */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">{status.nextPhase}</span>
          <span className="text-xs font-semibold text-gray-900">{status.nextPhaseTime}</span>
        </div>
        
        {/* Countdown Display */}
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-2.5 border border-gray-200">
          <div className="text-center">
            <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wide">Countdown</div>
            <div className="font-mono text-xl font-bold text-gray-900 leading-tight">{status.countdown}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
