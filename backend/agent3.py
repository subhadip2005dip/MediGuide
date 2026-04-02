# AGENT 3: Nearest Hospital Finder with Real-time Ambulance Routing
# Key Principle: Python handles ALL logic | LLM only for friendly summary

import json
import math
import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_DIRECTIONS_API_KEY = os.getenv("GOOGLE_DIRECTIONS_API_KEY")


# ====================== PURE PYTHON LOGIC ======================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_travel_time(distance_km: float, urgency: str) -> int:
    """Basic travel time estimation."""
    speed_kmh = 28 if urgency in ("high", "emergency") else 18
    minutes = (distance_km / speed_kmh) * 60 * 1.15  # +15% traffic buffer
    return max(int(minutes), 3)


def get_ambulance_routing(user_lat: float, user_lon: float, 
                         hospital_lat: float, hospital_lon: float, 
                         urgency: str = "medium") -> dict:
    """
    Real-time ambulance routing using Google Directions API.
    Returns accurate travel time with traffic and ambulance cost.
    """
    if not GOOGLE_DIRECTIONS_API_KEY:
        minutes = 15 if urgency in ("high", "emergency") else 25
        return {
            "estimated_minutes": minutes,
            "distance_km": 8.0,
            "ambulance_cost_inr": 1200 if urgency in ("high", "emergency") else 800,
            "note": "Estimated routing (API key not configured)",
            "real_time": False
        }

    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{user_lat},{user_lon}",
            "destination": f"{hospital_lat},{hospital_lon}",
            "mode": "driving",
            "departure_time": "now",
            "traffic_model": "best_guess",
            "key": GOOGLE_DIRECTIONS_API_KEY
        }

        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "OK":
            leg = data["routes"][0]["legs"][0]
            duration_sec = leg["duration_in_traffic"]["value"]
            distance_m = leg["distance"]["value"]

            minutes = duration_sec // 60
            distance_km = round(distance_m / 1000, 2)

            # Ambulance cost logic
            base_cost = 1000
            urgency_multiplier = 1.6 if urgency in ("high", "emergency") else 1.0
            ambulance_cost = int(base_cost * urgency_multiplier)

            return {
                "estimated_minutes": minutes,
                "distance_km": distance_km,
                "ambulance_cost_inr": ambulance_cost,
                "note": "Real-time routing with live traffic",
                "real_time": True
            }
    except Exception as e:
        print(f"[Ambulance Routing Error] {e}")

    # Safe fallback
    return {
        "estimated_minutes": 18,
        "distance_km": 7.5,
        "ambulance_cost_inr": 1100,
        "note": "Fallback estimated routing",
        "real_time": False
    }


def fetch_hospitals_from_google(city: str, user_lat: float, user_lon: float,
                                 radius_km: float) -> list[dict]:
    """Fetch hospitals using Google Places Nearby Search."""
    if not GOOGLE_PLACES_API_KEY:
        return []

    url = "https://places.googleapis.com/v1/places:searchNearby"
    payload = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": user_lat, "longitude": user_lon},
                "radius": int(radius_km * 1000)
            }
        },
        "includedTypes": ["hospital"],
        "maxResultCount": 15,
        "rankPreference": "DISTANCE"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.internationalPhoneNumber"
        )
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json().get("places", [])
    except Exception as e:
        print(f"[Google Places Error] {e}")
        return []


def normalize_google_result(place: dict, user_lat: float, user_lon: float, urgency: str) -> dict:
    """Convert raw Google result to standard hospital format."""
    loc = place.get("location", {})
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    distance_km = round(haversine_distance(user_lat, user_lon, lat, lon), 2) if lat and lon else None
    travel_min = estimate_travel_time(distance_km, urgency) if distance_km else None

    return {
        "id": place.get("id", "unknown"),
        "name": place.get("displayName", {}).get("text", "Unknown Hospital"),
        "address": place.get("formattedAddress", ""),
        "lat": lat,
        "lon": lon,
        "phone": place.get("internationalPhoneNumber"),
        "rating": place.get("rating", 4.0),
        "distance_km": distance_km,
        "estimated_travel_minutes": travel_min,
        "source": "google_places"
    }


MOCK_HOSPITALS = [   {
        "id": "hosp-001", "name": "Apollo Gleneagles Hospital",
        "address": "58 Canal Circular Rd, Kolkata 700054",
        "lat": 22.5726, "lon": 88.3639,
        "phone": "+91-33-2320-3040", "rating": 4.6,
        "source": "mock"
    },
    {
        "id": "hosp-002", "name": "AMRI Hospital Salt Lake",
        "address": "JC Block, Salt Lake City, Kolkata 700098",
        "lat": 22.5904, "lon": 88.4005,
        "phone": "+91-33-2335-1234", "rating": 4.4,
        "source": "mock"
    },
    {
        "id": "hosp-003", "name": "Fortis Hospital Anandapur",
        "address": "730 Anandapur, EM Bypass, Kolkata 700107",
        "lat": 22.5150, "lon": 88.4040,
        "phone": "+91-33-6628-4444", "rating": 4.7,
        "source": "mock"
    },
    {
        "id": "hosp-004", "name": "Ruby General Hospital",
        "address": "Kasba Golpark, EM Bypass, Kolkata 700107",
        "lat": 22.4995, "lon": 88.3920,
        "phone": "+91-33-3987-1800", "rating": 4.3,
        "source": "mock"
    },
    {
        "id": "hosp-005", "name": "Medica Superspecialty Hospital",
        "address": "127 Mukundapur, EM Bypass, Kolkata 700099",
        "lat": 22.4930, "lon": 88.4100,
        "phone": "+91-33-6652-0000", "rating": 4.5,
        "source": "mock"
    }, ]  


