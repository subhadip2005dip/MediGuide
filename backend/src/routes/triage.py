from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import json
import math
import httpx
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from ..database.db import get_db
from ..models.models import SymptomReport

load_dotenv()

router = APIRouter()
llm_client = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

TRIAGE_SYSTEM_PROMPT = """
You are a clinical triage AI assistant for travelers. You receive symptom intake data
and produce a structured medical assessment.

Output ONLY a valid JSON object — no extra text, no markdown:

{
  "severity_score": 6,
  "urgency_label": "medium",
  "recommended_specialty": "General Physician",
  "triage_reason": "Patient has moderate fever and body ache for 2 days.",
  "translated_summary": "Summary in English regardless of input language",
  "red_flags": [],
  "follow_up_questions": [],
  "estimated_visit_type": "in-person",
  "confidence_score": 0.85,
  "confidence_reason": "Clear symptom description with duration provided",
  "age_gender_note": "No age/gender factors affected scoring"
}

═══ SEVERITY SCORE GUIDE ═══
1-3   → Low       → urgency_label: "low"
4-6   → Medium    → urgency_label: "medium"
7-9   → High      → urgency_label: "high"
10    → Emergency → urgency_label: "emergency"

═══ SPECIALTY MAPPING ═══
Fever, cold, general illness     → General Physician
Chest pain, heart concerns       → Cardiologist
Broken bone, injury              → Orthopedic
Eye problems                     → Ophthalmologist
Skin issues                      → Dermatologist
Stomach, digestion               → Gastroenterologist
Mental health                    → Psychiatrist
Children under 12                → Pediatrician
Severe/multi-system/unclear      → Emergency Medicine
Dental pain                      → Dentist
Pregnancy related                → Gynecologist

═══ VISIT TYPE ═══
telemedicine   → severity 1-3, no red flags
in-person      → severity 4-8
emergency-room → severity 9-10

═══ CONFIDENCE SCORE (0.0 to 1.0) ═══
0.9-1.0 → Very clear symptoms, duration known, complete info
0.7-0.8 → Good info but minor gaps (e.g., no duration)
0.5-0.6 → Vague symptoms, incomplete data, borderline case
0.0-0.4 → Very unclear, missing critical info

═══ AGE/GENDER ADJUSTMENTS ═══
- Child under 5 with fever → +1 severity, use Pediatrician
- Elderly (65+) with chest pain → +1 severity, escalate faster
- Pregnant woman with abdominal pain → always Gynecologist + red_flag
- Male 40+ with chest/jaw/arm pain → red_flag: possible cardiac
- Child with high fever (>103F) → red_flag: febrile seizure risk

═══ RED FLAGS (auto-escalate to high/emergency) ═══
- Chest tightness or chest pain
- Difficulty breathing or shortness of breath
- Sudden severe headache ("worst of my life")
- Confusion, loss of consciousness
- High fever 104F+ (40C+)
- Vomiting blood or black stools
- Severe allergic reaction signs
- Pregnancy with bleeding or severe pain

Output ONLY the JSON. No explanation.
"""

SECOND_OPINION_PROMPT = """
You are a senior clinical triage reviewer. A first triage assessment returned a
borderline severity score of 5 or 6. Review the case and provide a second opinion.

Output ONLY a valid JSON:
{
  "second_opinion_score": 6,
  "agrees_with_first": true,
  "adjustment_reason": "First assessment was accurate. No additional red flags found.",
  "final_recommended_specialty": "General Physician",
  "escalate": false
}

Be conservative — if in doubt, escalate (set escalate: true and raise score by 1).
"""

ESCALATION_PATHS = {
    "emergency": {
        "action": "CALL_EMERGENCY",
        "message": "🚨 Call 112 immediately or go to nearest Emergency Room.",
        "skip_booking": True,
        "notify_hotel": True
    },
    "high": {
        "action": "PRIORITY_BOOKING",
        "message": "⚠️ High priority — booking earliest available emergency slot.",
        "skip_booking": False,
        "notify_hotel": False
    },
    "medium": {
        "action": "STANDARD_BOOKING",
        "message": "📋 Booking standard appointment.",
        "skip_booking": False,
        "notify_hotel": False
    },
    "low": {
        "action": "TELEMEDICINE_OR_BOOKING",
        "message": "💬 Telemedicine consultation recommended.",
        "skip_booking": False,
        "notify_hotel": False
    }
}

