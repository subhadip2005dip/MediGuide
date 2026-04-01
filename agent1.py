
# AGENT 1: Multilingual Chat Agent
# Handles tourist-facing symptom intake
# Supports: English, Hindi, Bengali, Spanish, French, etc.

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

client = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

SUPPORTED_LANGUAGES = [
    "English", "Hindi", "Bengali", "Spanish", "French",
    "Arabic", "Mandarin", "Japanese", "German", "Portuguese"
]

SYSTEM_PROMPT = """
You are MediGuide, a compassionate multilingual medical intake assistant for tourists.

Your responsibilities:
1. Detect the language the tourist is speaking and respond in the SAME language
2. Collect symptoms in a warm, non-alarming way
3. Ask follow-up questions to understand:
   - What symptoms they have
   - How long they've had them
   - Severity (mild/moderate/severe in their words)
   - Any known allergies or existing conditions
   - Current medications if any
4. Once you have enough information (at least symptoms + duration), output a structured JSON block like this:

<INTAKE_COMPLETE>
{
  "detected_language": "English",
  "original_complaint": "I have fever and headache since yesterday",
  "symptoms": ["fever", "headache"],
  "duration": "1 day",
  "severity_self_reported": "moderate",
  "allergies": "none mentioned",
  "existing_conditions": "none mentioned",
  "medications": "none mentioned",
  "tourist_name": "extracted if mentioned, else null",
  "ready_for_triage": true
}
</INTAKE_COMPLETE>

Rules:
- Never diagnose
- Never recommend specific medicines
- Be warm, calm, and reassuring
- If tourist seems in emergency (chest pain, can't breathe, unconscious), immediately output:
  <EMERGENCY>true</EMERGENCY> and advise calling local emergency number
- Keep conversation natural, not like a form
"""

class MultilingualChatAgent:
    def __init__(self):
        self.messages = []
        self.intake_data = None

    def chat(self, user_message: str) -> dict:
        """
        Single turn of conversation.
        Returns: {reply, intake_complete, intake_data, is_emergency}
        """
        self.messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model="gemini-2.5-flash",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=self.messages
        )

        reply = response.content[0].text
        self.messages.append({"role": "assistant", "content": reply})

        # Check for emergency
        is_emergency = "<EMERGENCY>true</EMERGENCY>" in reply

        # Check if intake is complete
        intake_complete = False
        intake_data = None
        if "<INTAKE_COMPLETE>" in reply and "</INTAKE_COMPLETE>" in reply:
            import json
            start = reply.index("<INTAKE_COMPLETE>") + len("<INTAKE_COMPLETE>")
            end = reply.index("</INTAKE_COMPLETE>")
            json_str = reply[start:end].strip()
            intake_data = json.loads(json_str)
            intake_complete = True
            self.intake_data = intake_data
            # Clean reply to remove raw JSON block for display
            reply = reply[:reply.index("<INTAKE_COMPLETE>")].strip()

        return {
            "reply": reply,
            "intake_complete": intake_complete,
            "intake_data": intake_data,
            "is_emergency": is_emergency
        }

    def run_interactive(self) -> dict:
        """Run a full interactive session until intake is complete."""
        print("=" * 55)
        print("  MediGuide — Medical Assistant for Tourists")
        print("  Type your symptoms in any language")
        print("=" * 55)

        # Opening message
        opening = self.chat("Hello, I need medical help")
        print(f"\nMediGuide: {opening['reply']}\n")

        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            result = self.chat(user_input)

            if result["is_emergency"]:
                print(f"\n🚨 MediGuide: {result['reply']}")
                print("\n🚨 EMERGENCY DETECTED — Call 112 (India) or go to nearest ER immediately!")
                return {"emergency": True}

            print(f"\nMediGuide: {result['reply']}\n")

            if result["intake_complete"]:
                print("\n✅ Symptom intake complete. Passing to Triage Agent...\n")
                return result["intake_data"]


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = MultilingualChatAgent()
    intake_result = agent.run_interactive()
    print("\nIntake Data Collected:")
    import json
    print(json.dumps(intake_result, indent=2))