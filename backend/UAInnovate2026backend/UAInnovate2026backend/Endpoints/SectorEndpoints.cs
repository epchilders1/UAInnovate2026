using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class SectorEndpoints
    {
        public static void MapSectorEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/sectors").WithTags("Sectors");

            group.MapGet("/", async (AppDbContext db) =>
                await db.Sectors.ToListAsync())
                .WithName("GetAllSectors");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
                await db.Sectors.FindAsync(id) is Sector sector
                    ? Results.Ok(sector)
                    : Results.NotFound())
                .WithName("GetSectorById");

            group.MapPost("/", async (Sector sector, AppDbContext db) =>
            {
                db.Sectors.Add(sector);
                await db.SaveChangesAsync();
                return Results.Created($"/api/sectors/{sector.Id}", sector);
            }).WithName("CreateSector");

            group.MapPut("/{id}", async (int id, Sector input, AppDbContext db) =>
            {
                var sector = await db.Sectors.FindAsync(id);
                if (sector is null) return Results.NotFound();

                sector.SectorName = input.SectorName;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateSector");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var sector = await db.Sectors.FindAsync(id);
                if (sector is null) return Results.NotFound();

                db.Sectors.Remove(sector);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteSector");
        }
    }
}
