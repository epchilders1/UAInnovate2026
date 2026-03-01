import { useState, useEffect } from 'react';


export interface ResourceItem {
  name: string;
  stockLevel: number;
  usage: number;
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
    fetch(`${import.meta.env.VITE_API_BASE}/api/dashboard`)
      .then(res => res.json())
      .then((json: DashboardData) => setData(json))
      .catch(err => console.error('Failed to fetch dashboard data:', err))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [startDate, endDate, refreshKey]);

  return { data, loading, refreshing };
}
