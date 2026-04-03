
# AGENT 2: Triage & Assessment Agent (Upgraded)
# New: Confidence score, escalation path,
# age/gender consideration, second opinion

import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


# TRIAGE PROMPT — now includes confidence + age/gender


TRIAGE_SYSTEM_PROMPT = """
You are a clinical triage AI assistant for tourists. You receive symptom intake data
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


# SECOND OPINION PROMPT — only triggered for borderline


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



# PURE PYTHON ESCALATION LOGIC


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


def check_red_flags_in_text(text: str) -> list:
    """
    Pure Python red flag detection from raw complaint text.
    Acts as a safety net independent of LLM output.
    """
    found = []
    text_lower = text.lower()
    for flag in RED_FLAG_KEYWORDS:
        if flag in text_lower:
            found.append(flag)
    return found


def apply_escalation(triage_result: dict, python_red_flags: list) -> dict:
    """
    Pure Python escalation logic.
    Overrides LLM score if Python detects red flags the LLM missed.
    """
    # If Python found red flags but LLM didn't escalate — override
    if python_red_flags and triage_result["severity_score"] < 8:
        print(f"  [Escalation Override] Python detected red flags: {python_red_flags}")
        triage_result["severity_score"] = max(triage_result["severity_score"], 8)
        triage_result["urgency_label"] = "high"
        triage_result["red_flags"] = list(set(
            triage_result.get("red_flags", []) + python_red_flags
        ))
        triage_result["escalation_override"] = True

    # Assign escalation path based on final urgency
    urgency = triage_result["urgency_label"]
    triage_result["escalation"] = ESCALATION_PATHS.get(urgency, ESCALATION_PATHS["medium"])

    return triage_result


def apply_age_gender_adjustment(triage_result: dict, age: int = None,
                                 gender: str = None) -> dict:
    """
    Pure Python age/gender severity adjustments.
    Supplements LLM's age_gender_note with actual score changes.
    """
    if age is None:
        return triage_result

    original_score = triage_result["severity_score"]
    specialty = triage_result["recommended_specialty"]
    red_flags = triage_result.get("red_flags", [])
    notes = []

    # Child under 5 with fever
    if age < 5 and "fever" in triage_result.get("translated_summary", "").lower():
        triage_result["severity_score"] = min(original_score + 1, 10)
        triage_result["recommended_specialty"] = "Pediatrician"
        notes.append("Child under 5 with fever — severity increased, redirected to Pediatrician")

    # Elderly with any cardiac symptoms
    elif age >= 65 and specialty == "Cardiologist":
        triage_result["severity_score"] = min(original_score + 1, 10)
        red_flags.append("elderly patient with cardiac symptoms")
        notes.append("Elderly patient with cardiac concern — severity increased")

    # Pregnant with abdominal issues
    elif gender == "female" and specialty == "Gynecologist":
        red_flags.append("pregnancy-related abdominal concern")
        notes.append("Pregnant patient — added red flag for monitoring")

    # Male 40+ with chest/arm/jaw pain
    elif gender == "male" and age >= 40 and "Cardiologist" in specialty:
        red_flags.append("male 40+ with possible cardiac symptoms")
        notes.append("Male 40+ with cardiac symptoms — added red flag")

    if notes:
        triage_result["age_gender_adjustments"] = notes
        triage_result["red_flags"] = red_flags

    return triage_result



# TRIAGE AGENT CLASS


class TriageAgent:
    def __init__(self):
        pass

    def _call_llm(self, prompt: str, system: str) -> str:
        """Single LLM call with system prompt prepended."""
        full_prompt = f"{system}\n\n{prompt}"
        response = client.invoke(full_prompt)
        # LangChain Gemini returns AIMessage — content is a string
        raw = response.content
        if isinstance(raw, list):
            raw = raw[0].get("text", "") if isinstance(raw[0], dict) else str(raw[0])
        return raw.strip()

    def _parse_json(self, raw: str) -> dict:
        """Strip markdown fences and parse JSON safely."""
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def _get_second_opinion(self, intake_data: dict,
                             first_result: dict) -> dict:
        """
        Triggered only when severity is borderline (5 or 6).
        LLM reviews the case again independently.
        """
        print("  [Second Opinion] Borderline score detected — requesting review...")

        prompt = f"""
First triage result:
{json.dumps(first_result, indent=2)}

Original intake:
- Symptoms: {', '.join(intake_data.get('symptoms', []))}
- Duration: {intake_data.get('duration', 'unknown')}
- Severity self-reported: {intake_data.get('severity_self_reported', 'unknown')}
- Allergies: {intake_data.get('allergies', 'none')}
- Existing conditions: {intake_data.get('existing_conditions', 'none')}

