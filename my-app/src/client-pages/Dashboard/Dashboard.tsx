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
import NewReportModal from '../../components/NewReportModal/NewReportModal';

hatch.register();

const API_BASE = 'http://localhost:5001';
const USAGE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];
const STOCK_COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'];

export default function Dashboard() {
  const { askingPrompt } = useJarvis();
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set());
  const [activeReport, setActiveReport] = useState<ReportDetail | null>(null);
  const [showNewReport, setShowNewReport] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Input state (what's shown in the date pickers)
  const [inputStart, setInputStart] = useState('');
  const [inputEnd, setInputEnd] = useState('');

  // Fetch state (only updates on user change, not on initialization)
  const [fetchStart, setFetchStart] = useState<string | undefined>(undefined);
  const [fetchEnd, setFetchEnd] = useState<string | undefined>(undefined);

  const { data, loading } = useDashboardData(fetchStart, fetchEnd, refreshKey);

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
    const res = await fetch(`${API_BASE}/reports/${id}`);
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
            <StatsRow
              resourceCount={data.resourceCount}
              daysRemaining={data.daysRemaining}
            />

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
              <div className="chart-card">
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

              <div className="chart-card">
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

            <h2 className="section-title">Resources</h2>
            <div className="resource-cards-grid">
              {data.resources.map((r) => (
                <ResourceCard
                  key={r.name}
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
              ))}
            </div>

            <div className="section-header">
              <h2 className="section-title">Reports</h2>
              <button className="new-report-btn" onClick={() => setShowNewReport(true)}>+ New</button>
            </div>
            <div className="report-cards-grid">
              {data.reports.map((r) => (
                <ReportCard
                  key={r.id}
                  heroAlias={r.heroAlias}
                  timestamp={r.timestamp}
                  priority={r.priority}
                  onClick={() => handleReportClick(r.id)}
                />
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
      {showNewReport && (
        <NewReportModal
          onClose={() => setShowNewReport(false)}
          onSuccess={() => setRefreshKey(k => k + 1)}
        />
      )}
    </div>
  );
}
