from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from sqlalchemy import func, desc
from database import create_db, get_session
<<<<<<< HEAD
from models import Hero, Sector, Resource, SectorResource, ResourceStockLevel, Report, User, UserSession
=======
from models import Hero, Sector, Resource, SectorResource, ResourceStockLevel, Report, Priority
>>>>>>> 0ae04fab6a676fc30d0292244c849775c27bcee2
from jarvis import Jarvis
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid, base64, json

jarvis = Jarvis()

class Message(BaseModel):
    role: str
    content: str

class AskJarvisRequest(BaseModel):
    messageList: List[Message]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db()


def decode_google_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT")
    payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


# --- Auth ---

class LoginRequest(BaseModel):
    google_token: str

class LogoutRequest(BaseModel):
    session_token: str

@app.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_session)):
    try:
        payload = decode_google_jwt(body.google_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = payload.get("email")
    name = payload.get("name", email)
    if not email:
        raise HTTPException(status_code=400, detail="No email in token")

    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(name=name, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    old_sessions = db.exec(select(UserSession).where(UserSession.user_id == user.id)).all()
    for s in old_sessions:
        if s.expires < datetime.utcnow():
            db.delete(s)
    db.commit()

    token = str(uuid.uuid4())
    new_session = UserSession(session_token=token, user_id=user.id)
    db.add(new_session)
    db.commit()

    return {"session_token": token}

@app.post("/auth/logout")
def logout(body: LogoutRequest, db: Session = Depends(get_session)):
    session = db.exec(select(UserSession).where(UserSession.session_token == body.session_token)).first()
    if session:
        db.delete(session)
        db.commit()
    return {"ok": True}


# --- Jarvis ---

@app.post("/ask_jarvis")
async def ask_jarvis(body: AskJarvisRequest):
    message_dicts = [m.model_dump() for m in body.messageList]
    response = await jarvis.ask_jarvis(messageList=message_dicts)
    return response


# --- Heroes ---

@app.get("/heroes")
def get_heroes(session: Session = Depends(get_session)):
    return session.exec(select(Hero)).all()

@app.get("/heroes/{hero_id}")
def get_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.post("/heroes")
def create_hero(hero: Hero, session: Session = Depends(get_session)):
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


# --- Sectors ---

@app.get("/sectors")
def get_sectors(session: Session = Depends(get_session)):
    return session.exec(select(Sector)).all()

@app.post("/sectors")
def create_sector(sector: Sector, session: Session = Depends(get_session)):
    session.add(sector)
    session.commit()
    session.refresh(sector)
    return sector


# --- Resources ---

@app.get("/resources")
def get_resources(session: Session = Depends(get_session)):
    return session.exec(select(Resource)).all()

@app.post("/resources")
def create_resource(resource: Resource, session: Session = Depends(get_session)):
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return resource


# --- Stock Levels ---

@app.get("/stock-levels")
def get_stock_levels(session: Session = Depends(get_session)):
    return session.exec(select(ResourceStockLevel)).all()

@app.get("/stock-levels/{sector_resource_id}")
def get_stock_levels_for_sector_resource(sector_resource_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(ResourceStockLevel).where(ResourceStockLevel.sector_resource_id == sector_resource_id)
    ).all()

@app.post("/stock-levels")
def create_stock_level(stock_level: ResourceStockLevel, session: Session = Depends(get_session)):
    session.add(stock_level)
    session.commit()
    session.refresh(stock_level)
    return stock_level


# --- Reports ---

@app.get("/reports")
def get_reports(session: Session = Depends(get_session)):
    return session.exec(select(Report)).all()

@app.post("/reports")
def create_report(report: Report, session: Session = Depends(get_session)):
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


# --- Dashboard ---

@app.get("/api/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    # Resource count
    resources = session.exec(select(Resource)).all()
    resource_count = len(resources)
    resource_map = {r.id: r.resource_name for r in resources}

    # Get all sector_resources to map sector_resource_id -> resource_name
    sector_resources = session.exec(select(SectorResource)).all()
    sr_to_resource = {sr.id: resource_map.get(sr.resource_id, "Unknown") for sr in sector_resources}

    # Get latest stock level and average usage per resource
    resource_stats = {}
    for sr in sector_resources:
        rname = sr_to_resource[sr.id]
        levels = session.exec(
            select(ResourceStockLevel)
            .where(ResourceStockLevel.sector_resource_id == sr.id)
            .order_by(desc(ResourceStockLevel.timestamp))
        ).all()
        if not levels:
            continue
        latest_stock = levels[0].stock_level
        avg_usage = sum(l.usage for l in levels) / len(levels) if levels else 0
        if rname not in resource_stats:
            resource_stats[rname] = {"stockLevel": 0, "usage": 0, "count": 0}
        resource_stats[rname]["stockLevel"] += latest_stock
        resource_stats[rname]["usage"] += avg_usage
        resource_stats[rname]["count"] += 1

    # Build resource list and compute days remaining
    resource_list = []
    days_remaining_values = []
    for name, stats in resource_stats.items():
        avg_usage = stats["usage"] / stats["count"] if stats["count"] else 0
        stock = stats["stockLevel"]
        resource_list.append({
            "name": name,
            "stockLevel": round(stock, 1),
            "usage": round(avg_usage, 2),
        })
        if avg_usage > 0:
            days_remaining_values.append(stock / (avg_usage * 24))

    days_remaining = round(min(days_remaining_values)) if days_remaining_values else 0

    # Get 5 most recent reports with hero alias
    reports_query = (
        select(Report, Hero)
        .join(Hero, Report.hero_id == Hero.id)
        .order_by(desc(Report.timestamp))
        .limit(5)
    )
    report_rows = session.exec(reports_query).all()
    priority_names = {0: "Routine", 1: "High", 2: "Avengers Level Threat"}
    report_list = [
        {
            "heroAlias": hero.alias,
            "timestamp": report.timestamp.isoformat(),
            "priority": priority_names.get(report.priority, "Routine"),
        }
        for report, hero in report_rows
    ]

    # Build chart time series data (aggregate by timestamp across all sectors per resource)
    all_levels = session.exec(
        select(ResourceStockLevel)
        .order_by(ResourceStockLevel.timestamp)
    ).all()

    # Group by timestamp
    usage_by_ts = {}
    stock_by_ts = {}
    for level in all_levels:
        rname = sr_to_resource.get(level.sector_resource_id, "Unknown")
        ts = level.timestamp.strftime("%Y-%m-%d %H:%M")
        if ts not in usage_by_ts:
            usage_by_ts[ts] = {"timestamp": ts}
            stock_by_ts[ts] = {"timestamp": ts}
        # Sum across sectors for same resource at same timestamp
        usage_by_ts[ts][rname] = usage_by_ts[ts].get(rname, 0) + level.usage
        stock_by_ts[ts][rname] = stock_by_ts[ts].get(rname, 0) + level.stock_level

    categories = list(resource_map.values())

    # Sample to max 50 data points for chart performance
    usage_data = list(usage_by_ts.values())
    stock_data = list(stock_by_ts.values())
    if len(usage_data) > 50:
        step = len(usage_data) // 50
        usage_data = usage_data[::step]
        stock_data = stock_data[::step]

    return {
        "resourceCount": resource_count,
        "daysRemaining": days_remaining,
        "resources": resource_list[:5],
        "reports": report_list,
        "usageChart": {
            "categories": categories,
            "data": usage_data,
        },
        "stockChart": {
            "categories": categories,
            "data": stock_data,
        },
    }
