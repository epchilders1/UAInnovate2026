from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import create_db, get_session
from models import Hero, Sector, Resource, SectorResource, ResourceStockLevel, Report, User, UserSession
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