RED_FLAG_KEYWORDS = [
    "chest pain", "chest tightness", "can't breathe", "difficulty breathing",
    "shortness of breath", "unconscious", "confusion", "worst headache",
    "vomiting blood", "severe allergic", "stroke", "seizure", "104f", "40c"
]

SEVERITY_COLORS = {
    "low": "green",
    "medium": "yellow",
    "high": "orange",
    "emergency": "red",
}

class TriageRequest(BaseModel):
    symptoms: str
    latitude: float
    longitude: float
    language: Optional[str] = "en"
    radius_meters: Optional[int] = 10000
    age: Optional[int] = None
    gender: Optional[str] = None


class HospitalResult(BaseModel):
    place_id: str
    name: str
    address: str
    phone: Optional[str]
    rating: Optional[float]
    distance_km: float
    open_now: Optional[bool]
    match_score: float
    match_reason: str
    google_maps_url: str


class TriageResponse(BaseModel):
    report_id: int
    severity: str
    severity_score: int
    severity_color: str
    urgency_label: str
    recommended_specialty: str
    ai_summary: str
    action_advice: str
    symptom_card: str
    confidence_score: float
    confidence_reason: str
    red_flags: list[str]
    estimated_visit_type: str
    escalation_action: str
    escalation_message: str
    hospitals: list[HospitalResult]
    emergency_call_advised: bool
    total_hospitals_found: int


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def check_red_flags_in_text(text: str) -> list:
    found = []
    text_lower = text.lower()
    for flag in RED_FLAG_KEYWORDS:
        if flag in text_lower:
            found.append(flag)
    return found


def apply_age_gender_adjustment(triage_result: dict, age: int = None, gender: str = None) -> dict:
    if age is None:
        return triage_result

    original_score = triage_result["severity_score"]
    specialty = triage_result["recommended_specialty"]
    red_flags = triage_result.get("red_flags", [])
    notes = []

    if age < 5 and "fever" in triage_result.get("translated_summary", "").lower():
        triage_result["severity_score"] = min(original_score + 1, 10)
        triage_result["recommended_specialty"] = "Pediatrician"
        notes.append("Child under 5 with fever — severity increased, redirected to Pediatrician")

    elif age >= 65 and specialty == "Cardiologist":
        triage_result["severity_score"] = min(original_score + 1, 10)
        red_flags.append("elderly patient with cardiac symptoms")
        notes.append("Elderly patient with cardiac concern — severity increased")

    elif gender == "female" and specialty == "Gynecologist":
        red_flags.append("pregnancy-related abdominal concern")
        notes.append("Pregnant patient — added red flag for monitoring")

    elif gender == "male" and age >= 40 and "Cardiologist" in specialty:
        red_flags.append("male 40+ with possible cardiac symptoms")
        notes.append("Male 40+ with cardiac symptoms — added red flag")

    if notes:
        triage_result["age_gender_adjustments"] = notes
        triage_result["red_flags"] = red_flags

    return triage_result


def apply_escalation(triage_result: dict, python_red_flags: list) -> dict:
    if python_red_flags and triage_result["severity_score"] < 8:
        triage_result["severity_score"] = max(triage_result["severity_score"], 8)
        triage_result["urgency_label"] = "high"
        triage_result["red_flags"] = list(set(
            triage_result.get("red_flags", []) + python_red_flags
        ))
        triage_result["escalation_override"] = True

    urgency = triage_result["urgency_label"]
    triage_result["escalation"] = ESCALATION_PATHS.get(urgency, ESCALATION_PATHS["medium"])
    return triage_result


