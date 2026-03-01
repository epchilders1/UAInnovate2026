import { useState, useEffect } from 'react';
import './NewReportModal.css';

const API_BASE = import.meta.env.VITE_API_BASE;

interface Hero {
  id: number;
  alias: string;
  contact: string;
}

const PRIORITY_OPTIONS = [
  { label: 'Routine', value: 0 },
  { label: 'High', value: 1 },
  { label: 'Avengers Level Threat', value: 2 },
];

const priorityColors: Record<number, string> = {
  0: '#22c55e',
  1: '#eab308',
  2: '#ef4444',
};

interface NewReportModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function NewReportModal({ onClose, onSuccess }: NewReportModalProps) {
  const [heroes, setHeroes] = useState<Hero[]>([]);
  const [heroId, setHeroId] = useState<number | ''>('');
  const [priority, setPriority] = useState<number>(0);
  const [rawText, setRawText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const now = new Date();
  const formattedTime = now.toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric',
  }) + ' ' + now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  useEffect(() => {
    fetch(`${API_BASE}/heroes`)
      .then(r => r.json())
      .then(setHeroes)
      .catch(() => {});
  }, []);

  const selectedHero = heroes.find(h => h.id === heroId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!heroId || !rawText.trim()) {
      setError('Please select a hero and enter a report.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText.trim(), hero_id: heroId, priority }),
      });
      if (!res.ok) throw new Error('Failed to submit report');
      onSuccess();
      onClose();
    } catch {
      setError('Failed to submit report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal new-report-modal" onClick={e => e.stopPropagation()}>
        <form onSubmit={handleSubmit}>
          <div className="report-modal-header">
            <div className="report-modal-title-row">
              <span
                className="report-modal-dot"
                style={{ backgroundColor: priorityColors[priority] }}
              />
              <select
                className="new-report-hero-select"
                value={heroId}
                onChange={e => setHeroId(Number(e.target.value))}
                required
              >
                <option value="">Select hero…</option>
                {heroes.map(h => (
                  <option key={h.id} value={h.id}>{h.alias}</option>
                ))}
              </select>
            </div>
            <button type="button" className="report-modal-close" onClick={onClose}>✕</button>
          </div>

          <div className="report-modal-meta">
            <div className="report-modal-meta-item">
              <span className="report-modal-meta-label">Priority</span>
              <select
                className="new-report-select"
                value={priority}
                onChange={e => setPriority(Number(e.target.value))}
                style={{ color: priorityColors[priority] }}
              >
                {PRIORITY_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div className="report-modal-meta-item">
              <span className="report-modal-meta-label">Time</span>
              <span className="report-modal-meta-value">{formattedTime}</span>
            </div>

            <div className="report-modal-meta-item" style={{ gridColumn: '1 / -1' }}>
              <span className="report-modal-meta-label">Contact</span>
              <span className="report-modal-meta-value">
                {selectedHero?.contact ?? <span className="new-report-placeholder">—</span>}
              </span>
            </div>
          </div>

          <div className="report-modal-body">
            <p className="report-modal-body-label">Report</p>
            <textarea
              className="new-report-textarea"
              value={rawText}
              onChange={e => setRawText(e.target.value)}
              placeholder="Describe the situation…"
              rows={5}
            />
          </div>

          {error && <p className="new-report-error">{error}</p>}

          <button
            type="submit"
            className="new-report-submit"
            disabled={submitting}
          >
            {submitting ? 'Submitting…' : 'Submit Report'}
          </button>
        </form>
      </div>
    </div>
  );
}
