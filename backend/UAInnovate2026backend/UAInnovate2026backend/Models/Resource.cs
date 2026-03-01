namespace UAInnovate2026backend.Models
{
    public class Resource
    {
        public int Id { get; set; }
        public string ResourceName { get; set; } = string.Empty;

        public ICollection<SectorResource> SectorResources { get; set; } = [];
        public ICollection<Report> Reports { get; set; } = [];
    }
}
