import './ResourceCard.css';

interface HistoryPoint { timestamp: string; stockLevel: number; }

interface ResourceCardProps {
  id: number;
  name: string;
  stockLevel?: number;
  usage?: number;
  history?: HistoryPoint[];
  pctChange?: number | null;
  isSelected?: boolean;
  loadingPrediction?: boolean;
  onClick?: () => void;
}

function Sparkline({ history, color }: { history: HistoryPoint[]; color: string }) {
  if (history.length < 2) return null;
  const W = 80, H = 32;
  const vals = history.map(p => p.stockLevel);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const points = vals
    .map((v, i) => `${(i / (vals.length - 1)) * W},${H - ((v - min) / range) * (H - 2) - 1}`)
    .join(' ');
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', flexShrink: 0 }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default function ResourceCard({ name, stockLevel, usage, history, pctChange, isSelected, loadingPrediction, onClick }: ResourceCardProps) {
  const isUp = pctChange != null && pctChange > 0;
  const isDown = pctChange != null && pctChange < 0;
  const sparkColor = isDown ? '#f43f5e' : isUp ? '#10b981' : '#6b7280';
  const hasSparkline = history && history.length >= 2;

  return (
    <div className={`resource-card${isSelected ? ' resource-card--selected' : ''}`} onClick={onClick} style={{ cursor: onClick ? 'pointer' : undefined }}>
      <p className="resource-card-name">{name}</p>
      <div className="resource-card-body">
        <div className="resource-card-left">
          <div className="resource-card-row">
            <p className="resource-card-stock">{stockLevel?.toLocaleString()}</p>
            {pctChange != null && (
              <span className={`resource-card-pct${isDown ? ' pct-down' : isUp ? ' pct-up' : ''}`}>
                {isUp ? '▲' : isDown ? '▼' : '—'} {Math.abs(pctChange)}%
              </span>
            )}
          </div>
          <p className="resource-card-usage">Usage: {usage}/hr</p>
          {loadingPrediction && (
            <p className="resource-card-predicting">
              <span className="predicting-dot" />
              Analyzing
            </p>
          )}
        </div>
        {hasSparkline && (
          <div className="resource-card-sparkline">
            <Sparkline history={history!} color={sparkColor} />
          </div>
        )}
      </div>
    </div>
  );
}
