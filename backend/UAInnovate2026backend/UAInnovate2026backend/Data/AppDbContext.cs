using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<Sector> Sectors { get; set; }
        public DbSet<Resource> Resources { get; set; }
        public DbSet<SectorResource> SectorResources { get; set; }
        public DbSet<ResourceStockLevel> ResourceStockLevels { get; set; }
        public DbSet<Hero> Heroes { get; set; }
        public DbSet<Report> Reports { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Report>()
                .Property(r => r.Priority)
                .HasConversion<string>();
        }
    }
}
