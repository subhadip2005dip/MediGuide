
# AGENT 2: Triage & Assessment Agent
# Converts intake data → severity score + specialty recommendation
# Uses structured tool-calling style output


import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

TRIAGE_SYSTEM_PROMPT = """
You are a clinical triage AI assistant. You receive symptom intake data from tourists
and produce a structured medical assessment.

Given the intake data, you must output ONLY a valid JSON object (no extra text) like this:

{
  "severity_score": 6,
  "urgency_label": "medium",
  "recommended_specialty": "General Physician",
  "triage_reason": "Patient has moderate fever and body ache for 2 days. No emergency signs.",
  "translated_summary": "Summary in English regardless of input language",
  "red_flags": [],
  "follow_up_questions": [],
  "estimated_visit_type": "in-person"
}

Severity Score Guide:
1-3   → Low       (mild cold, minor ache, rash) → urgency_label: "low"
4-6   → Medium    (fever, infection, sprain)     → urgency_label: "medium"
7-9   → High      (severe pain, breathing issues) → urgency_label: "high"
10    → Emergency (chest pain, stroke signs, unconscious) → urgency_label: "emergency"

Specialty Mapping:
- Fever, cold, general illness       → "General Physician"
- Chest pain, heart concerns         → "Cardiologist"
- Broken bone, injury                → "Orthopedic"
- Eye problems                       → "Ophthalmologist"
- Skin issues                        → "Dermatologist"
- Stomach, digestion                 → "Gastroenterologist"
- Mental health                      → "Psychiatrist"
- Children (under 12)               → "Pediatrician"
- Severe/multi-system/unclear        → "Emergency Medicine"
- Dental pain                        → "Dentist"
- Pregnancy related                  → "Gynecologist"

estimated_visit_type:
- "telemedicine" for low severity (1-3) with no red flags
- "in-person" for medium and above
- "emergency-room" for score 9-10

red_flags: list any warning signs found (e.g., "chest tightness", "high fever 104F+")
follow_up_questions: list any critical info still missing for better triage

Output ONLY the JSON. No explanation, no markdown code blocks.
"""


class TriageAgent:
    def __init__(self):
        pass

    def assess(self, intake_data: dict) -> dict:
        """
        Takes intake_data from Agent 1 and returns triage assessment.
        intake_data: output dict from MultilingualChatAgent
        """
        prompt = f"""
Perform triage assessment for the following tourist medical intake:

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
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            system=TRIAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        # Strip markdown code blocks if model wraps output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        triage_result = json.loads(raw)

        # Add tourist's detected language for downstream agents
        triage_result["detected_language"] = intake_data.get("detected_language", "English")
        triage_result["tourist_name"] = intake_data.get("tourist_name")

        return triage_result

    def print_summary(self, triage_result: dict):
        """Pretty print the triage result."""
        score = triage_result['severity_score']
        emoji = "🟢" if score <= 3 else "🟡" if score <= 6 else "🔴"

        print("\n" + "=" * 50)
        print("  TRIAGE ASSESSMENT REPORT")
        print("=" * 50)
        print(f"  Severity Score : {emoji} {score}/10  ({triage_result['urgency_label'].upper()})")
        print(f"  Specialty      : {triage_result['recommended_specialty']}")
        print(f"  Visit Type     : {triage_result['estimated_visit_type']}")
        print(f"  Reason         : {triage_result['triage_reason']}")
        if triage_result.get("red_flags"):
            print(f"  ⚠️  Red Flags   : {', '.join(triage_result['red_flags'])}")
        print("=" * 50)


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulated intake from Agent 1
    sample_intake = {
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

    agent = TriageAgent()
    result = agent.assess(sample_intake)
    agent.print_summary(result)

    print("\nFull Triage JSON:")
    print(json.dumps(result, indent=2))