using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class SectorResourceEndpoints
    {
        public static void MapSectorResourceEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/sector-resources").WithTags("SectorResources");

            group.MapGet("/", async (AppDbContext db) =>
                await db.SectorResources.ToListAsync())
                .WithName("GetAllSectorResources");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
                await db.SectorResources
                    .Include(sr => sr.Sector)
                    .Include(sr => sr.Resource)
                    .FirstOrDefaultAsync(sr => sr.Id == id) is SectorResource sr
                    ? Results.Ok(sr)
                    : Results.NotFound())
                .WithName("GetSectorResourceById");

            group.MapPost("/", async (SectorResource sectorResource, AppDbContext db) =>
            {
                db.SectorResources.Add(sectorResource);
                await db.SaveChangesAsync();
                return Results.Created($"/api/sector-resources/{sectorResource.Id}", sectorResource);
            }).WithName("CreateSectorResource");

            group.MapPut("/{id}", async (int id, SectorResource input, AppDbContext db) =>
            {
                var sectorResource = await db.SectorResources.FindAsync(id);
                if (sectorResource is null) return Results.NotFound();

                sectorResource.SectorId = input.SectorId;
                sectorResource.ResourceId = input.ResourceId;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateSectorResource");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var sectorResource = await db.SectorResources.FindAsync(id);
                if (sectorResource is null) return Results.NotFound();

                db.SectorResources.Remove(sectorResource);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteSectorResource");
        }
    }
}
