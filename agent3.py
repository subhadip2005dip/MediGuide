
# AGENT 3: Nearest Hospital Finder Agent
# Finds the nearest hospital using REAL-TIME Google Places API (New)
# Supports radius + estimated travel time

import json
import math
import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not GOOGLE_PLACES_API_KEY:
    print("WARNING: GOOGLE_PLACES_API_KEY not found in .env - falling back to mock data only.")

# ── Original Mock as Fallback ───────────────────────────────────────────────
MOCK_HOSPITALS = [
    {
        "id": "hosp-001", "name": "Apollo Gleneagles Hospital",
        "address": "58 Canal Circular Rd, Kolkata, West Bengal 700054",
        "city": "Kolkata", "lat": 22.5726, "lon": 88.3639,
        "phone": "+91-33-2320-3040", "emergency_available": True,
        "rating": 4.6, "specialties": ["General", "Emergency", "Cardiology"]
    },
    {
        "id": "hosp-002", "name": "AMRI Hospital Salt Lake",
        "address": "JC Block, Salt Lake City, Kolkata, West Bengal 700098",
        "city": "Kolkata", "lat": 22.5904, "lon": 88.4005,
        "phone": "+91-33-2335-1234", "emergency_available": True,
        "rating": 4.4, "specialties": ["General", "Emergency"]
    },
    {
        "id": "hosp-003", "name": "Fortis Hospital Anandapur",
        "address": "730 Anandapur, EM Bypass, Kolkata, West Bengal 700107",
        "city": "Kolkata", "lat": 22.5150, "lon": 88.4040,
        "phone": "+91-33-6628-4444", "emergency_available": True,
        "rating": 4.7, "specialties": ["Emergency", "Cardiology", "Multi-specialty"]
    },
    {
        "id": "hosp-004", "name": "Ruby General Hospital",
        "address": "Kasba Golpark, E M Bypass, Kolkata, West Bengal 700107",
        "city": "Kolkata", "lat": 22.4995, "lon": 88.3920,
        "phone": "+91-33-3987-1800", "emergency_available": True,
        "rating": 4.3, "specialties": ["General", "Emergency"]
    },
    {
        "id": "hosp-005", "name": "Medica Superspecialty Hospital",
        "address": "127 Mukundapur, E.M. Bypass, Kolkata, West Bengal 700099",
        "city": "Kolkata", "lat": 22.4930, "lon": 88.4100,
        "phone": "+91-33-6652-0000", "emergency_available": True,
        "rating": 4.5, "specialties": ["Emergency", "Multi-specialty"]
    },
]

# Distance
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Hospital_searching tool
def search_hospitals(city: str, user_lat: float = None, user_lon: float = None, 
                     radius_km: float = 10.0) -> list:
    """
    Uses Google Places API Nearby Search (New) when coordinates are provided.
    Falls back to Text Search or mock data otherwise.
    """
    if not GOOGLE_PLACES_API_KEY:
        print("Using mock hospitals (API key missing)")
        return MOCK_HOSPITALS[:8]

    # Prefer Nearby Search if user location is available (most accurate for "nearest")
    if user_lat is not None and user_lon is not None:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        payload = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": user_lat, "longitude": user_lon},
                    "radius": int(radius_km * 1000)  # meters
                }
            },
            "includedTypes": ["hospital"],
            "maxResultCount": 12,
            "rankPreference": "DISTANCE"
        }
    else:
        # Fallback Text Search
        url = "https://places.googleapis.com/v1/places:searchText"
        payload = {
            "textQuery": f"hospitals in {city}",
            "maxResultCount": 10
        }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,"
                           "places.rating,places.internationalPhoneNumber,places.businessStatus,places.types"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()

        results = []
        for place in data.get("places", []):
            loc = place.get("location", {})
            hospital = {
                "id": place.get("id", f"hosp-google-{len(results)}"),
                "name": place.get("displayName", {}).get("text", "Unknown Hospital"),
                "address": place.get("formattedAddress", ""),
                "city": city,
                "lat": loc.get("latitude"),
                "lon": loc.get("longitude"),
                "phone": place.get("internationalPhoneNumber"),
                "emergency_available": True,   # Most hospitals support emergency
                "rating": place.get("rating", 4.0),
                "specialties": ["General", "Emergency"],
                "google_place_id": place.get("id")
            }

            if user_lat and user_lon and loc.get("latitude") and loc.get("longitude"):
                hospital["distance_km"] = round(
                    haversine_distance(user_lat, user_lon, loc["latitude"], loc["longitude"]), 2
                )

            results.append(hospital)

        if user_lat and user_lon:
            results.sort(key=lambda x: x.get("distance_km", 999))

        return results[:10]

    except Exception as e:
        print(f"[Google Places API Error] {e}. Falling back to mock data.")
        return MOCK_HOSPITALS[:8]

