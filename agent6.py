
# AGENT 6: Document Generator Agent (Real PDF Generation)
# Generates professional Medical Summary + Insurance Claim Letter PDFs
# Uses CraftMyPDF API (Recommended) + fallback text version

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ── Configuration ─────────────────────────────────────────────────────────────
CRAFTMYPDF_API_KEY = os.getenv("CRAFTMYPDF_API_KEY")
CRAFTMYPDF_MEDICAL_SUMMARY_TEMPLATE = os.getenv("CRAFTMYPDF_MEDICAL_SUMMARY_TEMPLATE", "med_summary_template")
CRAFTMYPDF_CLAIM_LETTER_TEMPLATE = os.getenv("CRAFTMYPDF_CLAIM_LETTER_TEMPLATE", "claim_letter_template")

if not CRAFTMYPDF_API_KEY:
    print("WARNING: CRAFTMYPDF_API_KEY not found. PDF generation will fallback to text only.")

# ── Real PDF Generation using CraftMyPDF API ─────────────────────────────────
def generate_pdf_via_craftmypdf(template_id: str, data: dict) -> dict:
    """Generate PDF using CraftMyPDF API"""
    if not CRAFTMYPDF_API_KEY:
        return {"error": "PDF API key not configured", "pdf_url": None}

    url = "https://api.craftmypdf.com/v1/create"
    
    payload = {
        "template_id": template_id,
        "data": data,
        "output": "url",           # Returns direct PDF URL
        "expiration": 86400        # 24 hours
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": CRAFTMYPDF_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "pdf_url": result.get("url"),
            "pdf_id": result.get("id"),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[CraftMyPDF Error] {e}")
        return {"error": str(e), "pdf_url": None}


# ── Tool Implementations (Improved) ───────────────────────────────────────────
def generate_medical_summary(tourist_name: str, symptoms: str, triage_reason: str,
                             severity_score: int, recommended_specialty: str,
                             doctor_name: str, hospital_name: str,
                             appointment_date: str, appointment_time: str,
                             allergies: str = "None", medications: str = "None") -> dict:
    
    document = {
        "document_type": "Medical Summary",
        "generated_at": datetime.now().isoformat(),
        "patient_name": tourist_name,
        "chief_complaint": symptoms,
        "clinical_notes": triage_reason,
        "severity_score": severity_score,
        "recommended_specialty": recommended_specialty,
        "assigned_doctor": doctor_name,
        "hospital_name": hospital_name,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "known_allergies": allergies,
        "current_medications": medications,
        "generated_by": "MediGuide AI - Intelligent Health Assistant"
    }

    # Generate PDF
    pdf_result = generate_pdf_via_craftmypdf(CRAFTMYPDF_MEDICAL_SUMMARY_TEMPLATE, document)

    return {
        **document,
        "pdf_url": pdf_result.get("pdf_url"),
        "pdf_status": "generated" if pdf_result.get("pdf_url") else "text_fallback"
    }


def generate_claim_letter(tourist_name: str, insurance_plan: str, booking_id: str,
                          doctor_name: str, hospital_name: str, appointment_date: str,
                          symptoms: str, estimated_cost_inr: float,
                          covered_amount_inr: float, out_of_pocket_inr: float) -> dict:
    
    document = {
        "document_type": "Insurance Claim Letter",
        "generated_at": datetime.now().isoformat(),
        "claim_reference": f"CLM-{booking_id}-{datetime.now().strftime('%Y%m%d')}",
        "policyholder": tourist_name,
        "policy_plan": insurance_plan,
        "provider_name": doctor_name,
        "hospital_name": hospital_name,
        "date_of_service": appointment_date,
        "diagnosis_description": symptoms,
        "total_estimated_cost_inr": round(estimated_cost_inr, 2),
        "claimed_amount_inr": round(covered_amount_inr, 2),
        "patient_liability_inr": round(out_of_pocket_inr, 2),
        "supporting_documents_needed": [
            "Original payment receipts",
            "Doctor's prescription and clinical notes",
            "Laboratory / Imaging reports (if applicable)",
            "Copy of passport / ID",
            "Insurance policy card"
        ],
        "submission_instructions": "Submit this letter with all supporting documents to your insurance provider within 30 days of the date of service."
    }

    pdf_result = generate_pdf_via_craftmypdf(CRAFTMYPDF_CLAIM_LETTER_TEMPLATE, document)

    return {
        **document,
        "pdf_url": pdf_result.get("pdf_url"),
        "pdf_status": "generated" if pdf_result.get("pdf_url") else "text_fallback"
    }


def format_document_as_text(document: dict) -> dict:
    """Fallback: Format document as readable text"""
    lines = [f"{'='*70}", f"  {document.get('document_type', 'DOCUMENT').upper()}", f"{'='*70}"]
    
    for key, value in document.items():
        if key in ["document_type", "generated_at", "pdf_url", "pdf_status"]:
            continue
        formatted_key = key.replace("_", " ").title()
        if isinstance(value, list):
            lines.append(f"\n{formatted_key}:")
            for item in value:
                lines.append(f"   • {item}")
        else:
            lines.append(f"{formatted_key}: {value}")
    
    lines.append("="*70)
    return {
        "formatted_text": "\n".join(lines),
        "document_type": document.get("document_type"),
        "pdf_url": document.get("pdf_url")
    }


# ── Tool Definitions ─────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "generate_medical_summary",
        "description": "Generate a professional medical summary with PDF (if API configured).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tourist_name": {"type": "string"},
                "symptoms": {"type": "string"},
                "triage_reason": {"type": "string"},
                "severity_score": {"type": "integer"},
                "recommended_specialty": {"type": "string"},
                "doctor_name": {"type": "string"},
                "hospital_name": {"type": "string"},
                "appointment_date": {"type": "string"},
                "appointment_time": {"type": "string"},
                "allergies": {"type": "string"},
                "medications": {"type": "string"}
            },
            "required": ["tourist_name", "symptoms", "triage_reason", "severity_score",
                         "recommended_specialty", "doctor_name", "hospital_name",
                         "appointment_date", "appointment_time"]
        }
    },
    {
        "name": "generate_claim_letter",
        "description": "Generate an insurance claim letter with PDF support.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tourist_name": {"type": "string"},
                "insurance_plan": {"type": "string"},
                "booking_id": {"type": "string"},
                "doctor_name": {"type": "string"},
                "hospital_name": {"type": "string"},
                "appointment_date": {"type": "string"},
                "symptoms": {"type": "string"},
                "estimated_cost_inr": {"type": "number"},
                "covered_amount_inr": {"type": "number"},
                "out_of_pocket_inr": {"type": "number"}
            },
            "required": ["tourist_name", "insurance_plan", "booking_id", "doctor_name",
                         "hospital_name", "appointment_date", "symptoms",
                         "estimated_cost_inr", "covered_amount_inr", "out_of_pocket_inr"]
        }
    },
    {
        "name": "format_document_as_text",
        "description": "Convert document dict into nicely formatted text.",
        "input_schema": {
            "type": "object",
            "properties": {"document": {"type": "object"}},
            "required": ["document"]
        }
    }
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "generate_medical_summary":
        return json.dumps(generate_medical_summary(**inputs))
    elif name == "generate_claim_letter":
        return json.dumps(generate_claim_letter(**inputs))
    elif name == "format_document_as_text":
        return json.dumps(format_document_as_text(**inputs))
    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Document Generator Agent ─────────────────────────────────────────────────
