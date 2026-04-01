# MediGuide AI 🏥

**AI-Powered Medical Assistant for Tourists in India**

An intelligent multi-agent system that helps international tourists get fast, reliable medical assistance — from symptom checking to hospital discovery, cost estimation, and document generation.

---

### ✨ Features

- **Agent 1**: Multilingual Chat Agent (English, Hindi, Bengali, Spanish, French, etc.)
- **Agent 2**: Intelligent Triage & Severity Assessment
- **Agent 3**: Real-time Nearest Hospital Finder (using Google Places API)
- **Agent 4**: Booking & Coordination Agent
- **Agent 5**: Transparent Cost Estimator with Insurance Calculation
- **Agent 6**: Professional Medical Summary & Insurance Claim Letter Generator (PDF)

### 🛠️ Tech Stack

- **Backend**: Python + FastAPI
- **AI Models**: Anthropic Claude (Primary) + Google Gemini (for Agent 1)
- **APIs**:
  - Google Places API (Hospital search & pricing)
  - CraftMyPDF (Professional PDF generation)
  - Twilio (SMS/WhatsApp notifications - upcoming)
- **Multi-Agent Architecture** with tool-calling

---

### 📁 Project Structure

```bash
mediguide-ai/
├── backend/
│   ├── agent1.py          # Multilingual Chat
│   ├── agent2.py          # Triage & Assessment
│   ├── agent3.py          # Nearest Hospital Finder
│   ├── agent4.py          # Booking Agent
│   ├── agent5.py          # Cost Estimator
│   ├── agent6.py          # Document Generator
│   ├── orchestrator.py    # Main Pipeline
│   ├── requirements.txt
│   └── .env
├── .gitignore
├── README.md
└── venv/
