
# AGENT 4: Booking & Coordination Agent
# Confirms appointment + sends notifications
# Full agentic loop with tool use


import json
import uuid
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ── Mock Booking Store (replace with real DB) ───────────────────────────────────
BOOKINGS_DB = {}
NOTIFICATIONS_LOG = []


# ── Tool Implementations ────────────────────────────────────────────────────────

def confirm_booking(provider_id: str, slot_id: str, tourist_name: str,
                    tourist_phone: str, tourist_email: str,
                    language_preference: str, symptoms: str,
                    severity_score: int) -> dict:
    booking_id = f"BK-{str(uuid.uuid4())[:8].upper()}"
    booking = {
        "id": booking_id,
        "provider_id": provider_id,
        "slot_id": slot_id,
        "tourist_name": tourist_name,
        "tourist_phone": tourist_phone,
        "tourist_email": tourist_email,
        "language_preference": language_preference,
        "symptoms": symptoms,
        "severity_score": severity_score,
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    BOOKINGS_DB[booking_id] = booking
    return booking


def send_notification(channel: str, recipient: str,
                       message: str, booking_id: str) -> dict:
    log_entry = {
        "id": f"NOTIF-{str(uuid.uuid4())[:6].upper()}",
        "channel": channel,  # "sms", "email", "push"
        "recipient": recipient,
        "message": message,
        "booking_id": booking_id,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"
    }
    NOTIFICATIONS_LOG.append(log_entry)
    print(f"  [Notification Sent] {channel.upper()} → {recipient}")
    return log_entry


def check_booking_status(booking_id: str) -> dict:
    booking = BOOKINGS_DB.get(booking_id)
    if not booking:
        return {"error": f"Booking {booking_id} not found"}
    return {"booking_id": booking_id, "status": booking["status"],
            "tourist": booking["tourist_name"]}


# ── Tool Definitions ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "confirm_booking",
        "description": "Confirm and store an appointment booking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "provider_id": {"type": "string"},
                "slot_id": {"type": "string"},
                "tourist_name": {"type": "string"},
                "tourist_phone": {"type": "string"},
                "tourist_email": {"type": "string"},
                "language_preference": {"type": "string"},
                "symptoms": {"type": "string"},
                "severity_score": {"type": "integer"}
            },
            "required": ["provider_id", "slot_id", "tourist_name", "symptoms", "severity_score"]
        }
    },
    {
        "name": "send_notification",
        "description": "Send SMS, email, or push notification to tourist or hospital.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "enum": ["sms", "email", "push"]},
                "recipient": {"type": "string", "description": "Phone number or email"},
                "message": {"type": "string"},
                "booking_id": {"type": "string"}
            },
            "required": ["channel", "recipient", "message", "booking_id"]
        }
    },
    {
        "name": "check_booking_status",
        "description": "Verify a booking was successfully created.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string"}
            },
            "required": ["booking_id"]
        }
    }
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "confirm_booking":
        result = confirm_booking(**inputs)
        return json.dumps(result)
    elif name == "send_notification":
        result = send_notification(**inputs)
        return json.dumps(result)
    elif name == "check_booking_status":
        result = check_booking_status(**inputs)
        return json.dumps(result)
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Booking & Coordination Agent ────────────────────────────────────────────────

class BookingCoordinationAgent:
    def __init__(self):
        self.messages = []

    def book(self, matched_provider: dict, triage_result: dict,
             tourist_info: dict) -> dict:
        """
        Confirms booking and sends all notifications.
        Returns: booking confirmation dict
        """
        system_prompt = f"""
You are a medical booking coordination agent. Your job is to:
1. Confirm the appointment booking using confirm_booking tool
2. Send SMS notification to tourist (if phone available)
3. Send email notification to tourist (if email available)
4. Verify the booking was created using check_booking_status

Tourist Information:
- Name: {tourist_info['name']}
- Phone: {tourist_info.get('phone', 'not provided')}
- Email: {tourist_info.get('email', 'not provided')}
- Language: {tourist_info['language_preference']}

Doctor Matched:
- Doctor: {matched_provider['provider_name']}
- Clinic: {matched_provider['clinic_name']}
- Address: {matched_provider['address']}
- Date: {matched_provider['slot_date']}
- Time: {matched_provider['slot_time']}

Triage:
- Symptoms: {triage_result['translated_summary']}
- Severity: {triage_result['severity_score']}/10

Notification message must:
- Be in {tourist_info['language_preference']} language
- Include doctor name, clinic, address, date, time
- Be warm and reassuring
- Add: "Please arrive 10 minutes early with valid ID and insurance card"

After all steps done, return a JSON summary:
{{
  "booking_id": "BK-XXXXXXXX",
  "status": "confirmed",
  "doctor": "Dr. Name",
  "clinic": "Clinic Name",
  "address": "Full Address",
  "appointment_date": "YYYY-MM-DD",
  "appointment_time": "HH:MM AM/PM",
  "notifications_sent": ["sms", "email"],
  "confirmation_message": "Friendly message to tourist in their language"
}}
"""
        self.messages = [{
            "role": "user",
            "content": "Please complete the booking and send all notifications."
        }]

        print("\n[Booking & Coordination Agent Starting...]\n")

        final_result = None

        while True:
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                system=system_prompt,
                tools=TOOLS,
                messages=self.messages
            )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                raw = next((b.text for b in response.content if hasattr(b, "text")), "{}")
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                try:
                    final_result = json.loads(raw.strip())
                except Exception:
                    final_result = {"status": "confirmed", "raw_response": raw}
                break

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [Booking] {block.name}({json.dumps(block.input)[:80]}...)")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            self.messages.append({"role": "user", "content": tool_results})

        return final_result


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    matched_provider = {
        "provider_id": "doc-001",
        "provider_name": "Dr. Priya Sharma",
        "clinic_name": "City Health Clinic",
        "specialty": "General Physician",
        "address": "12 Park Street, Kolkata",
        "phone": "+91-98765-00001",
        "cost_range": "₹500–800",
        "rating": 4.8,
        "slot_id": "slot-101",
        "slot_date": "2025-08-01",
        "slot_time": "09:00 AM"
    }

    triage_result = {
        "severity_score": 6,
        "urgency_label": "medium",
        "translated_summary": "Tourist has fever 102F, body ache, and cough for 2 days."
    }

    tourist_info = {
        "name": "John Smith",
        "city": "Kolkata",
        "language_preference": "English",
        "phone": "+1-555-123-4567",
        "email": "john.smith@email.com"
    }

    agent = BookingCoordinationAgent()
    result = agent.book(matched_provider, triage_result, tourist_info)

    print("\n" + "=" * 50)
    print("BOOKING CONFIRMATION:")
    print(json.dumps(result, indent=2))