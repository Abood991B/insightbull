import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';

interface MarketCountdownProps {
  className?: string;
  compact?: boolean;
}

export const MarketCountdown = ({ className = '', compact = false }: MarketCountdownProps) => {
  const [countdown, setCountdown] = useState<{
    text: string;
    isOpen: boolean;
  }>({ text: 'Calculating...', isOpen: false });

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();

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
        minute: parseInt(etParts.find(p => p.type === 'minute')?.value || '0')
      };

      const etDate = new Date(etTime.year, etTime.month, etTime.day, etTime.hour, etTime.minute);
      const day = etDate.getDay();
      const hour = etTime.hour;
      const minute = etTime.minute;

      const isWeekend = day === 0 || day === 6;
      const isMarketHours = !isWeekend && ((hour === 9 && minute >= 30) || (hour > 9 && hour < 16));

      if (isMarketHours) {
        const closeTime = new Date(etTime.year, etTime.month, etTime.day, 16, 0, 0);
        const closeTimeUTC = new Date(Date.UTC(
          etTime.year,
          etTime.month,
          etTime.day,
          isDST(closeTime) ? 20 : 21,
          0,
          0
        ));

        const diff = closeTimeUTC.getTime() - now.getTime();

        if (diff > 0) {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);

          setCountdown({
            text: compact
              ? `${hours}h ${minutes}m ${seconds}s`
              : `Market closes in ${hours}h ${minutes}m ${seconds}s`,
            isOpen: true
          });
        } else {
          setCountdown({ text: 'Market Open', isOpen: true });
        }
      } else {
        let daysToAdd = 0;

        if (day === 0) {
          daysToAdd = 1;
        } else if (day === 6) {
          daysToAdd = 2;
        } else if (hour >= 16) {
          daysToAdd = 1;
        }

        const nextOpenDate = new Date(Date.UTC(
          etTime.year,
          etTime.month,
          etTime.day + daysToAdd,
          isDST(etDate) ? 13 : 14,
          30,
          0
        ));

        const diff = nextOpenDate.getTime() - now.getTime();

        if (diff > 0) {
          const days = Math.floor(diff / (1000 * 60 * 60 * 24));
          const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);

          let timeStr = '';
          if (days > 0) {
            timeStr = compact
              ? `${days}d ${hours}h ${minutes}m`
              : `${days}d ${hours}h ${minutes}m ${seconds}s`;
          } else {
            timeStr = `${hours}h ${minutes}m ${seconds}s`;
          }

          setCountdown({
            text: compact ? timeStr : `Market opens in ${timeStr}`,
            isOpen: false
          });
        } else {
          setCountdown({ text: 'Market Closed', isOpen: false });
        }
      }
    };

    const isDST = (date: Date) => {
      const jan = new Date(date.getFullYear(), 0, 1);
      const jul = new Date(date.getFullYear(), 6, 1);
      return date.getTimezoneOffset() < Math.max(jan.getTimezoneOffset(), jul.getTimezoneOffset());
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [compact]);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Clock className={`h-4 w-4 ${countdown.isOpen ? 'text-green-500' : 'text-muted-foreground'}`} />
      <span className={`font-mono ${compact ? 'text-sm' : 'text-base'}`}>
        {countdown.text}
      </span>
    </div>
  );
};
