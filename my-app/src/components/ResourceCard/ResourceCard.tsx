import './ResourceCard.css';

interface ResourceCardProps {
  name: string;
  stockLevel: number;
  usage: number;
}

export default function ResourceCard({ name, stockLevel, usage }: ResourceCardProps) {
  return (
    <div className="resource-card">
      <p className="resource-card-name">{name}</p>
      <p className="resource-card-stock">{stockLevel.toLocaleString()}</p>
      <p className="resource-card-usage">Usage: {usage}/hr</p>
    </div>
  );
}
