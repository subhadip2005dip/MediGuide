# ============================================
# MAIN ORCHESTRATOR - MediGuide AI Pipeline
# Runs all 6 agents in correct sequence
# ============================================

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import updated agents
from agent1 import MultilingualChatAgent
from agent2 import TriageAgent
from agent3 import NearestHospitalAgent
from agent4 import BookingCoordinationAgent
from agent5 import CostEstimatorAgent
from agent6 import DocumentGeneratorAgent


def print_stage(stage_num: int, title: str):
    print(f"\n{'='*60}")
    print(f" STAGE {stage_num}: {title}")
    print(f"{'='*60}\n")

def collect_tourist_info() -> dict:
    name = input("Your full name: ").strip() or "Tourist"
    city = input("Which city are you in?: ").strip() or "Kolkata"
    phone = input("Phone (optional): ").strip()
    email = input("Email (optional): ").strip()
    currency = input("Home currency (USD/EUR/GBP): ").strip().upper() or "USD"

    # ✅ Collect age and gender
    age_input = input("Your age (optional, improves triage): ").strip()
    age = int(age_input) if age_input.isdigit() else None
    gender = input("Gender (male/female/other, optional): ").strip().lower() or None

    print("\nInsurance Plan:")
    print("1. Standard Tourist  2. Premium Tourist  3. No Insurance")
    insurance_choice = input("Choice (1/2/3): ").strip()
    insurance_map = {"1": "standard_tourist", "2": "premium_tourist", "3": "no_insurance"}

    return {
        "name": name, "city": city, "phone": phone, "email": email,
        "home_currency": currency,
        "insurance_plan": insurance_map.get(insurance_choice, "no_insurance"),
        "language_preference": "English",
        "age": age,        # ✅ added
        "gender": gender   # ✅ added
    }


def run_pipeline(demo_mode: bool = False):

    if demo_mode:
        print("\n[DEMO MODE ACTIVATED]")
        tourist_info = {
            "name": "John Smith", "city": "Kolkata",
            "phone": "+91-9876543210", "email": "john.smith@email.com",
            "home_currency": "USD", "insurance_plan": "standard_tourist",
            "language_preference": "English",
            "age": 45, "gender": "male"   # ✅ realistic demo values
        }
        intake_data = {
            "detected_language": "English",
            "original_complaint": "I have fever and headache since yesterday",
            "symptoms": ["fever", "headache", "body ache"],
            "duration": "1 day", "severity_self_reported": "moderate",
            "allergies": "penicillin", "existing_conditions": "none",
            "medications": "paracetamol", "tourist_name": "John Smith"
        }
        # ✅ Show all stages even in demo
        print_stage(1, "Symptom Intake [DEMO - using sample data]")
        print(f"  Complaint : {intake_data['original_complaint']}")
        print(f"  Symptoms  : {', '.join(intake_data['symptoms'])}")

    else:
        tourist_info = collect_tourist_info()
        print_stage(1, "Multilingual Symptom Intake")
        chat_agent = MultilingualChatAgent()
        intake_data = chat_agent.run_interactive()

        if isinstance(intake_data, dict) and intake_data.get("emergency"):
            print("\n🚨 EMERGENCY — Call 112 immediately!")
            return

        if intake_data.get("detected_language"):
            tourist_info["language_preference"] = intake_data["detected_language"]
        if intake_data.get("tourist_name"):
            tourist_info["name"] = intake_data["tourist_name"]

    # STAGE 2: Triage — use age/gender from tourist_info
    print_stage(2, "Triage & Severity Assessment")
    triage_agent = TriageAgent()
    triage_result = triage_agent.assess(
        intake_data,
        age=tourist_info.get("age"),       # ✅ dynamic
        gender=tourist_info.get("gender")  # ✅ dynamic
    )
    triage_agent.print_summary(triage_result)

    if triage_result["severity_score"] >= 10:
        print("\n🚨 CRITICAL EMERGENCY — Go to nearest ER immediately!")
        return

    # STAGE 3: Hospital finder
    print_stage(3, "Finding Nearest Hospital")
    hospital_agent = NearestHospitalAgent()
    hospital_result = hospital_agent.find(
        triage_result=triage_result,
        tourist_info=tourist_info,
        user_lat=22.5726,
        user_lon=88.3639,
        radius_km=10.0
    )
    print(f"  ✅ Best match: {hospital_result.get('hospital_name')}")
    print(f"  📍 Distance : {hospital_result.get('distance_km')} km")

    # ✅ Issue 1 Fix — bridge hospital result to booking format
    matched_provider = {
        "provider_id": hospital_result.get("id", "hosp-001"),
        "provider_name": hospital_result.get("hospital_name"),
        "clinic_name": hospital_result.get("hospital_name"),
        "address": hospital_result.get("address"),
        "phone": hospital_result.get("phone"),
        "slot_id": f"slot-{hospital_result.get('id', 'auto')}",
        "slot_date": "2025-08-05",   # In production: fetch real slots
        "slot_time": "09:00 AM"
    }

    # STAGE 4: Booking
    print_stage(4, "Booking & Coordination")
    booking_agent = BookingCoordinationAgent()
    booking_confirmation = booking_agent.book(
        matched_provider,    # ✅ correct shape now
        triage_result,
        tourist_info
    )

    # STAGE 5: Cost
    print_stage(5, "Cost Estimation")
    cost_agent = CostEstimatorAgent()
    cost_estimate = cost_agent.estimate(triage_result, matched_provider, tourist_info)

    # STAGE 6: Documents
    print_stage(6, "Medical Document Generation")
    doc_agent = DocumentGeneratorAgent()
    documents = doc_agent.generate(
        intake_data=intake_data,
        triage_result=triage_result,
        booking_confirmation=booking_confirmation,
        cost_estimate=cost_estimate,
        tourist_info=tourist_info
    )

    # Final summary
    print("\n" + "="*70)
    print("  🎉 MEDIGUIDE PIPELINE COMPLETED")
    print("="*70)
    print(f"  Patient      : {tourist_info['name']}")
    print(f"  Hospital     : {hospital_result.get('hospital_name')}")
    print(f"  Booking ID   : {booking_confirmation.get('booking_id')}")
    print(f"  Severity     : {triage_result['severity_score']}/10")
    print(f"  Est. Cost    : ₹{cost_estimate.get('cost_breakdown_inr', {}).get('total_estimated', 'N/A')}")
    print(f"  Payment Link : {cost_estimate.get('payment', {}).get('payment_url', 'N/A')}")
    print("="*70)

    return {
        "tourist_info": tourist_info,
        "intake_data": intake_data,
        "triage_result": triage_result,
        "hospital_result": hospital_result,
        "booking_confirmation": booking_confirmation,
        "cost_estimate": cost_estimate,
        "documents": documents
    }


# ── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MediGuide AI - Tourist Medical Assistant")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with sample data")
    args = parser.parse_args()

    run_pipeline(demo_mode=args.demo)