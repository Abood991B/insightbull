import { useQuery } from '@tanstack/react-query';
import { analysisService } from '@/api/services/analysis.service';

export const useSentimentHistory = (
  symbol: string,
  timeframe: '1d' | '7d' | '14d' = '7d',
  limit: number = 100
) => {
  return useQuery({
    queryKey: ['sentiment-history', symbol, timeframe, limit],
    queryFn: () => analysisService.getSentimentHistory(symbol, timeframe, limit),
    enabled: !!symbol,
    staleTime: 60000, // 1 minute
  });
};

export const useCorrelationAnalysis = (
  symbol: string,
  timeframe: '1d' | '7d' | '14d' = '7d'
) => {
  return useQuery({
    queryKey: ['correlation', symbol, timeframe],
    queryFn: () => analysisService.getCorrelationAnalysis(symbol, timeframe),
    enabled: !!symbol,
    staleTime: 60000, // 1 minute
  });
};