class DocumentGeneratorAgent:
    def __init__(self):
        self.messages = []

    def generate(self, intake_data: dict, triage_result: dict,
                 booking_confirmation: dict, cost_estimate: dict,
                 tourist_info: dict) -> dict:
        
        has_insurance = tourist_info.get("insurance_plan", "no_insurance") != "no_insurance"
        hospital_name = booking_confirmation.get("hospital_name") or booking_confirmation.get("clinic", "City Health Clinic")

        system_prompt = f"""
You are a professional medical document generator for international tourists.

Generate high-quality documents using the available tools.

Required:
1. ALWAYS generate a **Medical Summary** using generate_medical_summary tool
2. If the tourist has insurance, ALSO generate an **Insurance Claim Letter**

Available Data:
- Patient: {tourist_info.get('name')}
- Symptoms: {intake_data.get('original_complaint') or triage_result.get('translated_summary')}
- Triage Reason: {triage_result.get('triage_reason')}
- Severity: {triage_result.get('severity_score')}/10
- Specialty: {triage_result.get('recommended_specialty')}
- Doctor: {booking_confirmation.get('doctor_name') or booking_confirmation.get('doctor')}
- Hospital/Clinic: {hospital_name}
- Appointment: {booking_confirmation.get('appointment_date')} {booking_confirmation.get('appointment_time', '')}
- Booking ID: {booking_confirmation.get('booking_id')}
- Allergies: {intake_data.get('allergies', 'None')}
- Current Medications: {intake_data.get('medications', 'None')}
- Total Estimated Cost: ₹{cost_estimate.get('cost_breakdown_inr', {}).get('total_estimated', 0)}
- Insurance Covered: ₹{cost_estimate.get('insurance', {}).get('covered_inr', 0)}
- Out of Pocket: ₹{cost_estimate.get('insurance', {}).get('out_of_pocket_inr', 0)}

After generating documents with tools, format them using format_document_as_text, then output ONLY this JSON:

{{
  "medical_summary": {{
    "formatted_text": "...",
    "pdf_url": "https://... (if available)"
  }},
  "claim_letter": {{
    "formatted_text": "... or null",
    "pdf_url": "https://... or null"
  }},
  "documents_generated": ["medical_summary", "claim_letter"] or ["medical_summary"],
  "status": "complete",
  "generated_at": "..."
}}
"""

        self.messages = [{"role": "user", "content": "Generate professional medical documents for this tourist."}]

        while True:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
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
                    raw = raw.split("```")[1].strip()
                    if raw.lower().startswith("json"):
                        raw = raw[4:].strip()
                try:
                    return json.loads(raw)
                except:
                    return {"error": "Failed to parse document JSON"}

            # Tool handling
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    print(f"  [DocumentGenerator] {block.name} called")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            self.messages.append({"role": "user", "content": tool_results})


