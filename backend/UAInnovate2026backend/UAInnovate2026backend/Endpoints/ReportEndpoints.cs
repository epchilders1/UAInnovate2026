using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class ReportEndpoints
    {
        public static void MapReportEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/reports").WithTags("Reports");

            // Optional filters: /api/reports?sectorId=1&resourceId=2
            group.MapGet("/", async (int? sectorId, int? resourceId, AppDbContext db) =>
            {
                var query = db.Reports
                    .Include(r => r.Resource)
                    .Include(r => r.Sector)
                    .AsQueryable();
                if (sectorId.HasValue)
                    query = query.Where(r => r.SectorId == sectorId.Value);
                if (resourceId.HasValue)
                    query = query.Where(r => r.ResourceId == resourceId.Value);
                return await query.Select(r => new
                {
                    r.Id,
                    r.RawText,
                    r.Timestamp,
                    r.Priority,
                    r.HeroId,
                    r.ResourceId,
                    ResourceName = r.Resource.ResourceName,
                    r.SectorId,
                    SectorName = r.Sector.SectorName
                }).ToListAsync();
            }).WithName("GetAllReports");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
            {
                var report = await db.Reports
                    .Include(r => r.Hero)
                    .Include(r => r.Resource)
                    .Include(r => r.Sector)
                    .FirstOrDefaultAsync(r => r.Id == id);
                if (report is null) return Results.NotFound();
                return Results.Ok(new
                {
                    report.Id,
                    report.RawText,
                    report.Timestamp,
                    report.Priority,
                    report.HeroId,
                    HeroAlias = report.Hero.Alias,
                    report.ResourceId,
                    ResourceName = report.Resource.ResourceName,
                    report.SectorId,
                    SectorName = report.Sector.SectorName
                });
            }).WithName("GetReportById");

            group.MapPost("/", async (Report report, AppDbContext db) =>
            {
                db.Reports.Add(report);
                await db.SaveChangesAsync();
                return Results.Created($"/api/reports/{report.Id}", report);
            }).WithName("CreateReport");

            group.MapPut("/{id}", async (int id, Report input, AppDbContext db) =>
            {
                var report = await db.Reports.FindAsync(id);
                if (report is null) return Results.NotFound();

                report.RawText = input.RawText;
                report.Timestamp = input.Timestamp;
                report.Priority = input.Priority;
                report.HeroId = input.HeroId;
                report.ResourceId = input.ResourceId;
                report.SectorId = input.SectorId;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateReport");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var report = await db.Reports.FindAsync(id);
                if (report is null) return Results.NotFound();

                db.Reports.Remove(report);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteReport");
        }
    }
}
