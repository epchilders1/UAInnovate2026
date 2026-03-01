"""
Seed the jarvis.db SQLite database from the challenger_package data files.

Usage:
    cd my-app/python-app
    python seeddb.py
"""

import csv
import json
from datetime import datetime
from sqlmodel import Session, select
from database import create_db, engine
from models import Hero, Sector, Resource, SectorResource, ResourceStockLevel, Report, Priority

DATA_DIR = "../../challenger_package"

SECTORS = ["Avengers Compound", "New Asgard", "Sanctum Sanctorum", "Sokovia", "Wakanda"]
RESOURCES = ["Arc Reactor Cores", "Clean Water (L)", "Medical Kits", "Pym Particles", "Vibranium (kg)"]
HEROES = {
    "Tony Stark": "555-0101 (Iron Line)",
    "Natasha Romanoff": "555-0199 (Black Widow Comms)",
    "Thor Odinson": "555-GOD-OF-THUNDER",
    "Peter Parker": "555-0123 (Spider-Sense)",
    "Bruce Banner": "555-HULK-SMASH",
    "Steve Rogers": "555-1941 (Shield Freq)",
}

PRIORITY_MAP = {
    "Routine": Priority.Routine,
    "High": Priority.High,
    "Avengers Level Threat": Priority.AvengersLevelThreat,
}


def seed():
    create_db()

    with Session(engine) as session:
        # Check if already seeded
        existing = session.exec(select(Hero)).first()
        if existing:
            print("Database already seeded. Delete jarvis.db and re-run to reseed.")
            return

        # --- Heroes ---
        hero_map = {}
        for alias, contact in HEROES.items():
            hero = Hero(alias=alias, contact=contact)
            session.add(hero)
            session.flush()
            hero_map[alias] = hero.id
        print(f"Seeded {len(hero_map)} heroes")

        # --- Sectors ---
        sector_map = {}
        for name in SECTORS:
            sector = Sector(sector_name=name)
            session.add(sector)
            session.flush()
            sector_map[name] = sector.id
        print(f"Seeded {len(sector_map)} sectors")

        # --- Resources ---
        resource_map = {}
        for name in RESOURCES:
            resource = Resource(resource_name=name)
            session.add(resource)
            session.flush()
            resource_map[name] = resource.id
        print(f"Seeded {len(resource_map)} resources")

        # --- SectorResources (one per sector-resource pair) ---
        sr_map = {}
        for sector_name in SECTORS:
            for resource_name in RESOURCES:
                sr = SectorResource(
                    sector_id=sector_map[sector_name],
                    resource_id=resource_map[resource_name],
                )
                session.add(sr)
                session.flush()
                sr_map[(sector_name, resource_name)] = sr.id
        print(f"Seeded {len(sr_map)} sector-resource pairs")

        # --- Stock Levels from CSV ---
        stock_count = 0
        # with open(f"{DATA_DIR}/cleaned_avengers_data.csv", newline="") as f:
        with open(f"{DATA_DIR}/avengers_data_with_snap.csv", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sector_name = row["sector_id"]
                resource_name = row["resource_type"]
                sr_id = sr_map.get((sector_name, resource_name))
                if sr_id is None:
                    continue
                level = ResourceStockLevel(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    stock_level=float(row["stock_level"]),
                    usage=float(row["usage_rate_hourly"]),
                    snap_event=row["snap_event_detected"] == "True",
                    sector_resource_id=sr_id,
                )
                session.add(level)
                stock_count += 1
        print(f"Seeded {stock_count} stock level records")

        # --- Reports from JSON ---
        with open(f"{DATA_DIR}/field_intel_reports.json") as f:
            reports = json.load(f)

        report_count = 0
        for r in reports:
            hero_alias = r["metadata"]["hero_alias"]
            hero_id = hero_map.get(hero_alias)
            if hero_id is None:
                continue

            raw = r["raw_text"]
            # Extract sector and resource from raw_text
            sector_id = None
            resource_id = None
            for s in SECTORS:
                if s in raw:
                    sector_id = sector_map[s]
                    break
            for res in RESOURCES:
                if res in raw:
                    resource_id = resource_map[res]
                    break

            # Default to first sector/resource if not found in text
            if sector_id is None:
                sector_id = sector_map[SECTORS[0]]
            if resource_id is None:
                resource_id = resource_map[RESOURCES[0]]

            report = Report(
                raw_text=raw,
                timestamp=datetime.fromisoformat(r["timestamp"]),
                priority=PRIORITY_MAP.get(r["priority"], Priority.Routine),
                hero_id=hero_id,
                resource_id=resource_id,
                sector_id=sector_id,
            )
            session.add(report)
            report_count += 1
        print(f"Seeded {report_count} reports")

        session.commit()
        print("Done! Database seeded successfully.")


if __name__ == "__main__":
    seed()
