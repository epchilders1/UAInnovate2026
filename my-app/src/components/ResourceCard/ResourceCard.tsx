import './ResourceCard.css';

interface ResourceCardProps {
  id: number;
  name: string;
  stockLevel?: number;
  usage?: number;
  isSelected?: boolean;
  onClick?: () => void;
}

export default function ResourceCard({ id, name, stockLevel, usage, isSelected, onClick }: ResourceCardProps) {
  return (
    <div className={`resource-card${isSelected ? ' resource-card--selected' : ''}`} onClick={() => { console.log(id); onClick?.(); }} style={{ cursor: onClick ? 'pointer' : undefined }}>
      <p className="resource-card-name">{name}</p>
      <p className="resource-card-stock">{stockLevel?.toLocaleString()}</p>
      <p className="resource-card-usage">Usage: {usage}/hr</p>
    </div>
  );
}