Provide your second opinion now.
"""
        try:
            raw = self._call_llm(prompt, SECOND_OPINION_PROMPT)
            second = self._parse_json(raw)

            # If second opinion escalates — use higher score
            if second.get("escalate") or second["second_opinion_score"] > first_result["severity_score"]:
                first_result["severity_score"] = second["second_opinion_score"]
                first_result["urgency_label"] = (
                    "high" if first_result["severity_score"] >= 7
                    else "medium"
                )
                first_result["recommended_specialty"] = second.get(
                    "final_recommended_specialty",
                    first_result["recommended_specialty"]
                )
                print(f"  [Second Opinion] Score adjusted to {first_result['severity_score']}")
            else:
                print(f"  [Second Opinion] Confirms original score {first_result['severity_score']}")

            first_result["second_opinion"] = second

        except Exception as e:
            print(f"  [Second Opinion] Failed: {e} — keeping original score")

        return first_result

    def assess(self, intake_data: dict,
               age: int = None, gender: str = None) -> dict:
        """
        Full triage assessment with all upgrades.

        Args:
            intake_data : output from Agent 1
            age         : tourist's age (optional but improves accuracy)
            gender      : 'male' / 'female' / 'other' (optional)

        Returns:
            triage_result dict with confidence, escalation, adjustments
        """

        # ── Step 1: Python pre-check for obvious red flags ──────
        original_complaint = intake_data.get("original_complaint", "")
        python_red_flags = check_red_flags_in_text(original_complaint)
        if python_red_flags:
            print(f"  [Pre-check] Python red flags found: {python_red_flags}")

        # ── Step 2: Primary LLM triage call ─────────────────────
        age_context = f"Age: {age}" if age else "Age: not provided"
        gender_context = f"Gender: {gender}" if gender else "Gender: not provided"

        prompt = f"""
Perform triage assessment for the following tourist medical intake:

{age_context}
{gender_context}
Detected Language: {intake_data.get('detected_language', 'English')}
Original Complaint: {intake_data.get('original_complaint', 'Not provided')}
Symptoms: {', '.join(intake_data.get('symptoms', []))}
Duration: {intake_data.get('duration', 'Unknown')}
Self-Reported Severity: {intake_data.get('severity_self_reported', 'Unknown')}
Allergies: {intake_data.get('allergies', 'None mentioned')}
Existing Conditions: {intake_data.get('existing_conditions', 'None mentioned')}
Current Medications: {intake_data.get('medications', 'None mentioned')}

Produce the triage JSON now.
"""
        try:
            raw = self._call_llm(prompt, TRIAGE_SYSTEM_PROMPT)
            triage_result = self._parse_json(raw)
        except Exception as e:
            print(f"  [Triage LLM Error] {e}")
            # Safe fallback — don't crash the pipeline
            triage_result = {
                "severity_score": 5,
                "urgency_label": "medium",
                "recommended_specialty": "General Physician",
                "triage_reason": "Assessment failed — defaulting to medium severity",
                "translated_summary": original_complaint,
                "red_flags": python_red_flags,
                "follow_up_questions": [],
                "estimated_visit_type": "in-person",
                "confidence_score": 0.2,
                "confidence_reason": "LLM assessment failed — low confidence fallback",
                "age_gender_note": "Not assessed"
            }

        # ── Step 3: Age/gender Python adjustment ────────────────
        triage_result = apply_age_gender_adjustment(triage_result, age, gender)

        # ── Step 4: Red flag escalation (Python override) ───────
        triage_result = apply_escalation(triage_result, python_red_flags)

        # ── Step 5: Second opinion for borderline scores ─────────
        if triage_result["severity_score"] in (5, 6):
            triage_result = self._get_second_opinion(intake_data, triage_result)

        # ── Step 6: Add metadata ─────────────────────────────────
        triage_result["detected_language"] = intake_data.get("detected_language", "English")
        triage_result["tourist_name"] = intake_data.get("tourist_name")
        triage_result["assessed_age"] = age
        triage_result["assessed_gender"] = gender

        return triage_result

    def print_summary(self, triage_result: dict):
        score = triage_result["severity_score"]
        confidence = triage_result.get("confidence_score", "N/A")
        emoji = "🟢" if score <= 3 else "🟡" if score <= 6 else "🔴"

        print("\n" + "=" * 55)
        print("  TRIAGE ASSESSMENT REPORT")
        print("=" * 55)
        print(f"  Severity Score  : {emoji} {score}/10  ({triage_result['urgency_label'].upper()})")
        print(f"  Confidence      : {confidence} — {triage_result.get('confidence_reason', '')}")
        print(f"  Specialty       : {triage_result['recommended_specialty']}")
        print(f"  Visit Type      : {triage_result['estimated_visit_type']}")
        print(f"  Reason          : {triage_result['triage_reason']}")

        if triage_result.get("red_flags"):
            print(f"  ⚠️  Red Flags   : {', '.join(triage_result['red_flags'])}")

        if triage_result.get("age_gender_adjustments"):
            print(f"  👤 Adjustments  : {'; '.join(triage_result['age_gender_adjustments'])}")

        if triage_result.get("second_opinion"):
            so = triage_result["second_opinion"]
            agreed = "✅ Agrees" if so.get("agrees_with_first") else "⚠️ Disagrees"
            print(f"  🔍 2nd Opinion  : {agreed} — {so.get('adjustment_reason', '')}")

        escalation = triage_result.get("escalation", {})
        print(f"  🚦 Action       : {escalation.get('action', 'STANDARD_BOOKING')}")
        print(f"  💬 Message      : {escalation.get('message', '')}")
        print("=" * 55)


# ── Entry point ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_intake = {
        "detected_language": "English",
        "original_complaint": "I have chest tightness and fever since yesterday",
        "symptoms": ["chest tightness", "fever", "body ache"],
        "duration": "1 day",
        "severity_self_reported": "moderate",
        "allergies": "penicillin",
        "existing_conditions": "none",
        "medications": "paracetamol",
        "tourist_name": "John Smith",
        "ready_for_triage": True
    }

    agent = TriageAgent()

    # Pass age + gender for better accuracy
    result = agent.assess(sample_intake, age=45, gender="male")
    agent.print_summary(result)

    print("\nFull Triage JSON:")
    print(json.dumps(result, indent=2))