import './DashboardHeader.css';
import { Bell, Settings, LogOut } from 'lucide-react';
import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Tesseract from '../../assets/tesseract.svg'

export default function DashboardHeader() {
  const [openSettings, setOpenSettings] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpenSettings(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSignOut = async () => {
    const session_token = localStorage.getItem('session_token');
    if (session_token) {
      await fetch(`${import.meta.env.VITE_FLASK_URL}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_token }),
      });
      localStorage.removeItem('session_token');
    }
    navigate('/login');
  };

  return (
    <header className="dash-header">
      <div className="dash-header-left">
        <span className="dash-header-badge"><img src={Tesseract} alt="logo" /></span>
        <h1 className="dash-header-title">JFX Dashboard</h1>
      </div>
      <div className="dash-header-right">
        <div className="dash-header-settings-wrap" ref={dropdownRef}>
          <button
            onClick={() => setOpenSettings(o => !o)}
            className={`dash-header-btn${openSettings ? ' active' : ''}`}
            aria-label="Settings"
          >
            <Settings size={20} />
          </button>
          <div className={`dash-settings-dropdown${openSettings ? ' open' : ''}`}>
            <button className="dash-settings-item" onClick={handleSignOut}>
              <LogOut size={15} />
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
