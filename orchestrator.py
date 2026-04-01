
# MAIN ORCHESTRATOR
# Runs all 6 agents in the correct sequence



import json
import sys
import os

# Add agents directory to path
sys.path.append(os.path.dirname(__file__))

from agent1 import MultilingualChatAgent
from agent2 import TriageAgent
from agent3 import DoctorMatchingAgent
from agent4 import BookingCoordinationAgent
from agent5 import CostEstimatorAgent
from agent6 import DocumentGeneratorAgent


def print_stage(stage_num: int, title: str):
    print(f"\n{'='*55}")
    print(f"  STAGE {stage_num}: {title}")
    print(f"{'='*55}\n")


def collect_tourist_info() -> dict:
    """Collect basic tourist info before starting agent pipeline."""
    print("\n" + "="*55)
    print("  Welcome to MediGuide — Tourist Medical Assistant")
    print("="*55)
    print("\nBefore we begin, a few quick details:\n")

    name = input("Your name: ").strip() or "Tourist"
    city = input("Which city are you in? (e.g. Kolkata, Mumbai, Delhi): ").strip() or "Kolkata"
    phone = input("Your phone number (optional): ").strip()
    email = input("Your email (optional): ").strip()
    currency = input("Your home currency (USD/EUR/GBP etc.): ").strip().upper() or "USD"
    insurance = input(
        "Insurance plan? [1] Standard Tourist  [2] Premium Tourist  [3] None: "
    ).strip()

    insurance_map = {"1": "standard_tourist", "2": "premium_tourist", "3": "no_insurance"}
    insurance_plan = insurance_map.get(insurance, "no_insurance")

    return {
        "name": name,
        "city": city,
        "phone": phone,
        "email": email,
        "home_currency": currency,
        "insurance_plan": insurance_plan,
        "language_preference": "English"  # Will be updated from Agent 1 output
    }


