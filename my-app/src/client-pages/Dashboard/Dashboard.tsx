import './Dashboard.css';
import { useState, useEffect } from 'react';
import { useJarvis } from '../../context/JarvisContext';
import { useDashboardData, fetchMoreReports, fetchResourceForecast } from './DashboardApi';
import type { ReportDetail, ReportItem, ForecastData } from './DashboardApi';
import { hatch } from 'ldrs';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import DashboardHeader from '../../components/DashboardHeader/DashboardHeader';
import StatsRow from '../../components/StatsRow/StatsRow';
import ResourceCard from '../../components/ResourceCard/ResourceCard';
import ReportCard from '../../components/ReportCard/ReportCard';
import ReportModal from '../../components/ReportModal/ReportModal';
import NewReportModal from '../../components/NewReportModal/NewReportModal';

hatch.register();

const USAGE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];
const STOCK_COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'];

export default function Dashboard() {
  const { referencedResources } = useJarvis();
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set());
  const [forecasts, setForecasts] = useState<Record<string, ForecastData | null>>({});


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
    setForecasts({});
  }

  // Reset extra reports when the base data refreshes
  useEffect(() => {
    setExtraReports([]);
    setHasMore(true);
  }, [data]);

  // Re-fetch forecasts for selected resources when date range changes
  useEffect(() => {
    if (!data || selectedResources.size === 0) return;
    const endDate = fetchEnd || data.maxDate || undefined;
    for (const name of selectedResources) {
      const resource = data.resources.find(r => r.name === name);
      if (!resource) continue;
      fetchResourceForecast(resource.id, endDate ?? undefined)
        .then(fd => setForecasts(p => ({ ...p, [name]: fd })))
        .catch(() => setForecasts(p => ({ ...p, [name]: null })));
    }
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

  function buildMultiForecastChartData(
    baseData: Record<string, unknown>[],
    activeForecasts: Record<string, ForecastData>,
  ): Record<string, unknown>[] {
    const map = new Map<string, Record<string, unknown>>();
    for (const pt of baseData) map.set(pt.timestamp as string, { ...pt });

    // Find last historical timestamp so we only show forecast beyond it
    const lastHistTs = baseData.length > 0
      ? (baseData[baseData.length - 1].timestamp as string)
      : '';

    for (const [resourceName, forecast] of Object.entries(activeForecasts)) {
      const { timestamps, values } = forecast.forecastLine;
      for (let i = 0; i < timestamps.length; i++) {
        const ts = timestamps[i];
        const val = values[i];
        if (ts < lastHistTs) continue;
        const existing = map.get(ts);
        if (existing) {
          existing[`${resourceName}_forecast`] = val;
        } else {
          map.set(ts, { timestamp: ts, [`${resourceName}_forecast`]: val });
        }
      }
      // Ensure CI and zero-day timestamps exist as data points so ReferenceLine renders
      for (const ts of [forecast.ciLowDate, forecast.ciHighDate, forecast.zeroDayDate]) {
        if (ts && !map.has(ts)) {
          map.set(ts, { timestamp: ts });
        }
      }
    }
    return Array.from(map.values()).sort(
      (a, b) => (a.timestamp as string).localeCompare(b.timestamp as string),
    );
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
                    setInputStart('');
                    setInputEnd('');
                    setFetchStart(undefined);
                    setFetchEnd(undefined);
                    setForecasts({});
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

              {(() => {
                // Collect all active forecasts for selected resources
                const activeForecasts: Record<string, ForecastData> = {};
                for (const name of selectedResources) {
                  const fd = forecasts[name];
                  if (fd) activeForecasts[name] = fd;
                }
                const hasForecasts = Object.keys(activeForecasts).length > 0;
                const stockChartData = hasForecasts
                  ? buildMultiForecastChartData(data.stockChart.data, activeForecasts)
                  : data.stockChart.data;
                const visibleCategories = data.stockChart.categories.filter(
                  cat => selectedResources.size === 0 || selectedResources.has(cat),
                );
                return (
                  <div className="chart-card animate-in" style={{ animationDelay: '0.16s' }}>
                    <h3 className="chart-title">Stock Levels</h3>
                    <p className="chart-subtitle">
                      Inventory levels over time
                      {Object.entries(activeForecasts).map(([name, fd]) =>
                        fd.zeroDayDate ? (
                          <span key={name} style={{ marginLeft: '0.75rem', color: '#f43f5e', fontSize: 12 }}>
                            · {name} hits zero: {fd.zeroDayDate}
                            {fd.ciLowDate && fd.ciHighDate && (
                              <span style={{ color: '#f87171' }}>
                                {' '}(95% CI: {fd.ciLowDate} – {fd.ciHighDate})
                              </span>
                            )}
                          </span>
                        ) : null
                      )}
                    </p>
                    <div style={{ width: '100%', height: 240, marginTop: '1rem' }}>
                      <ResponsiveContainer>
                        <LineChart data={stockChartData}>
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
                          {visibleCategories.map((cat) => (
                            <Line
                              key={cat}
                              type="monotone"
                              dataKey={cat}
                              stroke={STOCK_COLORS[data.stockChart.categories.indexOf(cat) % STOCK_COLORS.length]}
                              strokeWidth={2}
                              dot={false}
                            />
                          ))}
                          {Object.keys(activeForecasts).map((name) => (
                            <Line
                              key={`${name}_forecast`}
                              type="monotone"
                              dataKey={`${name}_forecast`}
                              stroke={STOCK_COLORS[data.stockChart.categories.indexOf(name) % STOCK_COLORS.length]}
                              strokeWidth={2}
                              strokeDasharray="5 4"
                              dot={false}
                              connectNulls
                            />
                          ))}
                          {Object.entries(activeForecasts).map(([name, fd]) =>
                            fd.ciLowDate ? (
                              <ReferenceLine
                                key={`${name}_ci_lo`}
                                x={fd.ciLowDate}
                                stroke="#f87171"
                                strokeWidth={1.5}
                                strokeDasharray="3 3"
                                label={{ value: 'CI low', position: 'insideBottomLeft', fill: '#f87171', fontSize: 9 }}
                              />
                            ) : null
                          )}
                          {Object.entries(activeForecasts).map(([name, fd]) =>
                            fd.ciHighDate ? (
                              <ReferenceLine
                                key={`${name}_ci_hi`}
                                x={fd.ciHighDate}
                                stroke="#f87171"
                                strokeWidth={1.5}
                                strokeDasharray="3 3"
                                label={{ value: 'CI high', position: 'insideBottomRight', fill: '#f87171', fontSize: 9 }}
                              />
                            ) : null
                          )}
                          {Object.entries(activeForecasts).map(([name, fd]) =>
                            fd.zeroDayDate ? (
                              <ReferenceLine
                                key={`${name}_zero`}
                                x={fd.zeroDayDate}
                                stroke="#f43f5e"
                                strokeWidth={2}
                                strokeDasharray="4 3"
                                label={{ value: name, position: 'insideTopRight', fill: '#f43f5e', fontSize: 10 }}
                              />
                            ) : null
                          )}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                );
              })()}
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
                    isSelected={selectedResources.has(r.name)}
                    onClick={() => {
                      const wasSelected = selectedResources.has(r.name);
                      setSelectedResources(prev => {
                        const next = new Set(prev);
                        next.has(r.name) ? next.delete(r.name) : next.add(r.name);
                        return next;
                      });
                      if (!wasSelected && forecasts[r.name] === undefined) {
                        const endDate = fetchEnd || data?.maxDate || undefined;
                        fetchResourceForecast(r.id, endDate ?? undefined)
                          .then(fd => setForecasts(p => ({ ...p, [r.name]: fd })))
                          .catch(() => setForecasts(p => ({ ...p, [r.name]: null })));
                      }
                    }}
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
