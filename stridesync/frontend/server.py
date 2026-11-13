# ruff: noqa
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Add stridesync root to path so we can import app modules directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import root_agent
from app.weather import fetch_city_weather
from app.tools import (
    check_consent_status,
    record_consent,
    save_user_profile,
    sync_google_health_demo,
    log_manual_workout,
    save_session_context,
    get_user_dashboard_data,
    delete_user_data,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

app = FastAPI(title="StrideSync Mindful Run Coach")

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
active_sessions: Dict[str, str] = {}

class ChatRequest(BaseModel):
    user_id: str = "default_user"
    message: str

class ConsentRequest(BaseModel):
    user_id: str = "default_user"
    consent: bool

class ProfileRequest(BaseModel):
    user_id: str = "default_user"
    running_goal: str
    weekly_days: int
    walking_baseline: str = "Moderate (4,000–8,000 steps/day)"
    running_baseline: str = "Complete Beginner / Not running yet"
    health_notes: Optional[str] = None
    life_stage: Optional[str] = None
    last_period_date: Optional[str] = None
    period_discovery_mode: bool = False
    has_indoor_gym: bool = True
    city_name: Optional[str] = "Hong Kong"

class HealthSyncRequest(BaseModel):
    user_id: str = "default_user"
    connect: bool

class ManualWorkoutRequest(BaseModel):
    user_id: str = "default_user"
    workout_type: str = "Run"
    duration_minutes: int = 20
    distance_km: Optional[float] = None
    rpe: int = 5
    feeling_notes: str = ""

class CheckinRequest(BaseModel):
    user_id: str = "default_user"
    daily_feeling: str
    notes: str = ""

class DeleteRequest(BaseModel):
    user_id: str = "default_user"
    mode: str = "all"
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str, demo_weather: Optional[str] = None):
    data = get_user_dashboard_data(user_id)
    profile = data.get("profile", {})
    city = profile.get("city_name", "Hong Kong")
    
    # Fetch real-time current + 7-day daily forecast
    weather_info = await fetch_city_weather(city_name=city, demo_override=demo_weather)
    data["weather"] = weather_info.get("current", {})
    data["daily_forecast"] = weather_info.get("daily_forecast", [])
    return JSONResponse(content=data)

@app.get("/api/weather")
async def get_weather(city: Optional[str] = "Hong Kong", demo_weather: Optional[str] = None):
    weather_info = await fetch_city_weather(city_name=city, demo_override=demo_weather)
    return JSONResponse(content=weather_info)

@app.post("/api/consent")
async def handle_consent(req: ConsentRequest):
    res = record_consent(user_id=req.user_id, consent_granted=req.consent)
    return JSONResponse(content=res)

@app.post("/api/profile")
async def handle_profile(req: ProfileRequest):
    res = save_user_profile(
        user_id=req.user_id,
        running_goal=req.running_goal,
        weekly_days=req.weekly_days,
        walking_baseline=req.walking_baseline,
        running_baseline=req.running_baseline,
        health_notes=req.health_notes,
        life_stage=req.life_stage,
        last_period_date=req.last_period_date,
        period_discovery_mode=req.period_discovery_mode,
        has_indoor_gym=req.has_indoor_gym,
        city_name=req.city_name
    )
    return JSONResponse(content=res)

@app.post("/api/sync-health")
async def handle_health_sync(req: HealthSyncRequest):
    res = sync_google_health_demo(user_id=req.user_id, connect=req.connect)
    return JSONResponse(content=res)

@app.post("/api/workout/manual")
async def handle_manual_workout(req: ManualWorkoutRequest):
    res = log_manual_workout(
        user_id=req.user_id,
        workout_type=req.workout_type,
        duration_minutes=req.duration_minutes,
        distance_km=req.distance_km,
        rpe=req.rpe,
        feeling_notes=req.feeling_notes
    )
    return JSONResponse(content=res)

@app.post("/api/checkin")
async def handle_checkin(req: CheckinRequest):
    res = save_session_context(
        user_id=req.user_id,
        daily_feeling=req.daily_feeling,
        notes=req.notes
    )
    return JSONResponse(content=res)

@app.post("/api/delete-data")
async def handle_delete(req: DeleteRequest):
    res = delete_user_data(
        user_id=req.user_id,
        mode=req.mode,
        category=req.category,
        start_date=req.start_date,
        end_date=req.end_date
    )
    return JSONResponse(content=res)

@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    user_id = req.user_id
    if user_id not in active_sessions:
        session = await session_service.create_session(app_name="app", user_id=user_id)
        active_sessions[user_id] = session.id
    session_id = active_sessions[user_id]
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=req.message)])
    text_replies = []
    
    try:
        async for event in runner.run_async(session_id=session_id, user_id=user_id, new_message=content):
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        text_replies.append(p.text)
        
        reply = "".join(text_replies)
        return JSONResponse(content={"reply": reply, "user_id": user_id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8090, reload=False)
