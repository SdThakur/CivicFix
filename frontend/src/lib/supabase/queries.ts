'use client';

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { getSupabaseBrowserClient } from '@/lib/supabase/client';
import { Database } from '@/types/supabase';

type Issue = Database['public']['Tables']['issues']['Row'];
type PublicIssue = Database['public']['Views']['public_issues']['Row'];
type Report = Database['public']['Tables']['reports']['Row'];

// ─── 1. MAP VIEWPORT LOADING VIA RPC (debounced on map idle) ──────────────────
export function useIssuesInBounds(params: {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
  categoryFilter?: string | null;
  statusFilter?: string | null;
  enabled?: boolean;
}) {
  const supabase = getSupabaseBrowserClient();

  return useQuery({
    queryKey: ['issues_in_bounds', params],
    queryFn: async () => {
      const { data, error } = await (supabase.rpc as any)('issues_in_bounds', {
        min_lat: params.minLat,
        max_lat: params.maxLat,
        min_lng: params.minLng,
        max_lng: params.maxLng,
        category_filter: params.categoryFilter || null,
        status_filter: params.statusFilter || null,
        p_limit: 250,
      });

      if (error) throw error;
      return (data ?? []) as Database['public']['Functions']['issues_in_bounds']['Returns'];
    },
    enabled: params.enabled !== false,
    staleTime: 1000 * 20, // 20 seconds
  });
}

// ─── 2. NEARBY ISSUES VIA RPC (100m warning & upvote candidate) ───────────────
export function useNearbyIssues(params: {
  lat: number;
  lng: number;
  radiusMeters?: number;
  enabled?: boolean;
}) {
  const supabase = getSupabaseBrowserClient();

  return useQuery({
    queryKey: ['nearby_issues', params.lat, params.lng, params.radiusMeters],
    queryFn: async () => {
      const { data, error } = await (supabase.rpc as any)('nearby_issues', {
        user_lat: params.lat,
        user_lng: params.lng,
        radius_meters: params.radiusMeters || 100.0,
        p_limit: 10,
      });

      if (error) throw error;
      return (data ?? []) as Database['public']['Functions']['nearby_issues']['Returns'];
    },
    enabled: params.enabled !== false && !isNaN(params.lat) && !isNaN(params.lng),
    staleTime: 1000 * 30,
  });
}

// ─── 3. TRANSPARENCY STATS & CATEGORY STATS ───────────────────────────────────
export function usePublicStats() {
  const supabase = getSupabaseBrowserClient();

  return useQuery({
    queryKey: ['public_stats'],
    queryFn: async () => {
      const { data, error } = await (supabase.from('public_stats') as any).select('*').limit(1).maybeSingle();
      if (error) throw error;
      return data as Database['public']['Views']['public_stats']['Row'] | null;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes (matches materialized view refresh)
  });
}

export function usePublicCategoryStats() {
  const supabase = getSupabaseBrowserClient();

  return useQuery({
    queryKey: ['public_category_stats'],
    queryFn: async () => {
      const { data, error } = await (supabase.from('public_category_stats') as any).select('*');
      if (error) throw error;
      return (data ?? []) as Database['public']['Views']['public_category_stats']['Row'][];
    },
    staleTime: 1000 * 60 * 5,
  });
}

// ─── 4. DASHBOARD FEED (KEYSET / CURSOR PAGINATION) ────────────────────────────
export function useDashboardFeed(userId?: string) {
  const supabase = getSupabaseBrowserClient();

  return useInfiniteQuery({
    queryKey: ['dashboard_feed', userId],
    queryFn: async ({ pageParam }) => {
      let query = supabase
        .from('reports')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      if (userId) {
        query = query.eq('user_id', userId);
      }

      // Keyset pagination using created_at cursor
      if (pageParam) {
        query = query.lt('created_at', pageParam);
      }

      const { data, error } = await query;
      if (error) throw error;
      return (data ?? []) as Report[];
    },
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => {
      if (!lastPage || lastPage.length < 10) return undefined;
      return lastPage[lastPage.length - 1].created_at;
    },
    enabled: Boolean(userId),
  });
}

// ─── 5. OPTIMISTIC UPVOTES MUTATION ───────────────────────────────────────────
export function useOptimisticUpvote() {
  const supabase = getSupabaseBrowserClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ issueId, userId }: { issueId: string; userId: string }) => {
      const { error } = await (supabase.from('issue_upvotes') as any).insert({
        issue_id: issueId,
        user_id: userId,
      });
      if (error) throw error;
      return { issueId };
    },
    onMutate: async ({ issueId }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['issues_in_bounds'] });

      // Snapshot previous state
      const previousData = queryClient.getQueryData(['issues_in_bounds']);

      // Optimistically update caches
      queryClient.setQueriesData({ queryKey: ['issues_in_bounds'] }, (old: any) => {
        if (!Array.isArray(old)) return old;
        return old.map((issue: any) =>
          issue.id === issueId
            ? { ...issue, upvotes: (issue.upvotes || 0) + 1, priority_score: Math.min(100, (issue.priority_score || 50) + 2) }
            : issue
        );
      });

      return { previousData };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousData) {
        queryClient.setQueriesData({ queryKey: ['issues_in_bounds'] }, context.previousData);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['issues_in_bounds'] });
      queryClient.invalidateQueries({ queryKey: ['nearby_issues'] });
    },
  });
}

// ─── 6. REALTIME SUBSCRIPTIONS HOOK ───────────────────────────────────────────
export function useRealtimeSubscriptions(params: {
  userId?: string;
  onReportChange?: (payload: any) => void;
  onIssueChange?: (payload: any) => void;
}) {
  const supabase = getSupabaseBrowserClient();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!params.userId) return;

    // 1. Subscribe to User's Own Reports
    const reportsChannel = supabase
      .channel(`user-reports-${params.userId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'reports',
          filter: `user_id=eq.${params.userId}`,
        },
        (payload) => {
          queryClient.invalidateQueries({ queryKey: ['dashboard_feed'] });
          if (params.onReportChange) params.onReportChange(payload);
        }
      )
      .subscribe();

    // 2. Subscribe to Global Issue Status Changes
    const issuesChannel = supabase
      .channel('public-issue-status-changes')
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'issues',
        },
        (payload) => {
          queryClient.invalidateQueries({ queryKey: ['issues_in_bounds'] });
          queryClient.invalidateQueries({ queryKey: ['public_stats'] });
          if (params.onIssueChange) params.onIssueChange(payload);
        }
      )
      .subscribe();

    // Cleanup and unsubscribe on unmount
    return () => {
      supabase.removeChannel(reportsChannel);
      supabase.removeChannel(issuesChannel);
    };
  }, [supabase, params.userId, queryClient, params]);
}

