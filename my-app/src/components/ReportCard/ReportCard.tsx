import './ReportCard.css';

interface ReportCardProps {
  heroAlias: string;
  timestamp: string;
  priority: string;
  onClick?: () => void;
}

const priorityColors: Record<string, string> = {
  'Routine': '#22c55e',
  'High': '#eab308',
  'Avengers Level Threat': '#ef4444',
};

export default function ReportCard({ heroAlias, timestamp, priority, onClick }: ReportCardProps) {
  const date = new Date(timestamp);
  const formatted = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  }) + ' ' + date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="report-card" onClick={onClick} style={{ cursor: onClick ? 'pointer' : undefined }}>
      <div className="report-card-top">
        <span
          className="report-card-dot"
          style={{ backgroundColor: priorityColors[priority] || '#6b7280' }}
        />
        <span className="report-card-hero">{heroAlias}</span>
      </div>
      <p className="report-card-time">{formatted}</p>
    </div>
  );
}
