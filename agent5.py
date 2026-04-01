# ============================================
# AGENT 5: Cost Estimator Agent (Real-time Enhanced)
# Pulls localized costs + hospital price level via Google Places + insurance benchmarks
# ============================================
import json
import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ── Enhanced Cost Benchmarks (2026 realistic for India) ───────────────────────
COST_BENCHMARKS = {
    "General Physician": {
        "consultation_min": 400, "consultation_max": 1200,
        "tests": {"blood_test": 600, "urine_test": 250, "xray": 900, "cbc": 550},
        "medicines_avg": 500
    },
    "Cardiologist": {
        "consultation_min": 1200, "consultation_max": 3000,
        "tests": {"ecg": 500, "echo": 2800, "stress_test": 4000, "lipid_profile": 800},
        "medicines_avg": 1800
    },
    "Emergency Medicine": {
        "consultation_min": 2000, "consultation_max": 6000,
        "tests": {"blood_panel": 2500, "ct_scan": 8500, "xray": 1000, "ultrasound": 1500},
        "medicines_avg": 2500
    },
    "Orthopedic": {
        "consultation_min": 900, "consultation_max": 2500,
        "tests": {"xray": 900, "mri": 6500},
        "medicines_avg": 1000
    },
    "Dermatologist": {
        "consultation_min": 600, "consultation_max": 1800,
        "tests": {"skin_biopsy": 2500},
        "medicines_avg": 700
    }
}

INSURANCE_PLANS = {
    "standard_tourist": {
        "plan_name": "Standard Tourist Medical Cover",
        "deductible_inr": 2500,
        "coverage_percent": 80,
        "max_claim_inr": 150000,
        "covers": ["consultation", "tests", "medicines", "hospitalization"]
    },
    "premium_tourist": {
        "plan_name": "Premium Tourist Cover",
        "deductible_inr": 1000,
        "coverage_percent": 92,
        "max_claim_inr": 600000,
        "covers": ["consultation", "tests", "medicines", "hospitalization", "emergency_transport"]
    },
    "no_insurance": {
        "plan_name": "Self Pay (No Insurance)",
        "deductible_inr": 0,
        "coverage_percent": 0,
        "max_claim_inr": 0,
        "covers": []
    }
}

CURRENCY_RATES = {
    "USD": 83.8, "EUR": 90.5, "GBP": 106.2, "AUD": 54.5,
    "CAD": 61.8, "JPY": 0.55, "SGD": 62.5, "AED": 22.8
}

