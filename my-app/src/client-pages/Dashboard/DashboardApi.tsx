import { useState, useEffect } from 'react';


export interface ResourceItem {
  name: string;
  stockLevel: number;
  usage: number;
}

export interface ReportItem {
  heroAlias: string;
  timestamp: string;
  priority: string;
}

export interface DashboardData {
  resourceCount: number;
  daysRemaining: number;
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

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE}/api/dashboard`)
      .then(res => res.json())
      .then((json: DashboardData) => setData(json))
      .catch(err => console.error('Failed to fetch dashboard data:', err))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
