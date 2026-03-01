import './Dashboard.css';
import { useState, useEffect } from 'react';
import { useJarvis } from '../../context/JarvisContext';
import { useDashboardData } from './DashboardApi';
import type { ReportDetail } from './DashboardApi';
import { hatch } from 'ldrs';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import DashboardHeader from '../../components/DashboardHeader/DashboardHeader';
import StatsRow from '../../components/StatsRow/StatsRow';
import ResourceCard from '../../components/ResourceCard/ResourceCard';
import ReportCard from '../../components/ReportCard/ReportCard';
import ReportModal from '../../components/ReportModal/ReportModal';

hatch.register();

const USAGE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];
const STOCK_COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'];

export default function Dashboard() {
  const { askingPrompt } = useJarvis();
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set());
  const [activeReport, setActiveReport] = useState<ReportDetail | null>(null);

  // Input state (what's shown in the date pickers)
  const [inputStart, setInputStart] = useState('');
  const [inputEnd, setInputEnd] = useState('');

  // Fetch state (only updates on user change, not on initialization)
  const [fetchStart, setFetchStart] = useState<string | undefined>(undefined);
  const [fetchEnd, setFetchEnd] = useState<string | undefined>(undefined);

  const { data, loading } = useDashboardData(fetchStart, fetchEnd);

  // Populate date inputs from data on first load without triggering a re-fetch
  useEffect(() => {
    if (data?.minDate && !inputStart) setInputStart(data.minDate);
    if (data?.maxDate && !inputEnd) setInputEnd(data.maxDate);
  }, [data]);

  function handleDateChange(start: string, end: string) {
    setInputStart(start);
    setInputEnd(end);
    setFetchStart(start || undefined);
    setFetchEnd(end || undefined);
  }

  async function handleReportClick(id: number) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/reports/${id}`);
    const detail: ReportDetail = await res.json();
    setActiveReport(detail);
  }

  return (
    <div className="dashboard-layout dark">
      <main className="dashboard-main">
        <DashboardHeader />
        {loading ? (
          <>
            <div className="skeleton-stats-row">
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton skeleton-stat" />)}
            </div>
            <div className="charts-grid" style={{ marginBottom: '1.5rem' }}>
              <div className="skeleton skeleton-chart" />
              <div className="skeleton skeleton-chart" />
            </div>
            <div className="resource-cards-grid">
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton skeleton-card" />)}
            </div>
            <div className="report-cards-grid" style={{ marginTop: '1rem' }}>
              {[...Array(5)].map((_, i) => <div key={i} className="skeleton skeleton-card" />)}
            </div>
          </>
        ) : data ? (
          <>
            <div className="animate-in" style={{ animationDelay: '0s' }}>
              <StatsRow
                resourceCount={data.resourceCount}
                daysRemaining={data.daysRemaining}
              />
            </div>

            <div className="date-filter-row">
              <label className="date-filter-label">
                From
                <input
                  type="date"
                  className="date-filter-input"
                  value={inputStart}
                  min={data.minDate ?? ''}
                  max={inputEnd || (data.maxDate ?? '')}
                  onChange={e => handleDateChange(e.target.value, inputEnd)}
                />
              </label>
              <label className="date-filter-label">
                To
                <input
                  type="date"
                  className="date-filter-input"
                  value={inputEnd}
                  min={inputStart || (data.minDate ?? '')}
                  max={data.maxDate ?? ''}
                  onChange={e => handleDateChange(inputStart, e.target.value)}
                />
              </label>
              {(fetchStart || fetchEnd) && (
                <button
                  className="date-filter-clear"
                  onClick={() => {
                    setFetchStart(undefined);
                    setFetchEnd(undefined);
                  }}
                >
                  Clear
                </button>
              )}
            </div>

            <div className="charts-grid">
              <div className="chart-card animate-in" style={{ animationDelay: '0.08s' }}>
                <h3 className="chart-title">Resource Usage</h3>
                <p className="chart-subtitle">Consumption over time</p>
                <div style={{ width: '100%', height: 240, marginTop: '1rem' }}>
                  <ResponsiveContainer>
                    <LineChart data={data.usageChart.data}>
                      <CartesianGrid stroke="#1e2130" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        width={48}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e2130',
                          border: '1px solid #2d3148',
                          borderRadius: 8,
                          color: '#e5e7eb',
                        }}
                      />
                      {data.usageChart.categories
                        .filter(cat => selectedResources.size === 0 || selectedResources.has(cat))
                        .map((cat) => (
                          <Line
                            key={cat}
                            type="monotone"
                            dataKey={cat}
                            stroke={USAGE_COLORS[data.usageChart.categories.indexOf(cat) % USAGE_COLORS.length]}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="chart-card animate-in" style={{ animationDelay: '0.16s' }}>
                <h3 className="chart-title">Stock Levels</h3>
                <p className="chart-subtitle">Inventory levels over time</p>
                <div style={{ width: '100%', height: 240, marginTop: '1rem' }}>
                  <ResponsiveContainer>
                    <LineChart data={data.stockChart.data}>
                      <CartesianGrid stroke="#1e2130" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        width={48}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e2130',
                          border: '1px solid #2d3148',
                          borderRadius: 8,
                          color: '#e5e7eb',
                        }}
                      />
                      {data.stockChart.categories
                        .filter(cat => selectedResources.size === 0 || selectedResources.has(cat))
                        .map((cat) => (
                          <Line
                            key={cat}
                            type="monotone"
                            dataKey={cat}
                            stroke={STOCK_COLORS[data.stockChart.categories.indexOf(cat) % STOCK_COLORS.length]}
                            strokeWidth={2}
                            dot={false}
                          />
                        ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="resource-cards-grid">
              {data.resources.map((r, i) => (
                <div key={r.name} className="animate-in" style={{ animationDelay: `${0.24 + i * 0.08}s` }}>
                  <ResourceCard
                    name={r.name}
                    stockLevel={r.stockLevel}
                    usage={r.usage}
                    isSelected={selectedResources.has(r.name)}
                    onClick={() => setSelectedResources(prev => {
                      const next = new Set(prev);
                      next.has(r.name) ? next.delete(r.name) : next.add(r.name);
                      return next;
                    })}
                  />
                </div>
              ))}
            </div>

            <div className="report-cards-grid">
              {data.reports.map((r, i) => (
                <div key={r.id} className="animate-in" style={{ animationDelay: `${0.64 + i * 0.08}s` }}>
                  <ReportCard
                    heroAlias={r.heroAlias}
                    timestamp={r.timestamp}
                    priority={r.priority}
                    onClick={() => handleReportClick(r.id)}
                  />
                </div>
              ))}
            </div>
          </>
        ) : (
          <p>Failed to load dashboard data.</p>
        )}
      </main>

      {activeReport && (
        <ReportModal report={activeReport} onClose={() => setActiveReport(null)} />
      )}
    </div>
  );
}
