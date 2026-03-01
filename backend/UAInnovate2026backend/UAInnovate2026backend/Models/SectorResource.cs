namespace UAInnovate2026backend.Models
{
    public class SectorResource
    {
        public int Id { get; set; }

        public int SectorId { get; set; }
        public Sector Sector { get; set; } = null!;

        public int ResourceId { get; set; }
        public Resource Resource { get; set; } = null!;

        public ICollection<ResourceStockLevel> ResourceStockLevels { get; set; } = [];
    }
}
