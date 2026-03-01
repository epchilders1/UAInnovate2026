import './StatsRow.css';

interface StatsRowProps {
  resourceCount?: number;
  daysRemaining?: number;
}

export default function StatsRow({ resourceCount, daysRemaining }: StatsRowProps) {
  return (
    <div className="stats-row">
      <div className="stats-card">
        <p className="stats-label">Resources</p>
        <p className="stats-value">{resourceCount}</p>
      </div>
      <div className="stats-card">
        <p className="stats-label">Time Until Depletion</p>
        <p className="stats-value">{daysRemaining} days remaining</p>
      </div>
    </div>
  );
}
