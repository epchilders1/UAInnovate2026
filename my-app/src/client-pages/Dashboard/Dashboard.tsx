import './Dashboard.css';
import { useJarvis } from '../../context/JarvisContext';
import { useDashboardData } from './DashboardApi';
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

hatch.register();

const USAGE_COLORS = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];
const STOCK_COLORS = ['#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#10b981'];

export default function Dashboard() {
  const { askingPrompt } = useJarvis();
  const { data, loading } = useDashboardData();

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
                      {data.usageChart.categories.map((cat, i) => (
                        <Line
                          key={cat}
                          type="monotone"
                          dataKey={cat}
                          stroke={USAGE_COLORS[i % USAGE_COLORS.length]}
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
                      {data.stockChart.categories.map((cat, i) => (
                        <Line
                          key={cat}
                          type="monotone"
                          dataKey={cat}
                          stroke={STOCK_COLORS[i % STOCK_COLORS.length]}
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
              {data.resources.map((r) => (
                <ResourceCard
                  key={r.name}
                  name={r.name}
                  stockLevel={r.stockLevel}
                  usage={r.usage}
                />
              ))}
            </div>

            <div className="report-cards-grid">
              {data.reports.map((r, i) => (
                <ReportCard
                  key={i}
                  heroAlias={r.heroAlias}
                  timestamp={r.timestamp}
                  priority={r.priority}
                />
              ))}
            </div>
          </>
        ) : (
          <p>Failed to load dashboard data.</p>
        )}
      </main>
    </div>
  );
}