# ── Travel Time Estimator ─────────────────────────────────────────────────────
def estimate_travel_time(distance_km: float, urgency: str = "medium") -> dict:
    if urgency in ["high", "emergency"]:
        speed_kmh = 28   # Faster with priority
    else:
        speed_kmh = 18   # Normal Kolkata traffic

    minutes = round((distance_km / speed_kmh) * 60 * 1.15)  # +15% traffic buffer
    return {
        "estimated_minutes": max(minutes, 5),
        "assumption": f"Urban traffic in {city} (~{speed_kmh} km/h average)"
    }

# ── Tool Definition ───────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "search_hospitals",
        "description": "Search for hospitals in a city using real-time Google Places API. Provide user_lat/user_lon for nearest results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "user_lat": {"type": "number", "description": "User's current latitude (highly recommended)"},
                "user_lon": {"type": "number", "description": "User's current longitude (highly recommended)"},
                "radius_km": {"type": "number", "description": "Search radius in kilometers (default 10)"}
            },
            "required": ["city"]
        }
    }
]

def execute_tool(name: str, inputs: dict) -> str:
    if name == "search_hospitals":
        results = search_hospitals(**inputs)
        if not results:
            return json.dumps({"error": "No hospitals found."})

        simplified = []
        for h in results:
            hosp = {
                "id": h["id"],
                "name": h["name"],
                "address": h["address"],
                "phone": h.get("phone"),
                "rating": h.get("rating"),
                "emergency_available": h.get("emergency_available", True),
                "distance_km": h.get("distance_km"),
                "specialties": h.get("specialties", ["General", "Emergency"])
            }
            simplified.append(hosp)
        return json.dumps(simplified)
    
    return json.dumps({"error": f"Unknown tool: {name}"})

# ── Nearest Hospital Agent Class ──────────────────────────────────────────────
class NearestHospitalAgent:
    def __init__(self):
        self.messages = []

    def find_nearest_hospital(self, triage_result: dict, tourist_info: dict,
                              user_lat: float = None, user_lon: float = None,
                              max_radius_km: float = 10.0, max_time_minutes: int = 30) -> dict:
        """
        Finds the nearest hospital using real-time API + agentic loop.
        """
        city = tourist_info.get("city", "Kolkata")
        urgency = triage_result.get("urgency_label", "medium")
        severity = triage_result.get("severity_score", 5)

        system_prompt = f"""
You are a hospital locator agent for medical tourists in India.
Use the search_hospitals tool to find real hospitals.

Context:
- City: {city}
- Severity: {severity}/10 ({urgency})
- Max radius: {max_radius_km} km
- Max acceptable travel time: {max_time_minutes} minutes

Instructions:
- Prefer hospitals with emergency_available = true when severity >= 7
- Use user coordinates if provided for accurate "nearest" results
- Pick the SINGLE best hospital (closest + suitable + reachable in time)
- Include distance and estimated travel time in your reasoning

Output ONLY a valid JSON object:
{{
  "hospital_id": "hosp-xxx or google place id",
  "hospital_name": "Full Hospital Name",
  "address": "Complete address",
  "phone": "+91-...",
  "distance_km": 2.4,
  "estimated_travel_minutes": 15,
  "emergency_available": true,
  "rating": 4.6,
  "match_reason": "Closest emergency hospital, 2.4km away, reachable in 12 minutes"
}}
"""

        self.messages = [{"role": "user", "content": "Find the nearest suitable hospital for this tourist."}]

        while True:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=800,
                system=system_prompt,
                tools=TOOLS,
                messages=self.messages
            )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                raw = next((b.text for b in response.content if hasattr(b, "text")), "{}")
                raw = raw.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                elif raw.startswith("```"):
                    raw = raw.split("```")[1]
                try:
                    return json.loads(raw.strip())
                except Exception:
                    return {"error": "Failed to parse JSON from model"}

            # Tool handling
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    print(f" [HospitalFinder] Calling {block.name} with {block.input}")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            self.messages.append({"role": "user", "content": tool_results})

# ── Test Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    triage_result = {
        "severity_score": 7,
        "recommended_specialty": "Emergency Medicine",
        "urgency_label": "high",
        "triage_reason": "High fever with breathing difficulty."
    }

    tourist_info = {
        "name": "John Smith",
        "city": "Kolkata",
        "language_preference": "English"
    }

    agent = NearestHospitalAgent()

    # Example: Pass approximate user location (Park Street area)
    result = agent.find_nearest_hospital(
        triage_result,
        tourist_info,
        user_lat=22.5726,      # Example coordinates near central Kolkata
        user_lon=88.3639,
        max_radius_km=10.0,
        max_time_minutes=25
    )

    print("\n=== Nearest Hospital Match (Real-time) ===")
    print(json.dumps(result, indent=2))