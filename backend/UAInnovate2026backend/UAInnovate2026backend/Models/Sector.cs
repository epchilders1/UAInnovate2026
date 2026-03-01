namespace UAInnovate2026backend.Models
{
    public class Sector
    {
        public int Id { get; set; }
        public string SectorName { get; set; } = string.Empty;

        public ICollection<SectorResource> SectorResources { get; set; } = [];
        public ICollection<Report> Reports { get; set; } = [];
    }
}
