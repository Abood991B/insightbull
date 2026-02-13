/**
 * usePipelineNotifications Hook
 * 
 * Enables cross-tab/window communication for pipeline completion events.
 * When admin triggers pipeline in one tab, dashboard in another tab gets notified instantly.
 * 
 * Uses localStorage events for cross-tab communication.
 */

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface PipelineEvent {
  type: 'pipeline_completed' | 'pipeline_started';
  timestamp: number;
  summary?: {
    analyzed: number;
    stored: number;
    status: 'success' | 'partial' | 'error';
  };
}

const PIPELINE_EVENT_KEY = 'insight_stock_pipeline_event';

/**
 * Hook to listen for pipeline completion events and trigger data refresh
 * 
 * @param onPipelineComplete - Optional callback when pipeline completes
 */
export const usePipelineNotifications = (
  onPipelineComplete?: (event: PipelineEvent) => void
) => {
  const queryClient = useQueryClient();

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      // Only handle our specific event key
      if (e.key !== PIPELINE_EVENT_KEY || !e.newValue) return;

      try {
        const event: PipelineEvent = JSON.parse(e.newValue);
        
        // Only process recent events (within last 5 seconds)
        const eventAge = Date.now() - event.timestamp;
        if (eventAge > 5000) return;

        if (event.type === 'pipeline_completed') {
          // Invalidate all dashboard-related queries to trigger refetch
          queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
          queryClient.invalidateQueries({ queryKey: ['stocks'] });
          queryClient.invalidateQueries({ queryKey: ['sentiment'] });
          
          // Call optional callback
          onPipelineComplete?.(event);
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('Failed to parse pipeline event:', error);
        }
      }
    };

    // Listen for storage events (cross-tab communication)
    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [queryClient, onPipelineComplete]);
};

/**
 * Broadcast pipeline event to all tabs/windows
 * 
 * Call this from admin panel after pipeline completes
 */
export const broadcastPipelineEvent = (event: Omit<PipelineEvent, 'timestamp'>) => {
  const fullEvent: PipelineEvent = {
    ...event,
    timestamp: Date.now(),
  };

  // Store event in localStorage (triggers storage event in other tabs)
  localStorage.setItem(PIPELINE_EVENT_KEY, JSON.stringify(fullEvent));

  // Clean up old event after 10 seconds
  setTimeout(() => {
    const current = localStorage.getItem(PIPELINE_EVENT_KEY);
    if (current === JSON.stringify(fullEvent)) {
      localStorage.removeItem(PIPELINE_EVENT_KEY);
    }
  }, 10000);
};
