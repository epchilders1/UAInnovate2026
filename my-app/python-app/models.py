from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timedelta
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
    timestamp: datetime = Field(default_factory=datetime.now)
    stock_level: float
    usage: float
    snap_event: bool = False
    sector_resource_id: int = Field(foreign_key="sectorresource.id")

    sector_resource: Optional[SectorResource] = Relationship(back_populates="stock_levels")


class Report(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raw_text: str
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: int = Field(default=Priority.Routine)
    hero_id: int = Field(foreign_key="hero.id")
    resource_id: int = Field(foreign_key="resource.id")
    sector_id: int = Field(foreign_key="sector.id")

    hero: Optional[Hero] = Relationship(back_populates="reports")
    resource: Optional[Resource] = Relationship(back_populates="reports")
    sector: Optional[Sector] = Relationship(back_populates="reports")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

    sessions: List["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_token: str
    expires: datetime = Field(default_factory=lambda: datetime.now() + timedelta(weeks=1))
    user_id: int = Field(foreign_key="user.id")

    user: Optional[User] = Relationship(back_populates="sessions")