def enrich_mock_with_distance(hospitals: list, user_lat: float, user_lon: float, urgency: str) -> list:
    """Add distance and travel time to mock hospitals."""
    enriched = []
    for h in hospitals:
        h = h.copy()
        d = round(haversine_distance(user_lat, user_lon, h["lat"], h["lon"]), 2)
        h["distance_km"] = d
        h["estimated_travel_minutes"] = estimate_travel_time(d, urgency)
        enriched.append(h)
    return enriched


def pick_best_hospital(hospitals: list, severity: int) -> dict:
    """Pure Python logic to pick best hospital."""
    if not hospitals:
        return {}

    if severity >= 8:
        return min(hospitals, key=lambda h: h.get("distance_km", 999))

    max_dist = max(h.get("distance_km", 1) for h in hospitals) or 1
    max_rating = max(h.get("rating", 1) for h in hospitals) or 1

    def score(h):
        dist_score = 1 - (h.get("distance_km", max_dist) / max_dist)
        rating_score = h.get("rating", 0) / max_rating
        return 0.6 * dist_score + 0.4 * rating_score

    return max(hospitals, key=score)


# ====================== LLM LAYER (Minimal) ======================
def generate_friendly_summary(best_hospital: dict, triage_result: dict,
                              tourist_info: dict, ambulance_info: dict = None) -> str:
    """LLM only generates the final friendly message."""
    language = tourist_info.get("language_preference", "English")
    urgency = triage_result.get("urgency_label", "medium")

    prompt = f"""
Write a short, calm and reassuring message to a tourist in {language}.

They need to go to:
- Hospital: {best_hospital['name']}
- Address: {best_hospital['address']}
- Distance: {best_hospital['distance_km']} km
- Estimated travel time: {best_hospital['estimated_travel_minutes']} minutes
"""

    if ambulance_info and ambulance_info.get("real_time"):
        prompt += f"\nAmbulance estimated arrival: {ambulance_info['estimated_minutes']} minutes"

    prompt += """
Rules:
- Keep it under 4 sentences
- Be warm and reassuring
- Mention hospital name and travel time
- If urgency is high, gently urge them to proceed quickly
"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except:
        return f"Please go to {best_hospital['name']} which is {best_hospital['distance_km']} km away (approx {best_hospital['estimated_travel_minutes']} minutes)."


# ====================== MAIN AGENT CLASS ======================
class NearestHospitalAgent:

    def find(self, triage_result: dict, tourist_info: dict,
             user_lat: float, user_lon: float,
             radius_km: float = 10.0) -> dict:

        city = tourist_info.get("city", "Kolkata")
        urgency = triage_result.get("urgency_label", "medium")
        severity = triage_result.get("severity_score", 5)

        # Step 1: Fetch hospitals
        raw_places = fetch_hospitals_from_google(city, user_lat, user_lon, radius_km)

        if raw_places:
            hospitals = [normalize_google_result(p, user_lat, user_lon, urgency) for p in raw_places]
            print(f"[HospitalFinder] Found {len(hospitals)} hospitals from Google Places API")
        else:
            hospitals = enrich_mock_with_distance(MOCK_HOSPITALS, user_lat, user_lon, urgency)
            print(f"[HospitalFinder] Using mock fallback — {len(hospitals)} hospitals")

        # Step 2: Filter reachable hospitals
        time_cap = 15 if severity >= 8 else 40
        reachable = [h for h in hospitals if h.get("estimated_travel_minutes", 999) <= time_cap]
        if not reachable:
            reachable = hospitals

        # Step 3: Pick best hospital
        best = pick_best_hospital(reachable, severity)

        # Step 4: Real-time Ambulance Routing (for high severity)
        ambulance_info = None
        if severity >= 7 and best.get("lat") and best.get("lon"):
            ambulance_info = get_ambulance_routing(
                user_lat, user_lon,
                best["lat"], best["lon"],
                urgency
            )
            # Override travel time with more accurate ambulance time
            if ambulance_info:
                best["estimated_travel_minutes"] = ambulance_info["estimated_minutes"]

        # Step 5: Generate friendly message
        tourist_message = generate_friendly_summary(best, triage_result, tourist_info, ambulance_info)

        return {
            "hospital_name": best["name"],
            "address": best["address"],
            "phone": best.get("phone"),
            "distance_km": best.get("distance_km"),
            "estimated_travel_minutes": best.get("estimated_travel_minutes"),
            "rating": best.get("rating"),
            "ambulance_routing": ambulance_info,
            "tourist_message": tourist_message,
            "data_source": best.get("source", "unknown"),
            "total_candidates_evaluated": len(hospitals)
        }


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    triage_result = {
        "severity_score": 8,
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
    result = agent.find(
        triage_result=triage_result,
        tourist_info=tourist_info,
        user_lat=22.5726,   # Example coordinates (Park Street, Kolkata)
        user_lon=88.3639,
        radius_km=10.0
    )

    print("\n=== Nearest Hospital with Real-time Ambulance Routing ===")
    print(json.dumps(result, indent=2))