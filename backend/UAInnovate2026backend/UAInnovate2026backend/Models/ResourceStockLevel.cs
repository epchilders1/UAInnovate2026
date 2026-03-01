namespace UAInnovate2026backend.Models
{
    public class ResourceStockLevel
    {
        public int Id { get; set; }
        public DateTime Timestamp { get; set; }
        public float StockLevel { get; set; }
        public float Usage { get; set; }
        public bool SnapEvent { get; set; }

        public int SectorResourceId { get; set; }
        public SectorResource SectorResource { get; set; } = null!;
    }
}
