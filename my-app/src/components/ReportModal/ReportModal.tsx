import './ReportModal.css';
import type { ReportDetail } from '../../client-pages/Dashboard/DashboardApi';

const priorityColors: Record<string, string> = {
  'Routine': '#22c55e',
  'High': '#eab308',
  'Avengers Level Threat': '#ef4444',
};

interface ReportModalProps {
  report: ReportDetail;
  onClose: () => void;
}

export default function ReportModal({ report, onClose }: ReportModalProps) {
  const date = new Date(report.timestamp);
  const formatted = date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }) + ' ' + date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="report-modal-overlay" onClick={onClose}>
      <div className="report-modal" onClick={e => e.stopPropagation()}>
        <div className="report-modal-header">
          <div className="report-modal-title-row">
            <span
              className="report-modal-dot"
              style={{ backgroundColor: priorityColors[report.priority] || '#6b7280' }}
            />
            <h2 className="report-modal-title">{report.heroAlias}</h2>
          </div>
          <button className="report-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="report-modal-meta">
          <div className="report-modal-meta-item">
            <span className="report-modal-meta-label">Priority</span>
            <span
              className="report-modal-priority"
              style={{ color: priorityColors[report.priority] || '#6b7280' }}
            >
              {report.priority}
            </span>
          </div>
          <div className="report-modal-meta-item">
            <span className="report-modal-meta-label">Time</span>
            <span className="report-modal-meta-value">{formatted}</span>
          </div>
          <div className="report-modal-meta-item">
            <span className="report-modal-meta-label">Contact</span>
            <span className="report-modal-meta-value">{report.heroContact}</span>
          </div>
          <div className="report-modal-meta-item">
            <span className="report-modal-meta-label">Resource</span>
            <span className="report-modal-meta-value">{report.resource}</span>
          </div>
          <div className="report-modal-meta-item">
            <span className="report-modal-meta-label">Sector</span>
            <span className="report-modal-meta-value">{report.sector}</span>
          </div>
        </div>

        <div className="report-modal-body">
          <p className="report-modal-body-label">Report</p>
          <p className="report-modal-body-text">{report.rawText}</p>
        </div>
      </div>
    </div>
  );
}
