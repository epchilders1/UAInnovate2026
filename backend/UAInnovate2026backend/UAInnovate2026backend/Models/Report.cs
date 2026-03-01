namespace UAInnovate2026backend.Models
{
    public class Report
    {
        public int Id { get; set; }
        public string RawText { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public Priority Priority { get; set; }

        public int HeroId { get; set; }
        public Hero Hero { get; set; } = null!;

        public int ResourceId { get; set; }
        public Resource Resource { get; set; } = null!;

        public int SectorId { get; set; }
        public Sector Sector { get; set; } = null!;
    }
}
