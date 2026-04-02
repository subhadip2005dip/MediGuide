
# AGENT 3 (REFACTORED): Nearest Hospital Finder
# Key principle: Python handles ALL logic
# LLM only generates the final friendly summary


import json
import math
import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")



# PURE PYTHON LOGIC 


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance between two GPS coordinates in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_travel_time(distance_km: float, urgency: str) -> int:
    """
    Estimate travel time in minutes based on distance and urgency.
    High urgency = faster assumed speed (priority driving).
    """
    speed_kmh = 28 if urgency in ("high", "emergency") else 18
    minutes = (distance_km / speed_kmh) * 60 * 1.15  # +15% traffic buffer
    return max(int(minutes), 3)  # minimum 3 minutes


def fetch_hospitals_from_google(city: str, user_lat: float, user_lon: float,
                                 radius_km: float) -> list[dict]:
    """
    Call Google Places Nearby Search API.
    Returns raw list of hospital dicts or empty list on failure.
    """
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


def normalize_google_result(place: dict, user_lat: float,
                             user_lon: float, urgency: str) -> dict:
    """Convert a raw Google Places result into our standard hospital dict."""
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


MOCK_HOSPITALS = [
    {
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
    },
]


def enrich_mock_with_distance(hospitals: list, user_lat: float,
                               user_lon: float, urgency: str) -> list:
    """Add distance + travel time to mock hospitals."""
    enriched = []
    for h in hospitals:
        h = h.copy()
        d = round(haversine_distance(user_lat, user_lon, h["lat"], h["lon"]), 2)
        h["distance_km"] = d
        h["estimated_travel_minutes"] = estimate_travel_time(d, urgency)
        enriched.append(h)
    return enriched


def pick_best_hospital(hospitals: list, severity: int) -> dict:
    """
    Pure Python ranking .
    High severity → sort purely by distance.
    Normal → weighted score: 60% distance (inverted), 40% rating.
    """
    if not hospitals:
        return {}

    if severity >= 8:
        # Emergency: just get the closest one
        return min(hospitals, key=lambda h: h.get("distance_km", 999))

    # Normalize distance and rating for scoring
    max_dist = max(h.get("distance_km", 1) for h in hospitals) or 1
    max_rating = max(h.get("rating", 1) for h in hospitals) or 1

    def score(h):
        dist_score = 1 - (h.get("distance_km", max_dist) / max_dist)  # closer = higher
        rating_score = h.get("rating", 0) / max_rating
        return 0.6 * dist_score + 0.4 * rating_score

    return max(hospitals, key=score)



# LLM LAYER — Only for final human-friendly summary


def generate_friendly_summary(best_hospital: dict, triage_result: dict,
                               tourist_info: dict) -> str:
    """
    LLM's only job: write a clear, reassuring message to the tourist.
    All data is already computed — no decisions delegated to LLM.
    """
    language = tourist_info.get("language_preference", "English")
    urgency = triage_result.get("urgency_label", "medium")

    prompt = f"""
Write a short, reassuring message to a tourist in {language}.

They need to go to:
- Hospital: {best_hospital['name']}
- Address: {best_hospital['address']}
- Phone: {best_hospital.get('phone', 'not available')}
- Distance: {best_hospital['distance_km']} km away
- Estimated travel: {best_hospital['estimated_travel_minutes']} minutes
- Urgency level: {urgency}

Rules:
- Keep it under 4 sentences
- Be calm and warm
- Include the hospital name and travel time
- If urgency is high or emergency, add "Please go immediately"
- Do NOT add any extra information beyond what is given
"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ══════════════════════════════════════════════════════
# MAIN AGENT CLASS
# ══════════════════════════════════════════════════════

class NearestHospitalAgent:

    def find(self, triage_result: dict, tourist_info: dict,
             user_lat: float, user_lon: float,
             radius_km: float = 10.0) -> dict:
        """
        Full pipeline:
        1. Fetch hospitals (Google API → fallback to mock)
        2. Compute distances in Python
        3. Pick best hospital with Python scoring
        4. LLM writes the summary message only
        """
        city = tourist_info.get("city", "Kolkata")
        urgency = triage_result.get("urgency_label", "medium")
        severity = triage_result.get("severity_score", 5)

        # ── Step 1: Fetch hospitals ─────────────────────────────
        raw_places = fetch_hospitals_from_google(city, user_lat, user_lon, radius_km)

        if raw_places:
            hospitals = [
                normalize_google_result(p, user_lat, user_lon, urgency)
                for p in raw_places
            ]
            print(f"[HospitalFinder] {len(hospitals)} hospitals from Google Places API")
        else:
            hospitals = enrich_mock_with_distance(MOCK_HOSPITALS, user_lat, user_lon, urgency)
            print(f"[HospitalFinder] Using mock fallback — {len(hospitals)} hospitals")

        # ── Step 2: Filter by travel time cap ──────────────────
        # Remove hospitals that are too far for the urgency
        time_cap = 15 if severity >= 8 else 40
        reachable = [h for h in hospitals if h.get("estimated_travel_minutes", 999) <= time_cap]
        if not reachable:
            reachable = hospitals  # fallback: use all if none qualify

        # ── Step 3: Pick best — pure Python ────────────────────
        best = pick_best_hospital(reachable, severity)

        # ── Step 4: LLM generates friendly message only ─────────
        summary_message = generate_friendly_summary(best, triage_result, tourist_info)

        return {
            "hospital_name": best["name"],
            "address": best["address"],
            "phone": best.get("phone"),
            "distance_km": best["distance_km"],
            "estimated_travel_minutes": best["estimated_travel_minutes"],
            "rating": best.get("rating"),
            "data_source": best.get("source", "unknown"),
            "tourist_message": summary_message,
            "total_candidates_evaluated": len(hospitals)
        }


# ── Entry Point ───────────────────────────────────────────────────────────────
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
    result = agent.find(
        triage_result,
        tourist_info,
        user_lat=22.5726,
        user_lon=88.3639,
        radius_km=10.0
    )

    print("\n=== Nearest Hospital Result ===")
    print(json.dumps(result, indent=2))