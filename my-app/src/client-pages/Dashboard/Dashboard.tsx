import './Dashboard.css';
import { useJarvis } from '../../context/JarvisContext';
import { useDashboardData } from './DashboardApi';
import { hatch } from 'ldrs';
import {
  Card,
  AreaChart,
} from '@tremor/react';
import {
  Shield,
  LayoutDashboard,
  Map,
  BarChart3,
  Settings,
  Bell,
} from 'lucide-react';

hatch.register();

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', active: true },
  { icon: Map, label: 'Sectors' },
  { icon: BarChart3, label: 'Analytics' },
  { icon: Bell, label: 'Alerts' },
  { icon: Settings, label: 'Settings' },
];

export default function Dashboard() {
  const { askingPrompt } = useJarvis();
  const { data, loading } = useDashboardData();

  const statCards = data
    ? [
        { title: 'Sectors', value: data.cards.sectors.toLocaleString() },
        { title: 'Resources', value: data.cards.resources.toLocaleString() },
        { title: 'Heroes', value: data.cards.heroes.toLocaleString() },
        { title: 'Reports', value: data.cards.reports.toLocaleString() },
      ]
    : [];

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Shield size={28} />
          <span>JARVIS FUCKS</span>
        </div>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <button
              key={item.label}
              className={`sidebar-item ${item.active ? 'active' : ''}`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <p className="dashboard-subtitle">Operations Overview</p>
        </header>

        {loading ? (
          <p>Loading...</p>
        ) : data ? (
          <>
            <div className="stat-cards">
              {statCards.map((card) => (
                <Card key={card.title} className="stat-card">
                  <p className="stat-label">{card.title}</p>
                  <p className="stat-value">{card.value}</p>
                </Card>
              ))}
            </div>

            <div className="charts-grid">
              <Card className="chart-card">
                <h3 className="chart-title">Resource Usage</h3>
                <p className="chart-subtitle">Consumption over time</p>
                <AreaChart
                  className="mt-4 h-60"
                  data={data.usageChart.data}
                  index="timestamp"
                  categories={data.usageChart.categories}
                  colors={['blue', 'cyan', 'emerald']}
                  yAxisWidth={48}
                  showLegend={false}
                  showAnimation
                />
              </Card>

              <Card className="chart-card">
                <h3 className="chart-title">Stock Levels</h3>
                <p className="chart-subtitle">Inventory levels over time</p>
                <AreaChart
                  className="mt-4 h-60"
                  data={data.stockChart.data}
                  index="timestamp"
                  categories={data.stockChart.categories}
                  colors={['rose', 'amber', 'violet']}
                  yAxisWidth={48}
                  showAnimation
                  showLegend={false}
                />
              </Card>
            </div>
          </>
        ) : (
          <p>Failed to load dashboard data.</p>
        )}
      </main>
    </div>
  );
}
