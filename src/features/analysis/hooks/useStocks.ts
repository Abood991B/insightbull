import { useQuery } from '@tanstack/react-query';
import { stockService } from '@/api/services/stock.service';

export const useStocks = (params?: { limit?: number; active_only?: boolean }) => {
  return useQuery({
    queryKey: ['stocks', params],
    queryFn: () => stockService.getAllStocks(params),
    staleTime: 300000, // 5 minutes
  });
};

export const useStockDetail = (symbol: string, timeframe: '1d' | '7d' | '14d' = '7d') => {
  return useQuery({
    queryKey: ['stock', symbol, timeframe],
    queryFn: () => stockService.getStockDetail(symbol, timeframe),
    enabled: !!symbol,
    staleTime: 60000, // 1 minute
  });
};