class TriageAgent:
    """Agentic triage system with escalation, age/gender adjustments, and second opinion."""

    def __init__(self):
        self.llm = llm_client

    def _call_llm(self, prompt: str, system: str) -> str:
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        raw = response.content
        if isinstance(raw, list):
            raw = raw[0].get("text", "") if isinstance(raw[0], dict) else str(raw[0])
        return raw.strip()

    def _parse_json(self, raw: str) -> dict:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def _get_second_opinion(self, symptoms: str, first_result: dict) -> dict:
        prompt = f"""
First triage result:
{json.dumps(first_result, indent=2)}

Original symptoms: {symptoms}

Provide your second opinion now.
"""
        try:
            raw = self._call_llm(prompt, SECOND_OPINION_PROMPT)
            second = self._parse_json(raw)
            if second.get("escalate") or second.get("second_opinion_score", 5) > first_result.get("severity_score", 5):
                first_result["severity_score"] = second.get("second_opinion_score", first_result.get("severity_score"))
                first_result["urgency_label"] = (
                    "high" if first_result["severity_score"] >= 7
                    else "medium" if first_result["severity_score"] >= 4
                    else "low"
                )
                first_result["recommended_specialty"] = second.get(
                    "final_recommended_specialty",
                    first_result["recommended_specialty"]
                )
            first_result["second_opinion"] = second
        except Exception:
            pass  # Keep original score if second opinion fails
        return first_result

    def assess(self, symptoms: str, language: str = "en", age: int = None, gender: str = None) -> dict:
        python_red_flags = check_red_flags_in_text(symptoms)

        age_context = f"Age: {age}" if age else "Age: not provided"
        gender_context = f"Gender: {gender}" if gender else "Gender: not provided"

        prompt = f"""
Perform triage assessment for the following traveler medical intake:

{age_context}
{gender_context}
Patient language preference: {language}
Symptoms: {symptoms}

Produce the triage JSON now.
"""
        try:
            raw = self._call_llm(prompt, TRIAGE_SYSTEM_PROMPT)
            triage_result = self._parse_json(raw)
        except Exception:
            triage_result = {
                "severity_score": 5,
                "urgency_label": "medium",
                "recommended_specialty": "General Physician",
                "triage_reason": "Assessment failed — defaulting to medium severity",
                "translated_summary": symptoms,
                "red_flags": python_red_flags,
                "follow_up_questions": [],
                "estimated_visit_type": "in-person",
                "confidence_score": 0.2,
                "confidence_reason": "LLM assessment failed — low confidence fallback",
                "age_gender_note": "Not assessed"
            }

        triage_result = apply_age_gender_adjustment(triage_result, age, gender)
        triage_result = apply_escalation(triage_result, python_red_flags)

        if triage_result.get("severity_score") in (5, 6):
            triage_result = self._get_second_opinion(symptoms, triage_result)

        triage_result["language"] = language
        triage_result["assessed_age"] = age
        triage_result["assessed_gender"] = gender

        return triage_result


