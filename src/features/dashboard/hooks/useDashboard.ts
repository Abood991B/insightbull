import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/api/services/dashboard.service';

export const useDashboard = () => {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardService.getDashboardSummary(),
    refetchInterval: 120000, // Refetch every 2 minutes
    staleTime: 60000, // Consider data stale after 1 minute
  });
};
