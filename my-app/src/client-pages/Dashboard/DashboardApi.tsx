import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:5001';

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

export function useDashboardData(startDate?: string, endDate?: string) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (data) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const query = params.toString() ? `?${params}` : '';

    fetch(`${API_BASE}/api/dashboard${query}`)
      .then(res => res.json())
      .then((json: DashboardData) => setData(json))
      .catch(err => console.error('Failed to fetch dashboard data:', err))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [startDate, endDate]);

  console.log(data)
  return { data, loading, refreshing };
}
