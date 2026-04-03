
# AGENT 4: Booking & Coordination Agent (Upgraded)
# New: Slot conflict detection, cancellation/rescheduling,
#      hospital-side notification, 1-hour reminder system


import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()


# IN-MEMORY STORES 


BOOKINGS_DB = {}          # booking_id → booking dict
SLOTS_DB = {}             # slot_id → {"booked": bool, "booking_id": str}
NOTIFICATIONS_LOG = []    # all notification records
REMINDER_REGISTRY = {}    # booking_id → reminder thread info



# SLOT CONFLICT DETECTION — Pure Python


def is_slot_available(slot_id: str) -> bool:
    """Check if a slot is free ."""
    slot = SLOTS_DB.get(slot_id)
    if not slot:
        # Slot not in DB yet — treat as available
        return True
    return not slot.get("booked", False)


def lock_slot(slot_id: str, booking_id: str):
    """Mark slot as booked — prevents double booking."""
    SLOTS_DB[slot_id] = {
        "booked": True,
        "booking_id": booking_id,
        "locked_at": datetime.now().isoformat()
    }


def release_slot(slot_id: str):
    """Free up a slot on cancellation."""
    if slot_id in SLOTS_DB:
        SLOTS_DB[slot_id]["booked"] = False
        SLOTS_DB[slot_id]["released_at"] = datetime.now().isoformat()
        print(f"  [Slot Released] {slot_id} is now available again")



# CORE BOOKING FUNCTIONS 


def confirm_booking(provider_id: str, slot_id: str, tourist_name: str,
                    tourist_phone: str, tourist_email: str,
                    language_preference: str, symptoms: str,
                    severity_score: int) -> dict:
    """
    Create and store a booking.
    Raises ValueError if slot is already taken.
    """
    #  Conflict check before booking 
    if not is_slot_available(slot_id):
        conflicting_id = SLOTS_DB[slot_id].get("booking_id", "unknown")
        raise ValueError(
            f"Slot {slot_id} is already booked (Booking ID: {conflicting_id}). "
            f"Please select a different slot."
        )

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
        "created_at": datetime.now().isoformat(),
        "cancelled_at": None,
        "cancellation_reason": None,
        "reschedule_history": []
    }

    BOOKINGS_DB[booking_id] = booking
    lock_slot(slot_id, booking_id)
    print(f"  ✅ Booking confirmed: {booking_id} | Slot locked: {slot_id}")
    return booking


def cancel_booking(booking_id: str, reason: str = "Tourist requested cancellation") -> dict:
    """
    Cancel a booking and release the slot.
    Returns updated booking or error dict.
    """
    booking = BOOKINGS_DB.get(booking_id)
    if not booking:
        return {"error": f"Booking {booking_id} not found"}

    if booking["status"] == "cancelled":
        return {"error": f"Booking {booking_id} is already cancelled"}

    # Update status
    booking["status"] = "cancelled"
    booking["cancelled_at"] = datetime.now().isoformat()
    booking["cancellation_reason"] = reason

    # Release the slot
    release_slot(booking["slot_id"])

    # Cancel any pending reminder
    cancel_reminder(booking_id)

    BOOKINGS_DB[booking_id] = booking
    print(f"  Booking cancelled: {booking_id} | Reason: {reason}")
    return booking