# ── Real-time Price Level from Google Places (if hospital provided) ───────────
def get_hospital_price_level(hospital_name: str, city: str = "Kolkata") -> dict:
    """Try to get price_level from Google Places API (0-4 scale)."""
    if not GOOGLE_PLACES_API_KEY:
        return {"price_level": None, "note": "Using benchmark data"}

    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        payload = {
            "textQuery": f"{hospital_name} {city}",
            "maxResultCount": 3
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.priceLevel,places.displayName"
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()

        for place in data.get("places", []):
            level = place.get("priceLevel")
            if level is not None:
                # Convert Google price_level (0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive)
                multiplier = 0.8 if level <= 1 else 1.0 if level == 2 else 1.3 if level == 3 else 1.6
                return {"price_level": level, "multiplier": multiplier, "note": "Adjusted using Google price data"}
        return {"price_level": None, "note": "No price data found"}
    except Exception:
        return {"price_level": None, "note": "API unavailable, using standard benchmarks"}


def get_cost_benchmark(specialty: str, city: str = "Kolkata", hospital_name: str = None) -> dict:
    benchmark = COST_BENCHMARKS.get(specialty, COST_BENCHMARKS["General Physician"])
    
    multiplier = 1.35 if city in ["Mumbai", "Delhi", "Bangalore"] else 1.15 if city == "Kolkata" else 1.0
    
    # Try to adjust using real hospital price level
    price_info = get_hospital_price_level(hospital_name, city) if hospital_name else {}
    if price_info.get("multiplier"):
        multiplier *= price_info["multiplier"]

    return {
        "specialty": specialty,
        "city": city,
        "consultation_range_inr": {
            "min": int(benchmark["consultation_min"] * multiplier),
            "max": int(benchmark["consultation_max"] * multiplier)
        },
        "common_tests_inr": {k: int(v * multiplier) for k, v in benchmark["tests"].items()},
        "estimated_medicines_inr": int(benchmark["medicines_avg"] * multiplier),
        "price_adjustment_note": price_info.get("note", "")
    }


def get_insurance_coverage(plan_type: str, estimated_total_inr: float) -> dict:
    plan = INSURANCE_PLANS.get(plan_type, INSURANCE_PLANS["no_insurance"])
    if plan["coverage_percent"] == 0:
        return {
            "plan_name": plan["plan_name"],
            "covered_amount_inr": 0,
            "out_of_pocket_inr": round(estimated_total_inr, 2),
            "coverage_percent": 0,
            "note": "Full self-payment required"
        }

    after_deductible = max(0, estimated_total_inr - plan["deductible_inr"])
    covered = min(after_deductible * (plan["coverage_percent"] / 100), plan["max_claim_inr"])
    out_of_pocket = estimated_total_inr - covered

    return {
        "plan_name": plan["plan_name"],
        "estimated_total_inr": round(estimated_total_inr, 2),
        "deductible_inr": plan["deductible_inr"],
        "covered_amount_inr": round(covered, 2),
        "out_of_pocket_inr": round(out_of_pocket, 2),
        "coverage_percent": plan["coverage_percent"],
        "covers": plan["covers"]
    }


def convert_currency(amount_inr: float, target_currency: str) -> dict:
    rate = CURRENCY_RATES.get(target_currency.upper(), 83.8)
    converted = round(amount_inr / rate, 2)
    return {
        "amount_inr": round(amount_inr, 2),
        "target_currency": target_currency.upper(),
        "converted_amount": converted,
        "exchange_rate": f"1 {target_currency.upper()} ≈ ₹{rate}"
    }


# ── Tool Definitions ─────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_cost_benchmark",
        "description": "Get realistic cost ranges for a medical specialty in a city (adjusts using Google price data if hospital provided).",
        "input_schema": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string"},
                "city": {"type": "string"},
                "hospital_name": {"type": "string", "description": "Optional hospital name for price adjustment"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_insurance_coverage",
        "description": "Calculate insurance coverage and out-of-pocket cost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_type": {"type": "string"},
                "estimated_total_inr": {"type": "number"}
            },
            "required": ["plan_type", "estimated_total_inr"]
        }
    },
    {
        "name": "convert_currency",
        "description": "Convert INR amount to tourist's home currency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_inr": {"type": "number"},
                "target_currency": {"type": "string"}
            },
            "required": ["amount_inr", "target_currency"]
        }
    }
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "get_cost_benchmark":
        return json.dumps(get_cost_benchmark(**inputs))
    elif name == "get_insurance_coverage":
        return json.dumps(get_insurance_coverage(**inputs))
    elif name == "convert_currency":
        return json.dumps(convert_currency(**inputs))
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Cost Estimator Agent ─────────────────────────────────────────────────────
class CostEstimatorAgent:
    def __init__(self):
        self.messages = []

    def estimate(self, triage_result: dict, matched_provider: dict, tourist_info: dict) -> dict:
        home_currency = tourist_info.get("home_currency", "USD")
        insurance_plan = tourist_info.get("insurance_plan", "no_insurance")
        hospital_name = matched_provider.get("hospital_name") or matched_provider.get("provider_name", "")

        system_prompt = f"""
You are an accurate medical cost estimator for international tourists in India.

Context:
- Recommended Specialty: {triage_result.get('recommended_specialty')}
- City: {tourist_info.get('city', 'Kolkata')}
- Matched Provider/Hospital: {hospital_name}
- Doctor/Clinic cost range (if available): {matched_provider.get('cost_range', 'Not specified')}
- Tourist Insurance: {insurance_plan}
- Tourist Home Currency: {home_currency}

Instructions:
1. Call get_cost_benchmark with the specialty, city, and hospital_name for realistic costs.
2. Estimate a reasonable total (consultation + likely tests + medicines).
3. Use get_insurance_coverage to compute coverage.
4. Convert the final out-of-pocket to {home_currency}.
5. Add practical tips for payment in India.

Output **ONLY** a clean JSON object (no extra text):
{{
  "specialty": "...",
  "cost_breakdown_inr": {{
    "consultation": number,
    "estimated_tests": number,
    "estimated_medicines": number,
    "total_estimated": number
  }},
  "insurance": {{
    "plan": "...",
    "covered_inr": number,
    "out_of_pocket_inr": number
  }},
  "out_of_pocket_{home_currency.lower()}": number,
  "payment_tips": ["tip1", "tip2"],
  "cost_summary": "One friendly sentence for the tourist",
  "disclaimer": "Costs are estimates only. Actual may vary."
}}
"""

        self.messages = [{"role": "user", "content": "Estimate the full transparent cost for this medical visit."}]

        while True:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                system=system_prompt,
                tools=TOOLS,
                messages=self.messages
            )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                raw = next((b.text for b in response.content if hasattr(b, "text")), "{}")
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1].strip()
                    if raw.startswith("json"):
                        raw = raw[4:].strip()
                try:
                    return json.loads(raw)
                except:
                    return {"error": "Failed to parse cost estimate JSON"}

            # Handle tool calls
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    print(f"  [CostEstimator] {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            self.messages.append({"role": "user", "content": tool_results})


# ── Test Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    triage_result = {
        "severity_score": 6,
        "recommended_specialty": "General Physician"
    }

    matched_provider = {
        "hospital_name": "Apollo Gleneagles Hospital",
        "provider_name": "Dr. Priya Sharma",
        "cost_range": "₹500–800"
    }

    tourist_info = {
        "name": "John Smith",
        "city": "Kolkata",
        "home_currency": "USD",
        "insurance_plan": "standard_tourist"
    }

    agent = CostEstimatorAgent()
    result = agent.estimate(triage_result, matched_provider, tourist_info)

    print("\n=== Real-time Cost Estimate ===")
    print(json.dumps(result, indent=2))