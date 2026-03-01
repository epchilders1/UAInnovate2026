using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class ResourceEndpoints
    {
        public static void MapResourceEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/resources").WithTags("Resources");

            group.MapGet("/", async (AppDbContext db) =>
                await db.Resources.ToListAsync())
                .WithName("GetAllResources");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
                await db.Resources.FindAsync(id) is Resource resource
                    ? Results.Ok(resource)
                    : Results.NotFound())
                .WithName("GetResourceById");

            group.MapPost("/", async (Resource resource, AppDbContext db) =>
            {
                db.Resources.Add(resource);
                await db.SaveChangesAsync();
                return Results.Created($"/api/resources/{resource.Id}", resource);
            }).WithName("CreateResource");

            group.MapPut("/{id}", async (int id, Resource input, AppDbContext db) =>
            {
                var resource = await db.Resources.FindAsync(id);
                if (resource is null) return Results.NotFound();

                resource.ResourceName = input.ResourceName;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateResource");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var resource = await db.Resources.FindAsync(id);
                if (resource is null) return Results.NotFound();

                db.Resources.Remove(resource);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteResource");
        }
    }
}