def reschedule_booking(booking_id: str, new_slot_id: str,
                        new_slot_date: str, new_slot_time: str) -> dict:
    """
    Reschedule a booking to a new slot.
    Checks new slot availability, releases old slot.
    """
    booking = BOOKINGS_DB.get(booking_id)
    if not booking:
        return {"error": f"Booking {booking_id} not found"}

    if booking["status"] == "cancelled":
        return {"error": "Cannot reschedule a cancelled booking"}

    # Check new slot availability
    if not is_slot_available(new_slot_id):
        conflicting_id = SLOTS_DB[new_slot_id].get("booking_id", "unknown")
        return {
            "error": f"New slot {new_slot_id} is already taken "
                     f"(Booking ID: {conflicting_id}). Choose another slot."
        }

    # Save reschedule history
    old_slot_id = booking["slot_id"]
    booking["reschedule_history"].append({
        "rescheduled_at": datetime.now().isoformat(),
        "old_slot_id": old_slot_id,
        "new_slot_id": new_slot_id,
        "new_slot_date": new_slot_date,
        "new_slot_time": new_slot_time
    })

    # Release old slot, lock new slot
    release_slot(old_slot_id)
    lock_slot(new_slot_id, booking_id)

    # Update booking
    booking["slot_id"] = new_slot_id
    booking["slot_date"] = new_slot_date
    booking["slot_time"] = new_slot_time
    booking["status"] = "rescheduled"
    booking["rescheduled_at"] = datetime.now().isoformat()

    # Cancel old reminder, schedule new one
    cancel_reminder(booking_id)

    BOOKINGS_DB[booking_id] = booking
    print(f"  🔄 Booking rescheduled: {booking_id} → New slot: {new_slot_id} "
          f"({new_slot_date} at {new_slot_time})")
    return booking


def check_booking_status(booking_id: str) -> dict:
    """Return current booking state."""
    return BOOKINGS_DB.get(booking_id, {"error": f"Booking {booking_id} not found"})



# NOTIFICATION SYSTEM 


def send_notification(channel: str, recipient: str,
                       message: str, booking_id: str,
                       notification_type: str = "confirmation") -> dict:
    """
    Log and send a notification.
    channel: "sms" | "email" | "push" | "hospital_portal"
    notification_type: "confirmation" | "cancellation" | "reschedule" | "reminder"
    """
    log_entry = {
        "id": f"NOTIF-{str(uuid.uuid4())[:6].upper()}",
        "channel": channel,
        "recipient": recipient,
        "message": message,
        "booking_id": booking_id,
        "notification_type": notification_type,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"
    }
    NOTIFICATIONS_LOG.append(log_entry)
    print(f"  📨 [{notification_type.upper()}] {channel.upper()} → {recipient}")
    return log_entry


def notify_tourist(tourist_info: dict, message: str,
                    booking_id: str, notification_type: str = "confirmation"):
    """Send all available channels to tourist."""
    sent = []
    if tourist_info.get("phone"):
        send_notification("sms", tourist_info["phone"],
                          message, booking_id, notification_type)
        sent.append("sms")
    if tourist_info.get("email"):
        send_notification("email", tourist_info["email"],
                          message, booking_id, notification_type)
        sent.append("email")
    return sent


def notify_hospital(provider: dict, message: str,
                     booking_id: str, notification_type: str = "confirmation"):
    """
    Send hospital-side notification.
    In production: integrate with hospital's booking portal/API.
    """
    hospital_contact = provider.get("phone") or provider.get("hospital_email")
    if hospital_contact:
        send_notification(
            "hospital_portal",
            hospital_contact,
            message,
            booking_id,
            notification_type
        )
        return True
    return False



# REMINDER SYSTEM 


def schedule_reminder(booking_id: str, appointment_datetime: datetime,
                       tourist_info: dict, provider: dict,
                       reminder_message: str):
    """
    Schedule a reminder 1 hour before appointment using a background thread.
    In production: replace with Celery/APScheduler/cron job.
    """
    now = datetime.now()
    reminder_time = appointment_datetime - timedelta(hours=1)
    delay_seconds = (reminder_time - now).total_seconds()

    if delay_seconds <= 0:
        print(f"  [Reminder] Appointment too soon — sending reminder immediately")
        delay_seconds = 5  # send in 5 seconds for demo

    def _send_reminder():
        time.sleep(delay_seconds)
        booking = BOOKINGS_DB.get(booking_id)
        # Only send if booking is still active
        if booking and booking["status"] not in ("cancelled",):
            print(f"\n  🔔 [REMINDER FIRING] Booking {booking_id}")
            notify_tourist(tourist_info, reminder_message,
                           booking_id, "reminder")
            notify_hospital(provider, reminder_message,
                            booking_id, "reminder")

    thread = threading.Thread(target=_send_reminder, daemon=True)
    thread.start()

    REMINDER_REGISTRY[booking_id] = {
        "thread": thread,
        "scheduled_for": reminder_time.isoformat(),
        "status": "scheduled"
    }
    print(f"  🔔 Reminder scheduled for {reminder_time.strftime('%Y-%m-%d %H:%M')} "
          f"(in {int(delay_seconds/60)} min)")


