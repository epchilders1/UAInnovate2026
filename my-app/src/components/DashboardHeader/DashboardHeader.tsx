import './DashboardHeader.css';
import { Bell, Settings } from 'lucide-react';

export default function DashboardHeader() {
  return (
    <header className="dash-header">
      <div className="dash-header-left">
        <span className="dash-header-badge">JFX</span>
        <h1 className="dash-header-title">Dashboard</h1>
      </div>
      <div className="dash-header-right">
        <button className="dash-header-btn" aria-label="Notifications">
          <Bell size={20} />
        </button>
        <button className="dash-header-btn" aria-label="Settings">
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
}
