from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import IntEnum


class Priority(IntEnum):
    Routine = 0
    High = 1
    AvengersLevelThreat = 2


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str
    contact: str

    reports: List["Report"] = Relationship(back_populates="hero")


class Sector(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sector_name: str

    sector_resources: List["SectorResource"] = Relationship(back_populates="sector")
    reports: List["Report"] = Relationship(back_populates="sector")


class Resource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_name: str

    sector_resources: List["SectorResource"] = Relationship(back_populates="resource")
    reports: List["Report"] = Relationship(back_populates="resource")


class SectorResource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sector_id: int = Field(foreign_key="sector.id")
    resource_id: int = Field(foreign_key="resource.id")

    sector: Optional[Sector] = Relationship(back_populates="sector_resources")
    resource: Optional[Resource] = Relationship(back_populates="sector_resources")
    stock_levels: List["ResourceStockLevel"] = Relationship(back_populates="sector_resource")


class ResourceStockLevel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stock_level: float
    usage: float
    snap_event: bool = False
    sector_resource_id: int = Field(foreign_key="sectorresource.id")

    sector_resource: Optional[SectorResource] = Relationship(back_populates="stock_levels")


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=Priority.Routine)
    hero_id: int = Field(foreign_key="hero.id")
    resource_id: int = Field(foreign_key="resource.id")
    sector_id: int = Field(foreign_key="sector.id")

    hero: Optional[Hero] = Relationship(back_populates="reports")
    resource: Optional[Resource] = Relationship(back_populates="reports")
    sector: Optional[Sector] = Relationship(back_populates="reports")
