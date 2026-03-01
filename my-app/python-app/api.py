from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from sqlalchemy import func, desc
from database import create_db, get_session
from models import Hero, Sector, Resource, SectorResource, ResourceStockLevel, Report, Priority, User, UserSession
from jarvis import Jarvis, openai_client
from config import Config
from pydantic import BaseModel
from typing import List, Optional
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

@app.get("/reports/{report_id}")
def get_report(report_id: int, session: Session = Depends(get_session)):
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    priority_names = {0: "Routine", 1: "High", 2: "Avengers Level Threat"}
    return {
        "id": report.id,
        "rawText": report.raw_text,
        "timestamp": report.timestamp.isoformat(),
        "priority": priority_names.get(report.priority, "Routine"),
        "heroAlias": report.hero.alias if report.hero else None,
        "heroContact": report.hero.contact if report.hero else None,
        "resource": report.resource.resource_name if report.resource else None,
        "sector": report.sector.sector_name if report.sector else None,
    }

class CreateReportRequest(BaseModel):
    raw_text: str
    hero_id: int
    priority: int

@app.post("/reports")
async def create_report(body: CreateReportRequest, session: Session = Depends(get_session)):
    # Convert ORM objects to plain dicts before the await — SQLAlchemy expires
    # ORM objects after async suspension, causing their attributes to read as None.
    sector_data = [{"id": s.id, "name": s.sector_name} for s in session.exec(select(Sector)).all()]
    resource_data = [{"id": r.id, "name": r.resource_name} for r in session.exec(select(Resource)).all()]

    sector_names = [s["name"] for s in sector_data]
    resource_names = [r["name"] for r in resource_data]

    prompt = (
        f"You are analyzing a field report to extract the most relevant sector and resource.\n"
        f"Available sectors: {sector_names}\n"
        f"Available resources: {resource_names}\n"
        f"Report: {body.raw_text}\n\n"
        f"Respond with a JSON object with exactly two keys: \"sector\" and \"resource\", "
        f"using the exact names from the lists above. Pick the closest match if not explicitly stated."
    )

    ai_response = await openai_client.chat.completions.create(
        model=Config.MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    extracted = json.loads(ai_response.choices[0].message.content or "{}")
    sector_name = extracted.get("sector", sector_names[0] if sector_names else "")
    resource_name = extracted.get("resource", resource_names[0] if resource_names else "")

    matched_sector = next((s for s in sector_data if s["name"] == sector_name), sector_data[0] if sector_data else None)
    matched_resource = next((r for r in resource_data if r["name"] == resource_name), resource_data[0] if resource_data else None)

    if not matched_sector or not matched_resource:
        raise HTTPException(status_code=400, detail="Could not resolve sector or resource")

    report = Report(
        raw_text=body.raw_text,
        hero_id=body.hero_id,
        priority=body.priority,
        sector_id=matched_sector["id"],
        resource_id=matched_resource["id"],
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return {
        "id": report.id,
        "sector": matched_sector["name"],
        "resource": matched_resource["name"],
    }


# --- Dashboard ---

@app.get("/api/dashboard")
def get_dashboard(
    session: Session = Depends(get_session),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    date_filtered = start_date is not None or end_date is not None
    start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59) if end_date else None

    # Resource count
    resources = session.exec(select(Resource)).all()
    resource_count = len(resources)
    resource_map = {r.id: r.resource_name for r in resources}

    # Get all sector_resources to map sector_resource_id -> resource_name
    sector_resources = session.exec(select(SectorResource)).all()
    sr_to_resource = {sr.id: resource_map.get(sr.resource_id, "Unknown") for sr in sector_resources}

    # Get latest stock level and average usage per resource (within date range)
    resource_stats = {}
    for sr in sector_resources:
        rname = sr_to_resource[sr.id]
        levels_query = (
            select(ResourceStockLevel)
            .where(ResourceStockLevel.sector_resource_id == sr.id)
            .order_by(desc(ResourceStockLevel.timestamp))
        )
        if start_dt:
            levels_query = levels_query.where(ResourceStockLevel.timestamp >= start_dt)
        if end_dt:
            levels_query = levels_query.where(ResourceStockLevel.timestamp <= end_dt)
        levels = session.exec(levels_query).all()
        if not levels:
            continue
        latest_stock = levels[0].stock_level
        avg_usage = sum(l.usage for l in levels) / len(levels) if levels else 0
        if rname not in resource_stats:
            resource_stats[rname] = {"stockLevel": 0, "usage": 0, "count": 0}
        resource_stats[rname]["stockLevel"] += latest_stock
        resource_stats[rname]["usage"] += avg_usage
        resource_stats[rname]["count"] += 1

    # Build resource list
    resource_list = []
    for name, stats in resource_stats.items():
        avg_usage = stats["usage"] / stats["count"] if stats["count"] else 0
        stock = stats["stockLevel"]
        resource_list.append({
            "name": name,
            "stockLevel": round(stock, 1),
            "usage": round(avg_usage, 2),
        })

    days_remaining = 5

    # Get 5 most recent reports with hero alias (within date range)
    reports_query = (
        select(Report, Hero)
        .join(Hero, Report.hero_id == Hero.id)
        .order_by(desc(Report.timestamp))
    )
    if start_dt:
        reports_query = reports_query.where(Report.timestamp >= start_dt)
    if end_dt:
        reports_query = reports_query.where(Report.timestamp <= end_dt)
    reports_query = reports_query.limit(5)
    report_rows = session.exec(reports_query).all()
    priority_names = {0: "Routine", 1: "High", 2: "Avengers Level Threat"}
    report_list = [
        {
            "id": report.id,
            "heroAlias": hero.alias,
            "timestamp": report.timestamp.isoformat(),
            "priority": priority_names.get(report.priority, "Routine"),
        }
        for report, hero in report_rows
    ]

    # Build chart time series data (within date range)
    all_levels_query = select(ResourceStockLevel).order_by(ResourceStockLevel.timestamp)
    if start_dt:
        all_levels_query = all_levels_query.where(ResourceStockLevel.timestamp >= start_dt)
    if end_dt:
        all_levels_query = all_levels_query.where(ResourceStockLevel.timestamp <= end_dt)
    all_levels = session.exec(all_levels_query).all()

    usage_by_ts = {}
    stock_by_ts = {}
    count_by_ts = {}
    for level in all_levels:
        rname = sr_to_resource.get(level.sector_resource_id, "Unknown")
        ts = level.timestamp.strftime("%Y-%m-%d %H:%M")
        if ts not in usage_by_ts:
            usage_by_ts[ts] = {"timestamp": ts}
            stock_by_ts[ts] = {"timestamp": ts}
            count_by_ts[ts] = {}
        usage_by_ts[ts][rname] = usage_by_ts[ts].get(rname, 0) + level.usage
        stock_by_ts[ts][rname] = stock_by_ts[ts].get(rname, 0) + level.stock_level
        count_by_ts[ts][rname] = count_by_ts[ts].get(rname, 0) + 1

    # Average across sectors for same resource at same timestamp
    for ts in usage_by_ts:
        for rname in count_by_ts[ts]:
            n = count_by_ts[ts][rname]
            if n > 1:
                usage_by_ts[ts][rname] /= n
                stock_by_ts[ts][rname] /= n

    # Compute overall min/max dates from all stock levels (unfiltered)
    all_timestamps = session.exec(select(ResourceStockLevel.timestamp)).all()
    if all_timestamps:
        min_date = min(all_timestamps).strftime("%Y-%m-%d")
        max_date = max(all_timestamps).strftime("%Y-%m-%d")
    else:
        min_date = None
        max_date = None

    categories = list(resource_map.values())

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
        "minDate": min_date,
        "maxDate": max_date,
        "usageChart": {
            "categories": categories,
            "data": usage_data,
        },
        "stockChart": {
            "categories": categories,
            "data": stock_data,
        },
    }
