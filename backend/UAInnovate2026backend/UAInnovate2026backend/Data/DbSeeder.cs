using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Data
{
    public static class DbSeeder
    {
        public static async Task SeedAsync(AppDbContext db)
        {
            // Only seed if the database is empty
            if (await db.Sectors.AnyAsync()) return;

            var baseDir = AppContext.BaseDirectory;
            var csvPath = Path.Combine(baseDir, "SeedData", "historical_avengers_data.csv");
            var jsonPath = Path.Combine(baseDir, "SeedData", "field_intel_reports.json");

            // ── 1. Parse CSV ────────────────────────────────────────────────
            var csvLines = await File.ReadAllLinesAsync(csvPath);
            var dataRows = csvLines.Skip(1).Select(l => l.Split(',')).Where(p => p.Length >= 6).ToList();

            // Unique sectors and resources
            var sectorNames = dataRows.Select(p => p[1].Trim()).Distinct().ToList();
            var resourceNames = dataRows.Select(p => p[2].Trim()).Distinct().ToList();

            // ── 2. Seed Sectors ──────────────────────────────────────────────
            var sectors = sectorNames.Select(n => new Sector { SectorName = n }).ToList();
            db.Sectors.AddRange(sectors);
            await db.SaveChangesAsync();
            var sectorMap = sectors.ToDictionary(s => s.SectorName, s => s.Id);

            // ── 3. Seed Resources ────────────────────────────────────────────
            var resources = resourceNames.Select(n => new Resource { ResourceName = n }).ToList();
            db.Resources.AddRange(resources);
            await db.SaveChangesAsync();
            var resourceMap = resources.ToDictionary(r => r.ResourceName, r => r.Id);

            // ── 4. Seed SectorResources (unique pairs) ───────────────────────
            var srPairs = dataRows
                .Select(p => (sector: p[1].Trim(), resource: p[2].Trim()))
                .Distinct()
                .ToList();

            var sectorResources = srPairs.Select(p => new SectorResource
            {
                SectorId = sectorMap[p.sector],
                ResourceId = resourceMap[p.resource]
            }).ToList();

            db.SectorResources.AddRange(sectorResources);
            await db.SaveChangesAsync();

            // Build a lookup: (sectorName, resourceName) → SectorResource.Id
            var srMap = sectorResources.ToDictionary(
                sr => (
                    sectors.First(s => s.Id == sr.SectorId).SectorName,
                    resources.First(r => r.Id == sr.ResourceId).ResourceName
                ),
                sr => sr.Id
            );

            // ── 5. Seed ResourceStockLevels ──────────────────────────────────
            var stockLevels = new List<ResourceStockLevel>();
            foreach (var parts in dataRows)
            {
                var sectorName = parts[1].Trim();
                var resourceName = parts[2].Trim();

                if (!srMap.TryGetValue((sectorName, resourceName), out var srId)) continue;

                stockLevels.Add(new ResourceStockLevel
                {
                    Timestamp = DateTime.Parse(parts[0].Trim()),
                    StockLevel = float.Parse(parts[3].Trim()),
                    Usage = float.Parse(parts[4].Trim()),
                    SnapEvent = parts[5].Trim().Equals("True", StringComparison.OrdinalIgnoreCase),
                    SectorResourceId = srId
                });
            }

            db.ResourceStockLevels.AddRange(stockLevels);
            await db.SaveChangesAsync();

            // ── 6. Parse JSON ────────────────────────────────────────────────
            var jsonContent = await File.ReadAllTextAsync(jsonPath);
            using var jsonDoc = JsonDocument.Parse(jsonContent);
            var reportItems = jsonDoc.RootElement.EnumerateArray().ToList();

            // ── 7. Seed Heroes (unique aliases) ──────────────────────────────
            var heroData = new Dictionary<string, string>();
            foreach (var item in reportItems)
            {
                var meta = item.GetProperty("metadata");
                var alias = meta.GetProperty("hero_alias").GetString() ?? "";
                var contact = meta.GetProperty("secure_contact").GetString() ?? "";
                heroData.TryAdd(alias, contact);
            }

            var heroes = heroData.Select(kv => new Hero { Alias = kv.Key, Contact = kv.Value }).ToList();
            db.Heroes.AddRange(heroes);
            await db.SaveChangesAsync();
            var heroMap = heroes.ToDictionary(h => h.Alias, h => h.Id);

            // ── 8. Seed Reports ───────────────────────────────────────────────
            var reports = new List<Report>();
            foreach (var item in reportItems)
            {
                var meta = item.GetProperty("metadata");
                var alias = meta.GetProperty("hero_alias").GetString() ?? "";
                var rawText = item.GetProperty("raw_text").GetString() ?? "";
                var timestamp = DateTime.Parse(item.GetProperty("timestamp").GetString() ?? DateTime.UtcNow.ToString());
                var priorityStr = item.GetProperty("priority").GetString() ?? "Routine";

                var priority = priorityStr switch
                {
                    "Avengers Level Threat" => Priority.AvengersLevelThreat,
                    "High" => Priority.High,
                    _ => Priority.Routine
                };

                // Match sector and resource from names mentioned in the raw text
                var sectorId = sectorMap
                    .Where(kv => rawText.Contains(kv.Key, StringComparison.OrdinalIgnoreCase))
                    .Select(kv => kv.Value)
                    .FirstOrDefault();
                if (sectorId == 0) sectorId = sectorMap.Values.First();

                var resourceId = resourceMap
                    .Where(kv => rawText.Contains(kv.Key, StringComparison.OrdinalIgnoreCase))
                    .Select(kv => kv.Value)
                    .FirstOrDefault();
                if (resourceId == 0) resourceId = resourceMap.Values.First();

                reports.Add(new Report
                {
                    HeroId = heroMap[alias],
                    RawText = rawText,
                    Timestamp = timestamp,
                    Priority = priority,
                    SectorId = sectorId,
                    ResourceId = resourceId
                });
            }

            db.Reports.AddRange(reports);
            await db.SaveChangesAsync();
        }
    }
}
