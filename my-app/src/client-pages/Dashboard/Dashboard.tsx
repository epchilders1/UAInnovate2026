import './Dashboard.css';
import { useState, useEffect, useMemo } from 'react';
import { useJarvis } from '../../context/JarvisContext';
import { useDashboardData, fetchMoreReports } from './DashboardApi';
import type { ReportDetail, ReportItem } from './DashboardApi';
import { hatch } from 'ldrs';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
} from 'recharts';
import DashboardHeader from '../../components/DashboardHeader/DashboardHeader';
import ResourceCard from '../../components/ResourceCard/ResourceCard';
import ReportCard from '../../components/ReportCard/ReportCard';
import ReportModal from '../../components/ReportModal/ReportModal';
import NewReportModal from '../../components/NewReportModal/NewReportModal';

hatch.register();

const USAGE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];
const STOCK_COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'];

type RegressionData = {
  line: { timestamps: string[]; data: number[] };
  ci: { OK: boolean; ci_lo?: number; ci_hi?: number; t_star?: number } | null;
  result: { t_star: number; [key: string]: any } | null;
  t_0: string;
  t_star_ts: string | null;
  ci_lo_ts: string | null;
  ci_hi_ts: string | null;
};

export default function Dashboard() {
  const { referencedResources } = useJarvis();
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set());
  const [regressionData, setRegressionData] = useState<Record<string, RegressionData>>({});
  const [regressionLoading, setRegressionLoading] = useState<Set<string>>(new Set());


  const [activeReport, setActiveReport] = useState<ReportDetail | null>(null);
  const [showNewReport, setShowNewReport] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const [extraReports, setExtraReports] = useState<ReportItem[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const [inputStart, setInputStart] = useState('');
  const [inputEnd, setInputEnd] = useState('');

  const [fetchStart, setFetchStart] = useState<string | undefined>(undefined);
  const [fetchEnd, setFetchEnd] = useState<string | undefined>(undefined);

  const { data, loading } = useDashboardData(fetchStart, fetchEnd, refreshKey);

  useEffect(() => {
    if (referencedResources.length === 0 || !data?.resources) return;
    const normalize = (s: string) => s.replace(/\s*\(.*?\)$/, '').trim().toLowerCase();
    const matched = new Set(
      data.resources
        .filter(r => referencedResources.some(ref => normalize(ref) === normalize(r.name)))
        .map(r => r.name)
    );
    if (matched.size > 0) setSelectedResources(matched);
  }, [referencedResources, data]);
  
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

  useEffect(() => {
    setExtraReports([]);
    setHasMore(true);
  }, [data]);

  async function handleLoadMore() {
    if (!data) return;
    setLoadingMore(true);
    const next = await fetchMoreReports(
      data.reports.length + extraReports.length,
      fetchStart,
      fetchEnd,
    );
    setExtraReports(prev => [...prev, ...next]);
    if (next.length < 5) setHasMore(false);
    setLoadingMore(false);
  }

  async function handleReportClick(id: number) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE}/reports/${id}`);
    const detail: ReportDetail = await res.json();
    setActiveReport(detail);
  }

  async function handleResourceClick(r: any) {
    const isSelected = selectedResources.has(r.name);
    setSelectedResources(prev => {
      const next = new Set(prev);
      next.has(r.name) ? next.delete(r.name) : next.add(r.name);
      return next;
    });
    if (!isSelected && !regressionData[r.name]) {
      setRegressionLoading(prev => new Set(prev).add(r.name));
      try {
        const res = await fetch(`${import.meta.env.VITE_API_BASE}/api/regression/${r.id}`);
        const reg: RegressionData = await res.json();
        setRegressionData(prev => ({ ...prev, [r.name]: reg }));
      } catch (e) {
        console.error('Regression fetch failed', e);
      } finally {
        setRegressionLoading(prev => { const next = new Set(prev); next.delete(r.name); return next; });
      }
    }
  }

  const normalizeTs = (ts: string) => ts.replace('T', ' ').slice(0, 16);

  const mergedStockData = useMemo(() => {
    if (!data) return [];
    const real = data.stockChart.data;
    const lastTs = real.length > 0 ? real[real.length - 1].timestamp : null;
    const merged: Record<string, any>[] = real.map(p => ({ ...p }));

    for (const [name, reg] of Object.entries(regressionData)) {
      if (!selectedResources.has(name) || !reg?.line) continue;
      const { timestamps, data: vals } = reg.line;

      // Find last regression index at or before the last real timestamp (connector)
      let connectorIdx = -1;
      for (let i = 0; i < timestamps.length; i++) {
        if (normalizeTs(timestamps[i]) <= (lastTs ?? '')) connectorIdx = i;
        else break;
      }
      if (connectorIdx >= 0 && lastTs) {
        const lastPoint = merged.find(p => p.timestamp === lastTs);
        if (lastPoint) lastPoint[`${name}_proj`] = Math.max(0, vals[connectorIdx]);
      }

      // Append projection points after last real timestamp, clamped to >= 0
      for (let i = 0; i < timestamps.length; i++) {
        const ts = normalizeTs(timestamps[i]);
        if (lastTs && ts <= lastTs) continue;
        const val = Math.max(0, vals[i]);
        merged.push({ timestamp: ts, [`${name}_proj`]: val });
        if (val === 0) break; // no point extending past depletion
      }
    }

    // Inject CI marker timestamps so the categorical x-axis recognises them
    for (const [name, reg] of Object.entries(regressionData)) {
      if (!selectedResources.has(name) || !reg?.ci?.OK) continue;
      for (const ts of [reg.ci_lo_ts, reg.ci_hi_ts, reg.t_star_ts]) {
        if (ts && !merged.find(p => p.timestamp === ts)) {
          merged.push({ timestamp: ts });
        }
      }
    }

    merged.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    return merged;
  }, [data, regressionData, selectedResources]);

  return (
    <div className="dashboard-layout dark">
      <main className="dashboard-main">
        <DashboardHeader />
        {loading ? (
          <>
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
                    setInputStart('');
                    setInputEnd('');
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
                {Object.entries(regressionData).map(([name, reg]) => {
                  if (!selectedResources.has(name) || !reg?.ci?.OK || !reg.result) return null;
                  const t0 = new Date(reg.t_0);
                  const fmt = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  const depleteDate = new Date(t0.getTime() + reg.result.t_star * 12 * 60 * 1000);
                  const ciLo = reg.ci.ci_lo != null ? new Date(t0.getTime() + reg.ci.ci_lo * 12 * 60 * 1000) : null;
                  const ciHi = reg.ci.ci_hi != null ? new Date(t0.getTime() + reg.ci.ci_hi * 12 * 60 * 1000) : null;
                  const catIdx = data.stockChart.categories.indexOf(name);
                  const color = STOCK_COLORS[catIdx % STOCK_COLORS.length];
                  return (
                    <div key={name} className="projection-badge" style={{ borderColor: color }}>
                      <span className="projection-badge-name" style={{ color }}>{name}</span>
                      <span>depletes <strong>{fmt(depleteDate)}</strong></span>
                      {ciLo && ciHi && (
                        <span className="projection-badge-ci">95% CI: {fmt(ciLo)} – {fmt(ciHi)}</span>
                      )}
                    </div>
                  );
                })}
                <div style={{ width: '100%', height: 240, marginTop: '1rem' }}>
                  <ResponsiveContainer>
                    <LineChart data={mergedStockData}>
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
                      {Object.entries(regressionData).map(([name, reg]) => {
                        if (!selectedResources.has(name) || !reg?.line) return null;
                        const catIdx = data.stockChart.categories.indexOf(name);
                        const color = STOCK_COLORS[catIdx % STOCK_COLORS.length];
                        return (
                          <Line
                            key={`${name}_proj`}
                            type="monotone"
                            dataKey={`${name}_proj`}
                            stroke={color}
                            strokeWidth={2}
                            strokeOpacity={0.45}
                            strokeDasharray="6 4"
                            dot={false}
                            connectNulls
                          />
                        );
                      })}
                      {Object.entries(regressionData).map(([name, reg]) => {
                        if (!selectedResources.has(name) || !reg?.ci?.OK) return null;
                        const catIdx = data.stockChart.categories.indexOf(name);
                        const color = STOCK_COLORS[catIdx % STOCK_COLORS.length];
                        return [
                          reg.ci_lo_ts && reg.ci_hi_ts && (
                            <ReferenceArea
                              key={`${name}_ci_band`}
                              x1={reg.ci_lo_ts}
                              x2={reg.ci_hi_ts}
                              fill={color}
                              fillOpacity={0.12}
                              strokeOpacity={0}
                            />
                          ),
                          reg.t_star_ts && (
                            <ReferenceLine
                              key={`${name}_t_star`}
                              x={reg.t_star_ts}
                              stroke={color}
                              strokeWidth={1.5}
                              strokeDasharray="4 3"
                              strokeOpacity={0.7}
                            />
                          ),
                        ];
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <h2 className="section-title">Resources</h2>
            <div className="resource-cards-grid">
              {data.resources.map((r, i) => (
                <div key={r.name} className="animate-in" style={{ animationDelay: `${0.24 + i * 0.08}s` }}>
                  <ResourceCard
                    id={r.id}
                    name={r.name}
                    stockLevel={r.stockLevel}
                    usage={r.usage}
                    history={r.history}
                    pctChange={r.pctChange}
                    isSelected={selectedResources.has(r.name)}
                    loadingPrediction={regressionLoading.has(r.name)}
                    onClick={() => handleResourceClick(r)}
                  />
                </div>
              ))}
            </div>

            <div className="section-header">
              <h2 className="section-title">Reports</h2>
              <button className="new-report-btn" onClick={() => setShowNewReport(true)}>+ New</button>
            </div>
            <div className="report-cards-grid">
              {[...data.reports, ...extraReports].map((r, i) => (
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
            {hasMore && (
              <button
                className="date-filter-clear"
                style={{ marginTop: '0.75rem' }}
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? 'Loading…' : 'Load more'}
              </button>
            )}
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
