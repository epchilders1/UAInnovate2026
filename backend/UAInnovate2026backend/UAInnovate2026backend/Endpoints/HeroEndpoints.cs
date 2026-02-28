using Microsoft.EntityFrameworkCore;
using UAInnovate2026backend.Data;
using UAInnovate2026backend.Models;

namespace UAInnovate2026backend.Endpoints
{
    public static class HeroEndpoints
    {
        public static void MapHeroEndpoints(this WebApplication app)
        {
            var group = app.MapGroup("/api/heroes").WithTags("Heroes");

            group.MapGet("/", async (AppDbContext db) =>
                await db.Heroes.ToListAsync())
                .WithName("GetAllHeroes");

            group.MapGet("/{id}", async (int id, AppDbContext db) =>
                await db.Heroes.FindAsync(id) is Hero hero
                    ? Results.Ok(hero)
                    : Results.NotFound())
                .WithName("GetHeroById");

            group.MapPost("/", async (Hero hero, AppDbContext db) =>
            {
                db.Heroes.Add(hero);
                await db.SaveChangesAsync();
                return Results.Created($"/api/heroes/{hero.Id}", hero);
            }).WithName("CreateHero");

            group.MapPut("/{id}", async (int id, Hero input, AppDbContext db) =>
            {
                var hero = await db.Heroes.FindAsync(id);
                if (hero is null) return Results.NotFound();

                hero.Alias = input.Alias;
                hero.Contact = input.Contact;
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("UpdateHero");

            group.MapDelete("/{id}", async (int id, AppDbContext db) =>
            {
                var hero = await db.Heroes.FindAsync(id);
                if (hero is null) return Results.NotFound();

                db.Heroes.Remove(hero);
                await db.SaveChangesAsync();
                return Results.NoContent();
            }).WithName("DeleteHero");
        }
    }
}