def cancel_reminder(booking_id: str):
    """
    Mark reminder as cancelled.
    Thread will check booking status before firing.
    """
    if booking_id in REMINDER_REGISTRY:
        REMINDER_REGISTRY[booking_id]["status"] = "cancelled"
        print(f"  [Reminder Cancelled] Booking {booking_id}")



# LLM — Only for message generation


def generate_message(message_type: str, provider: dict,
                      tourist_info: dict, booking_id: str,
                      extra_context: str = "") -> str:
    """
    LLM generates all human-facing messages.
    message_type: "confirmation" | "cancellation" | "reschedule" | "reminder" | "hospital_notice"
    """
    language = tourist_info.get("language_preference", "English")
    name = tourist_info.get("name", "Tourist")
    doctor = provider.get("provider_name", "the doctor")
    clinic = provider.get("clinic_name", "the clinic")
    address = provider.get("address", "")
    date = provider.get("slot_date", "")
    time_slot = provider.get("slot_time", "")

    templates = {
        "confirmation": f"""
Write a warm appointment confirmation message in {language} for {name}.
Doctor: {doctor} | Clinic: {clinic} | Address: {address}
Date: {date} at {time_slot} | Booking ID: {booking_id}
End with: "Please arrive 10 minutes early with valid ID and insurance card."
Keep under 4 sentences.
""",
        "cancellation": f"""
Write a polite appointment cancellation message in {language} for {name}.
Cancelled appointment was with {doctor} at {clinic} on {date} at {time_slot}.
Booking ID: {booking_id}
{extra_context}
Keep under 3 sentences. Be apologetic and helpful.
""",
        "reschedule": f"""
Write a rescheduling confirmation message in {language} for {name}.
New appointment: {doctor} at {clinic}, {address}
New date: {date} at {time_slot} | Booking ID: {booking_id}
Keep under 4 sentences. Be reassuring.
""",
        "reminder": f"""
Write a friendly 1-hour appointment reminder in {language} for {name}.
Appointment with {doctor} at {clinic}, {address}
Time: {time_slot} today | Booking ID: {booking_id}
Keep under 3 sentences. Be warm and prompt.
""",
        "hospital_notice": f"""
Write a professional hospital staff notification in English.
New patient appointment:
- Patient: {name}
- Doctor: {doctor}
- Date: {date} at {time_slot}
- Booking ID: {booking_id}
- Symptoms summary: {extra_context}
Keep under 4 sentences. Professional tone.
"""
    }

    prompt = templates.get(message_type, templates["confirmation"])

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  [LLM Message Error] {e} — using fallback")
        # Deterministic fallback — pipeline never breaks
        fallbacks = {
            "confirmation": f"Dear {name}, your appointment with {doctor} at {clinic} on {date} at {time_slot} is confirmed. Booking ID: {booking_id}. Please arrive 10 minutes early.",
            "cancellation": f"Dear {name}, your appointment (ID: {booking_id}) with {doctor} has been cancelled.",
            "reschedule": f"Dear {name}, your appointment has been rescheduled to {date} at {time_slot} with {doctor}. Booking ID: {booking_id}.",
            "reminder": f"Reminder: Your appointment with {doctor} at {clinic} is in 1 hour ({time_slot}). Booking ID: {booking_id}.",
            "hospital_notice": f"New booking {booking_id}: Patient {name} scheduled with {doctor} on {date} at {time_slot}."
        }
        return fallbacks.get(message_type, f"Booking {booking_id} update.")



