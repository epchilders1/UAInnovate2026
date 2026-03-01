import { useState, useEffect } from 'react';


export interface ResourceHistoryPoint {
  timestamp: string;
  stockLevel: number;
}

export interface ResourceItem {
  id: number;
  name: string;
  stockLevel: number;
  usage: number;
  history: ResourceHistoryPoint[];
  pctChange: number | null;
}

export interface ReportItem {
  id: number;
  heroAlias: string;
  timestamp: string;
  priority: string;
}

export interface ReportDetail {
  id: number;
  rawText: string;
  timestamp: string;
  priority: string;
  heroAlias: string;
  heroContact: string;
  resource: string;
  sector: string;
}

export interface DashboardData {
  resourceCount: number;
  daysRemaining: number;
  minDate: string | null;
  maxDate: string | null;
  resources: ResourceItem[];
  reports: ReportItem[];
  usageChart: {
    categories: string[];
    data: Record<string, unknown>[];
  };
  stockChart: {
    categories: string[];
    data: Record<string, unknown>[];
  };
}

export function useDashboardData(startDate?: string, endDate?: string, refreshKey?: number) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const query = params.toString() ? `?${params.toString()}` : '';

    fetch(`${import.meta.env.VITE_API_BASE}/api/dashboard${query}`)
      .then(res => res.json())
      .then((json: DashboardData) => setData(json))
      .catch(err => console.error('Failed to fetch dashboard data:', err))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [startDate, endDate, refreshKey]);

  // console.log(data)
  return { data, loading, refreshing };
}

export async function fetchMoreReports(
  offset: number,
  startDate?: string,
  endDate?: string,
): Promise<ReportItem[]> {
  const params = new URLSearchParams();
  params.set('offset', String(offset));
  params.set('limit', '5');
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  const res = await fetch(
    `${import.meta.env.VITE_API_BASE}/api/dashboard/reports?${params.toString()}`
  );
  return res.json();
}
