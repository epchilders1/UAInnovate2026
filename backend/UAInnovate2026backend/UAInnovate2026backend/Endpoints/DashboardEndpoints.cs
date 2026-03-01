using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;

namespace UAInnovate2026backend.Endpoints
{
    public static class DashboardEndpoints
    {
        public static void MapDashboardEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/dashboard").WithTags("Dashboard");

            group.MapGet("/", async (AppDbContext db) =>
            {
                var sectorCount = await db.Sectors.CountAsync();
                var resourceCount = await db.Resources.CountAsync();
                var heroCount = await db.Heroes.CountAsync();
                var reportCount = await db.Reports.CountAsync();

                // Get all stock level records with their resource names
                var rawData = await db.ResourceStockLevels
                    .Include(rsl => rsl.SectorResource)
                        .ThenInclude(sr => sr.Resource)
                    .OrderBy(rsl => rsl.Timestamp)
                    .Select(rsl => new
                    {
                        rsl.Timestamp,
                        Resource = rsl.SectorResource.Resource.ResourceName,
                        rsl.Usage,
                        rsl.StockLevel
                    })
                    .ToListAsync();

                var resourceNames = await db.Resources
                    .Select(r => r.ResourceName)
                    .ToListAsync();

                // Pivot usage data: { timestamp, Resource1: usage1, Resource2: usage2, ... }
                var usageByTimestamp = rawData
                    .GroupBy(r => r.Timestamp)
                    .OrderBy(g => g.Key)
                    .Select(g =>
                    {
                        var dict = new Dictionary<string, object>
                        {
                            ["timestamp"] = g.Key.ToString("yyyy-MM-dd HH:mm")
                        };
                        foreach (var item in g)
                            dict[item.Resource] = Math.Round(item.Usage, 2);
                        return dict;
                    })
                    .ToList();

                // Pivot stock data: { timestamp, Resource1: level1, Resource2: level2, ... }
                var stockByTimestamp = rawData
                    .GroupBy(r => r.Timestamp)
                    .OrderBy(g => g.Key)
                    .Select(g =>
                    {
                        var dict = new Dictionary<string, object>
                        {
                            ["timestamp"] = g.Key.ToString("yyyy-MM-dd HH:mm")
                        };
                        foreach (var item in g)
                            dict[item.Resource] = Math.Round(item.StockLevel, 2);
                        return dict;
                    })
                    .ToList();

                return Results.Ok(new
                {
                    cards = new
                    {
                        sectors = sectorCount,
                        resources = resourceCount,
                        heroes = heroCount,
                        reports = reportCount
                    },
                    usageChart = new
                    {
                        categories = resourceNames,
                        data = usageByTimestamp
                    },
                    stockChart = new
                    {
                        categories = resourceNames,
                        data = stockByTimestamp
                    }
                });
            }).WithName("GetDashboardData");
        }
    }
}
