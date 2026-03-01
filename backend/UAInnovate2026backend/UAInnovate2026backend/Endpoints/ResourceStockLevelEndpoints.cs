using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class ResourceStockLevelEndpoints
    {
        public static void MapResourceStockLevelEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/stock-levels").WithTags("ResourceStockLevels");

            // Optional filter: /api/stock-levels?sectorResourceId=1
            group.MapGet("/", async (int? sectorResourceId, AppDbContext db) =>
            {
                var query = db.ResourceStockLevels.AsQueryable();
                if (sectorResourceId.HasValue)
                    query = query.Where(r => r.SectorResourceId == sectorResourceId.Value);
                return await query.Take(500).ToListAsync();
            }).WithName("GetAllStockLevels");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
                await db.ResourceStockLevels
                    .Include(r => r.SectorResource)
                    .FirstOrDefaultAsync(r => r.Id == id) is ResourceStockLevel level
                    ? Results.Ok(level)
                    : Results.NotFound())
                .WithName("GetStockLevelById");

            group.MapPost("/", async (ResourceStockLevel stockLevel, AppDbContext db) =>
            {
                db.ResourceStockLevels.Add(stockLevel);
                await db.SaveChangesAsync();
                return Results.Created($"/api/stock-levels/{stockLevel.Id}", stockLevel);
            }).WithName("CreateStockLevel");

            group.MapPut("/{id}", async (int id, ResourceStockLevel input, AppDbContext db) =>
            {
                var stockLevel = await db.ResourceStockLevels.FindAsync(id);
                if (stockLevel is null) return Results.NotFound();

                stockLevel.Timestamp = input.Timestamp;
                stockLevel.StockLevel = input.StockLevel;
                stockLevel.Usage = input.Usage;
                stockLevel.SnapEvent = input.SnapEvent;
                stockLevel.SectorResourceId = input.SectorResourceId;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateStockLevel");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var stockLevel = await db.ResourceStockLevels.FindAsync(id);
                if (stockLevel is null) return Results.NotFound();

                db.ResourceStockLevels.Remove(stockLevel);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteStockLevel");
        }
    }
}