# MAIN AGENT CLASS


class BookingCoordinationAgent:
    def __init__(self):
        pass

    def book(self, matched_provider: dict, triage_result: dict,
             tourist_info: dict) -> dict:
        """
        Full booking flow:
        1. Conflict check + confirm
        2. Generate messages (LLM)
        3. Notify tourist (SMS + email)
        4. Notify hospital
        5. Schedule 1-hour reminder
        """

        # ── Step 1: Conflict check + confirm ───────────────────
        try:
            booking = confirm_booking(
                provider_id=matched_provider["provider_id"],
                slot_id=matched_provider["slot_id"],
                tourist_name=tourist_info["name"],
                tourist_phone=tourist_info.get("phone", ""),
                tourist_email=tourist_info.get("email", ""),
                language_preference=tourist_info.get("language_preference", "English"),
                symptoms=triage_result.get("translated_summary", ""),
                severity_score=triage_result.get("severity_score", 5)
            )
        except ValueError as e:
            # Slot conflict — return error for orchestrator to handle
            print(f"  ❌ Slot conflict: {e}")
            return {"error": str(e), "status": "conflict", "action_needed": "select_new_slot"}

        booking_id = booking["id"]

        # ── Step 2: Generate messages (LLM) ────────────────────
        tourist_msg = generate_message(
            "confirmation", matched_provider, tourist_info, booking_id
        )
        hospital_msg = generate_message(
            "hospital_notice", matched_provider, tourist_info, booking_id,
            extra_context=triage_result.get("translated_summary", "")
        )
        reminder_msg = generate_message(
            "reminder", matched_provider, tourist_info, booking_id
        )

        # ── Step 3: Notify tourist ──────────────────────────────
        tourist_channels = notify_tourist(
            tourist_info, tourist_msg, booking_id, "confirmation"
        )

        # ── Step 4: Notify hospital ─────────────────────────────
        hospital_notified = notify_hospital(
            matched_provider, hospital_msg, booking_id, "confirmation"
        )

        # ── Step 5: Schedule 1-hour reminder ────────────────────
        try:
            appt_datetime = datetime.strptime(
                f"{matched_provider['slot_date']} {matched_provider['slot_time']}",
                "%Y-%m-%d %I:%M %p"
            )
            schedule_reminder(
                booking_id, appt_datetime,
                tourist_info, matched_provider, reminder_msg
            )
        except Exception as e:
            print(f"  [Reminder Setup Warning] {e} — reminder not scheduled")

        return {
            "booking_id": booking_id,
            "status": "confirmed",
            "doctor": matched_provider.get("provider_name"),
            "clinic": matched_provider.get("clinic_name"),
            "address": matched_provider.get("address"),
            "appointment_date": matched_provider.get("slot_date"),
            "appointment_time": matched_provider.get("slot_time"),
            "tourist_notifications": tourist_channels,
            "hospital_notified": hospital_notified,
            "reminder_scheduled": booking_id in REMINDER_REGISTRY,
            "confirmation_message": tourist_msg
        }

    def cancel(self, booking_id: str, tourist_info: dict,
                provider: dict, reason: str = "Tourist requested") -> dict:
        """Cancel a booking and notify all parties."""
        result = cancel_booking(booking_id, reason)
        if "error" in result:
            return result

        cancel_msg = generate_message(
            "cancellation", provider, tourist_info, booking_id,
            extra_context=reason
        )
        notify_tourist(tourist_info, cancel_msg, booking_id, "cancellation")
        notify_hospital(provider, cancel_msg, booking_id, "cancellation")

        return {
            "booking_id": booking_id,
            "status": "cancelled",
            "reason": reason,
            "message_sent": cancel_msg
        }

    def reschedule(self, booking_id: str, new_slot_id: str,
                    new_slot_date: str, new_slot_time: str,
                    tourist_info: dict, provider: dict) -> dict:
        """Reschedule booking and notify all parties."""
        # Update provider info with new slot for message generation
        updated_provider = {**provider,
                            "slot_date": new_slot_date,
                            "slot_time": new_slot_time}

        result = reschedule_booking(booking_id, new_slot_id,
                                     new_slot_date, new_slot_time)
        if "error" in result:
            return result

        reschedule_msg = generate_message(
            "reschedule", updated_provider, tourist_info, booking_id
        )
        notify_tourist(tourist_info, reschedule_msg, booking_id, "reschedule")
        notify_hospital(updated_provider, reschedule_msg, booking_id, "reschedule")

        # Schedule new reminder
        try:
            appt_datetime = datetime.strptime(
                f"{new_slot_date} {new_slot_time}", "%Y-%m-%d %I:%M %p"
            )
            reminder_msg = generate_message(
                "reminder", updated_provider, tourist_info, booking_id
            )
            schedule_reminder(booking_id, appt_datetime,
                               tourist_info, updated_provider, reminder_msg)
        except Exception as e:
            print(f"  [Reminder Setup Warning] {e}")

        return {
            "booking_id": booking_id,
            "status": "rescheduled",
            "new_slot_date": new_slot_date,
            "new_slot_time": new_slot_time,
            "message_sent": reschedule_msg
        }


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    matched_provider = {
        "provider_id": "doc-001",
        "provider_name": "Dr. Priya Sharma",
        "clinic_name": "City Health Clinic",
        "address": "12 Park Street, Kolkata",
        "phone": "+91-98765-00001",
        "slot_id": "slot-101",
        "slot_date": "2025-08-05",
        "slot_time": "09:00 AM"
    }
    triage_result = {
        "severity_score": 6,
        "translated_summary": "Fever 102F, body ache, and cough for 2 days."
    }
    tourist_info = {
        "name": "John Smith",
        "language_preference": "English",
        "phone": "+91-9876543210",
        "email": "john.smith@email.com"
    }

    agent = BookingCoordinationAgent()

    # ── Test 1: Normal booking ──────────────────────────
    print("\n" + "="*60)
    print("TEST 1: Normal Booking")
    print("="*60)
    result = agent.book(matched_provider, triage_result, tourist_info)
    print(json.dumps({k: v for k, v in result.items()
                      if k != "booking_details"}, indent=2))

    booking_id = result["booking_id"]

    # ── Test 2: Slot conflict ───────────────────────────
    print("\n" + "="*60)
    print("TEST 2: Slot Conflict (same slot)")
    print("="*60)
    conflict_result = agent.book(matched_provider, triage_result, {
        **tourist_info, "name": "Jane Doe"
    })
    print(json.dumps(conflict_result, indent=2))

    # ── Test 3: Reschedule ──────────────────────────────
    print("\n" + "="*60)
    print("TEST 3: Reschedule")
    print("="*60)
    reschedule_result = agent.reschedule(
        booking_id=booking_id,
        new_slot_id="slot-102",
        new_slot_date="2025-08-06",
        new_slot_time="11:00 AM",
        tourist_info=tourist_info,
        provider=matched_provider
    )
    print(json.dumps(reschedule_result, indent=2))

    # ── Test 4: Cancel ──────────────────────────────────
    print("\n" + "="*60)
    print("TEST 4: Cancellation")
    print("="*60)
    cancel_result = agent.cancel(
        booking_id=booking_id,
        tourist_info=tourist_info,
        provider=matched_provider,
        reason="Tourist feeling better"
    )
    print(json.dumps(cancel_result, indent=2))

    # Keep main thread alive briefly so reminder thread can demo
    print("\n[Waiting 3 seconds to show reminder thread is alive...]")
    time.sleep(3)