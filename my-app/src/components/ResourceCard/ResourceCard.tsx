import './ResourceCard.css';

interface ResourceCardProps {
  name: string;
  stockLevel: number;
  usage: number;
  isSelected?: boolean;
  onClick?: () => void;
}

export default function ResourceCard({ name, stockLevel, usage, isSelected, onClick }: ResourceCardProps) {
  return (
    <div className={`resource-card${isSelected ? ' resource-card--selected' : ''}`} onClick={onClick} style={{ cursor: onClick ? 'pointer' : undefined }}>
      <p className="resource-card-name">{name}</p>
      <p className="resource-card-stock">{stockLevel.toLocaleString()}</p>
      <p className="resource-card-usage">Usage: {usage}/hr</p>
    </div>
  );
}