# ── Test Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    intake_data = {
        "original_complaint": "Fever, headache and body ache since yesterday",
        "allergies": "Penicillin",
        "medications": "Paracetamol 500mg"
    }

    triage_result = {
        "severity_score": 6,
        "recommended_specialty": "General Physician",
        "triage_reason": "Fever and body ache for 2 days. Moderate severity.",
        "translated_summary": "Tourist has fever 102F, body ache, cough."
    }

    booking_confirmation = {
        "booking_id": "BK-AB123456",
        "doctor_name": "Dr. Priya Sharma",
        "hospital_name": "Apollo Gleneagles Hospital",
        "clinic": "City Health Clinic",
        "appointment_date": "2025-08-05",
        "appointment_time": "09:00 AM"
    }

    cost_estimate = {
        "cost_breakdown_inr": {"total_estimated": 1850},
        "insurance": {"covered_inr": 1480, "out_of_pocket_inr": 370}
    }

    tourist_info = {
        "name": "John Smith",
        "insurance_plan": "standard_tourist"
    }

    agent = DocumentGeneratorAgent()
    result = agent.generate(intake_data, triage_result, booking_confirmation, cost_estimate, tourist_info)

    print("\n✅ Documents Generated Successfully!\n")
    print(json.dumps(result, indent=2))