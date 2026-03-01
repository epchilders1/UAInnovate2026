namespace UAInnovate2026backend.Models
{
    public class Hero
    {
        public int Id { get; set; }
        public string Alias { get; set; } = string.Empty;
        public string Contact { get; set; } = string.Empty;

        public ICollection<Report> Reports { get; set; } = [];
    }
}