async def fetch_nearby_hospitals(lat: float, lng: float, radius_meters: int) -> list[dict]:
    if not GOOGLE_PLACES_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_PLACES_API_KEY not set in .env")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_meters,
        "type": "hospital",
        "key": GOOGLE_PLACES_API_KEY,
    }

    async with httpx.AsyncClient(timeout=10) as http:
        response = await http.get(url, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Places API request failed")

    data = response.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(
            status_code=502,
            detail=f"Google Places error: {data.get('status')} — {data.get('error_message', '')}"
        )

    results = []
    for place in data.get("results", []):
        loc = place.get("geometry", {}).get("location", {})
        results.append({
            "place_id": place.get("place_id", ""),
            "name": place.get("name", "Unknown"),
            "address": place.get("vicinity", ""),
            "latitude": loc.get("lat"),
            "longitude": loc.get("lng"),
            "rating": place.get("rating"),
            "open_now": place.get("opening_hours", {}).get("open_now"),
            "types": place.get("types", []),
        })

    return results


async def fetch_place_phone(place_id: str) -> Optional[str]:
    if not GOOGLE_PLACES_API_KEY or not place_id:
        return None
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number",
        "key": GOOGLE_PLACES_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as http:
            response = await http.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("result", {}).get("formatted_phone_number")
    except Exception:
        pass
    return None


@router.post("/", response_model=TriageResponse)
async def triage(request: TriageRequest, db: AsyncSession = Depends(get_db)):
    agent = TriageAgent()

    triage_assessment, nearby_hospitals = await asyncio.gather(
        asyncio.to_thread(
            agent.assess,
            symptoms=request.symptoms,
            language=request.language,
            age=request.age,
            gender=request.gender,
        ),
        fetch_nearby_hospitals(request.latitude, request.longitude, request.radius_meters),
    )

    if not nearby_hospitals:
        raise HTTPException(
            status_code=404,
            detail="No hospitals found within the search radius. Try increasing radius_meters."
        )

    urgency_label = triage_assessment.get("urgency_label", "medium")
    severity_score = triage_assessment.get("severity_score", 5)

    scored = []
    for h in nearby_hospitals:
        score = 0.0
        reason_parts = []

        dist = haversine_distance(request.latitude, request.longitude, h["latitude"], h["longitude"])
        dist_score = max(0, 1 - (dist / (request.radius_meters / 1000)))
        score += dist_score * 35
        reason_parts.append(f"{dist} km away")

        if h.get("rating"):
            score += h["rating"] * 5
            reason_parts.append(f"rated {h['rating']}/5")

        if h.get("open_now") is True:
            score += 15
            reason_parts.append("open now")
        elif h.get("open_now") is False:
            score -= 20

        place_types = h.get("types", [])
        if "hospital" in place_types:
            score += 10
        if severity_score >= 8 and "emergency" in place_types:
            score += 20

        scored.append({
            **h,
            "distance_km": dist,
            "score": round(score, 2),
            "reason": ", ".join(reason_parts),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top5 = scored[:5]

    phones = await asyncio.gather(*[fetch_place_phone(h["place_id"]) for h in top5])

    report = SymptomReport(
        symptoms_raw=request.symptoms,
        triage_result=json.dumps(triage_assessment),
        severity=urgency_label,
        recommended_specialty=triage_assessment.get("recommended_specialty", "General Physician"),
        user_latitude=request.latitude,
        user_longitude=request.longitude,
        user_language=request.language,
        created_at=datetime.utcnow(),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    hospital_results = [
        HospitalResult(
            place_id=h["place_id"],
            name=h["name"],
            address=h["address"],
            phone=phone,
            rating=h.get("rating"),
            distance_km=h["distance_km"],
            open_now=h.get("open_now"),
            match_score=h["score"],
            match_reason=h["reason"],
            google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{h['place_id']}",
        )
        for h, phone in zip(top5, phones)
    ]

    escalation = triage_assessment.get("escalation", ESCALATION_PATHS["medium"])

    return TriageResponse(
        report_id=report.id,
        severity=urgency_label,
        severity_score=severity_score,
        severity_color=SEVERITY_COLORS.get(urgency_label, "yellow"),
        urgency_label=urgency_label,
        recommended_specialty=triage_assessment.get("recommended_specialty", "General Physician"),
        ai_summary=triage_assessment.get("translated_summary", ""),
        action_advice=triage_assessment.get("triage_reason", ""),
        symptom_card=triage_assessment.get("triage_reason", ""),
        confidence_score=triage_assessment.get("confidence_score", 0.5),
        confidence_reason=triage_assessment.get("confidence_reason", ""),
        red_flags=triage_assessment.get("red_flags", []),
        estimated_visit_type=triage_assessment.get("estimated_visit_type", "in-person"),
        escalation_action=escalation.get("action", "STANDARD_BOOKING"),
        escalation_message=escalation.get("message", "Standard appointment booking"),
        hospitals=hospital_results,
        emergency_call_advised=severity_score >= 8,
        total_hospitals_found=len(nearby_hospitals),
    )