def run_pipeline(tourist_info: dict = None, demo_mode: bool = False):
    """
    Full MediGuide pipeline.
    demo_mode=True skips interactive chat and uses sample data.
    """

    # ── Demo data for testing without interactive input ─────────────────────────
    if demo_mode:
        print("\n[DEMO MODE — Using sample tourist data]\n")
        tourist_info = {
            "name": "John Smith",
            "city": "Kolkata",
            "phone": "+1-555-123-4567",
            "email": "john.smith@email.com",
            "home_currency": "USD",
            "insurance_plan": "standard_tourist",
            "language_preference": "English"
        }
        intake_data = {
            "detected_language": "English",
            "original_complaint": "I have fever and headache since yesterday",
            "symptoms": ["fever", "headache", "body ache"],
            "duration": "1 day",
            "severity_self_reported": "moderate",
            "allergies": "penicillin",
            "existing_conditions": "none",
            "medications": "paracetamol",
            "tourist_name": "John Smith",
            "ready_for_triage": True
        }
    else:
        # ── STAGE 1: Multilingual Chat Agent ────────────────────────────────────
        print_stage(1, "Symptom Intake (Multilingual Chat Agent)")
        chat_agent = MultilingualChatAgent()
        intake_data = chat_agent.run_interactive()

        if intake_data.get("emergency"):
            print("\n🚨 Emergency protocol activated. Please call 112 immediately.")
            return

        # Update language preference from detected language
        tourist_info["language_preference"] = intake_data.get("detected_language", "English")
        if intake_data.get("tourist_name"):
            tourist_info["name"] = intake_data["tourist_name"]

    # ── STAGE 2: Triage & Assessment Agent ─────────────────────────────────────
    print_stage(2, "Triage & Assessment Agent")
    triage_agent = TriageAgent()
    triage_result = triage_agent.assess(intake_data)
    triage_agent.print_summary(triage_result)

    # Handle true emergency
    if triage_result["severity_score"] >= 10:
        print("\n🚨 CRITICAL: Please go to the nearest Emergency Room immediately!")
        print("   Call 112 (India Emergency) or ask hotel staff for help.")
        return

    # ── STAGE 3: Doctor Matching Agent ─────────────────────────────────────────
    print_stage(3, "Doctor Matching Agent")
    matching_agent = DoctorMatchingAgent()
    matched_provider = matching_agent.match(triage_result, tourist_info)
    print(f"\n✅ Best Match: {matched_provider.get('provider_name')} "
          f"@ {matched_provider.get('clinic_name')}")
    print(f"   📅 Slot: {matched_provider.get('slot_date')} "
          f"at {matched_provider.get('slot_time')}")

    # ── STAGE 4: Booking & Coordination Agent ──────────────────────────────────
    print_stage(4, "Booking & Coordination Agent")
    booking_agent = BookingCoordinationAgent()
    booking_confirmation = booking_agent.book(matched_provider, triage_result, tourist_info)
    print(f"\n✅ Booking ID: {booking_confirmation.get('booking_id')}")
    print(f"   Status: {booking_confirmation.get('status', '').upper()}")

    # ── STAGE 5: Cost Estimator Agent ──────────────────────────────────────────
    print_stage(5, "Cost Estimator Agent")
    cost_agent = CostEstimatorAgent()
    cost_estimate = cost_agent.estimate(triage_result, matched_provider, tourist_info)
    print(f"\n💰 Estimated Total: ₹{cost_estimate.get('cost_breakdown_inr', {}).get('total_estimated', 'N/A')}")
    print(f"   Insurance Covers: ₹{cost_estimate.get('insurance', {}).get('covered_inr', 0)}")
    print(f"   Your Out-of-Pocket: ₹{cost_estimate.get('insurance', {}).get('out_of_pocket_inr', 'N/A')}")

    # ── STAGE 6: Document Generator Agent ─────────────────────────────────────
    print_stage(6, "Document Generator Agent")
    doc_agent = DocumentGeneratorAgent()
    documents = doc_agent.generate(
        intake_data, triage_result, booking_confirmation,
        cost_estimate, tourist_info
    )
    print(f"\n✅ Documents Generated: {', '.join(documents.get('documents_generated', []))}")

    # ── FINAL SUMMARY ──────────────────────────────────────────────────────────
    print("\n" + "="*55)
    print("  🏥 MEDIGUIDE — COMPLETE SUMMARY")
    print("="*55)
    print(f"\n  Patient     : {tourist_info['name']}")
    print(f"  Doctor      : {booking_confirmation.get('doctor', matched_provider.get('provider_name'))}")
    print(f"  Clinic      : {booking_confirmation.get('clinic', matched_provider.get('clinic_name'))}")
    print(f"  Address     : {booking_confirmation.get('address', matched_provider.get('address'))}")
    print(f"  Date & Time : {booking_confirmation.get('appointment_date')} "
          f"at {booking_confirmation.get('appointment_time')}")
    print(f"  Booking ID  : {booking_confirmation.get('booking_id')}")
    print(f"  Est. Cost   : ₹{cost_estimate.get('cost_breakdown_inr', {}).get('total_estimated', 'N/A')}")

    if booking_confirmation.get("confirmation_message"):
        print(f"\n  💬 {booking_confirmation['confirmation_message']}")

    print("\n" + "="*55)

    # Print documents
    if documents.get("medical_summary_text"):
        print("\n📄 MEDICAL SUMMARY FOR DOCTOR:")
        print(documents["medical_summary_text"])

    if documents.get("claim_letter_text"):
        print("\n📋 INSURANCE CLAIM LETTER:")
        print(documents["claim_letter_text"])

    # Return full pipeline output for integration use
    return {
        "tourist_info": tourist_info,
        "intake_data": intake_data,
        "triage_result": triage_result,
        "matched_provider": matched_provider,
        "booking_confirmation": booking_confirmation,
        "cost_estimate": cost_estimate,
        "documents": documents
    }


# ── Entry point ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MediGuide — Tourist Medical Assistant")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with sample data")
    args = parser.parse_args()

    if args.demo:
        result = run_pipeline(demo_mode=True)
    else:
        tourist_info = collect_tourist_info()
        result = run_pipeline(tourist_info=tourist_info, demo_mode=False)