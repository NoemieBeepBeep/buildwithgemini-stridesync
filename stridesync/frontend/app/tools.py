# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from google.cloud import firestore

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-b759b63b7250")

def _get_db():
    return firestore.Client(project=PROJECT_ID)

def check_consent_status(user_id: str = "default_user") -> Dict[str, Any]:
    """Checks user consent status, onboarding step, and profile summaries."""
    try:
        db = _get_db()
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            data = doc.to_dict() or {}
            return {
                "consent_granted": data.get("consent_granted", False),
                "google_health_connected": data.get("google_health_connected", False),
                "profile": data.get("profile", {}),
                "onboarding_completed": data.get("onboarding_completed", False),
                "has_profile": "profile" in data
            }
        return {
            "consent_granted": False,
            "google_health_connected": False,
            "profile": {},
            "onboarding_completed": False,
            "has_profile": False
        }
    except Exception as e:
        return {"error": str(e), "consent_granted": False}

def record_consent(user_id: str = "default_user", consent_granted: bool = True) -> Dict[str, Any]:
    """Records the user's explicit upfront consent decision."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        payload = {
            "consent_granted": consent_granted,
            "consent_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        user_ref.set(payload, merge=True)
        return {
            "status": "success",
            "consent_granted": consent_granted,
            "message": "Consent recorded." if consent_granted else "Consent declined. Data collection paused."
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def save_user_profile(
    user_id: str = "default_user",
    running_goal: str = "mental wellbeing",
    weekly_days: int = 3,
    walking_baseline: str = "Moderate (4,000–8,000 steps/day)",
    running_baseline: str = "Complete Beginner / Not running yet",
    health_notes: Optional[str] = None,
    life_stage: Optional[str] = None,
    last_period_date: Optional[str] = None,
    period_discovery_mode: bool = False,
    has_indoor_gym: bool = True,
    city_name: Optional[str] = "Hong Kong"
) -> Dict[str, Any]:
    """Saves running goals, 1-7 weekly days, separate walking & running baselines, cycle/period mode, gym, and city."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists or not doc.to_dict().get("consent_granted", False):
            return {"status": "blocked", "message": "Consent required before saving profile."}
        
        existing = doc.to_dict().get("profile", {})
        profile_data = {
            "running_goal": running_goal or existing.get("running_goal", "mental wellbeing"),
            "weekly_days": weekly_days or existing.get("weekly_days", 3),
            "walking_baseline": walking_baseline or existing.get("walking_baseline", "Moderate (4,000–8,000 steps/day)"),
            "running_baseline": running_baseline or existing.get("running_baseline", "Complete Beginner / Not running yet"),
            "health_notes": health_notes if health_notes is not None else existing.get("health_notes"),
            "life_stage": life_stage if life_stage is not None else existing.get("life_stage"),
            "last_period_date": last_period_date if last_period_date is not None else existing.get("last_period_date"),
            "period_discovery_mode": period_discovery_mode if period_discovery_mode is not None else existing.get("period_discovery_mode", False),
            "has_indoor_gym": has_indoor_gym if has_indoor_gym is not None else existing.get("has_indoor_gym", True),
            "city_name": (city_name or "Hong Kong").strip() if city_name is not None else existing.get("city_name", "Hong Kong"),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        user_ref.set({"profile": profile_data, "onboarding_completed": True}, merge=True)
        return {"status": "success", "profile": profile_data}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def sync_google_health_demo(user_id: str = "default_user", connect: bool = True) -> Dict[str, Any]:
    """Imports or syncs 14-day dummy Google Health dataset (Step 4)."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists or not doc.to_dict().get("consent_granted", False):
            return {"status": "blocked", "message": "Consent required."}
        
        if not connect:
            user_ref.set({"google_health_connected": False}, merge=True)
            return {"status": "success", "google_health_connected": False, "message": "Google Health sync skipped / disconnected."}

        dummy_path = Path(__file__).parent / "dummy_google_health_profile.json"
        with open(dummy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        user_ref.set({
            "google_health_connected": True,
            "google_health_metrics": data.get("user_metrics", {}),
            "last_google_health_sync": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }, merge=True)
        
        # Save activities into workout_logs subcollection
        activities = data.get("activities_last_14_days", [])
        for act in activities:
            user_ref.collection("workout_logs").document(act["id"]).set(act, merge=True)
            
        return {
            "status": "success",
            "google_health_connected": True,
            "synced_activities_count": len(activities),
            "metrics": data.get("user_metrics", {}),
            "message": f"Successfully synced {len(activities)} activities and health metrics from Google Health."
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def log_manual_workout(
    user_id: str = "default_user",
    workout_type: str = "Run",
    duration_minutes: int = 20,
    distance_km: Optional[float] = None,
    rpe: int = 5,
    feeling_notes: str = ""
) -> Dict[str, Any]:
    """Logs a manual walk or run workout entry."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists or not doc.to_dict().get("consent_granted", False):
            return {"status": "blocked", "message": "Consent required."}
            
        act_id = f"manual_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
        today_str = datetime.date.today().isoformat()
        workout = {
            "id": act_id,
            "date": today_str,
            "type": workout_type,
            "duration_minutes": duration_minutes,
            "distance_km": distance_km,
            "rpe": rpe,
            "feeling_notes": feeling_notes,
            "source": "Manual Entry",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        user_ref.collection("workout_logs").document(act_id).set(workout)
        return {"status": "success", "workout": workout}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def save_session_context(user_id: str = "default_user", daily_feeling: str = "normal", notes: str = "") -> Dict[str, Any]:
    """Logs daily mindful check-in context (cramps, mood, fatigue, sleep)."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        doc = user_ref.get()
        if not doc.exists or not doc.to_dict().get("consent_granted", False):
            return {"status": "blocked", "message": "Consent required."}
            
        today_str = datetime.date.today().isoformat()
        log_payload = {
            "date": today_str,
            "category": "symptoms_and_mood",
            "daily_feeling": daily_feeling,
            "notes": notes,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        user_ref.collection("checkin_logs").document(today_str).set(log_payload, merge=True)
        return {"status": "success", "log": log_payload}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def get_user_dashboard_data(user_id: str = "default_user") -> Dict[str, Any]:
    """Fetches user profile, recent activities, and metrics for the dashboard."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return {"consent_granted": False, "activities": [], "profile": {}}
            
        user_data = user_doc.to_dict() or {}
        
        # Fetch workout logs
        workout_docs = user_ref.collection("workout_logs").order_by("date", direction=firestore.Query.DESCENDING).limit(10).stream()
        activities = [w.to_dict() for w in workout_docs]
        
        # Fetch latest check-in
        checkin_docs = user_ref.collection("checkin_logs").order_by("date", direction=firestore.Query.DESCENDING).limit(1).stream()
        latest_checkin = None
        for c in checkin_docs:
            latest_checkin = c.to_dict()
            break
            
        return {
            "consent_granted": user_data.get("consent_granted", False),
            "google_health_connected": user_data.get("google_health_connected", False),
            "google_health_metrics": user_data.get("google_health_metrics", {}),
            "profile": user_data.get("profile", {}),
            "onboarding_completed": user_data.get("onboarding_completed", False),
            "activities": activities,
            "latest_checkin": latest_checkin,
            "total_activities": len(activities)
        }
    except Exception as e:
        return {"error": str(e), "activities": [], "profile": {}}

def delete_user_data(
    user_id: str = "default_user",
    mode: str = "all",
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Granular user data deletion: all, by_category, by_date_range, or disconnect_google_health."""
    try:
        db = _get_db()
        user_ref = db.collection("users").document(user_id)
        
        if mode == "disconnect_google_health":
            user_ref.update({
                "google_health_connected": False,
                "google_health_metrics": firestore.DELETE_FIELD,
                "last_google_health_sync": firestore.DELETE_FIELD
            })
            synced = user_ref.collection("workout_logs").where("source", "==", "Google Health Sync").stream()
            c = 0
            for s in synced:
                s.reference.delete()
                c += 1
            return {"status": "success", "mode": "disconnect_google_health", "message": f"Disconnected Google Health and removed {c} synced entries."}

        elif mode == "all":
            for w in user_ref.collection("workout_logs").stream():
                w.reference.delete()
            for ch in user_ref.collection("checkin_logs").stream():
                ch.reference.delete()
            user_ref.delete()
            return {"status": "success", "mode": "all", "message": "All user data, health syncs, logs, and profile completely wiped from Firestore."}

        elif mode == "by_category":
            if category == "profile":
                user_ref.update({"profile": firestore.DELETE_FIELD})
                return {"status": "success", "mode": "by_category", "message": "Profile and goals cleared."}
            elif category in ("checkin_logs", "symptoms_and_mood"):
                c = 0
                for ch in user_ref.collection("checkin_logs").stream():
                    ch.reference.delete()
                    c += 1
                return {"status": "success", "mode": "by_category", "message": f"Deleted {c} check-in symptom/mood records."}
            elif category == "workout_logs":
                c = 0
                for w in user_ref.collection("workout_logs").stream():
                    w.reference.delete()
                    c += 1
                return {"status": "success", "mode": "by_category", "message": f"Deleted {c} workout entries."}
            else:
                return {"status": "error", "message": f"Unknown category: {category}"}

        elif mode == "by_date_range":
            deleted_count = 0
            for col in ["workout_logs", "checkin_logs"]:
                for doc in user_ref.collection(col).stream():
                    d = doc.to_dict().get("date")
                    if d:
                        if start_date and d < start_date:
                            continue
                        if end_date and d > end_date:
                            continue
                        doc.reference.delete()
                        deleted_count += 1
            return {"status": "success", "mode": "by_date_range", "message": f"Deleted {deleted_count} entries between {start_date} and {end_date}."}

        else:
            return {"status": "error", "message": f"Unknown mode: {mode}"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}
