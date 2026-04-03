# MediGuide AI 🏥

**AI-Powered Medical Assistant for Tourists in India**

An intelligent multi-agent system that helps international tourists get fast, reliable medical assistance — from symptom checking to hospital discovery, cost estimation, and document generation. Built with Claude AI (Anthropic), Google Gemini, FastAPI, and Next.js.

**[Jump to Setup](#-quick-start) | [API Docs](#-api-endpoints) | [Architecture](#-architecture)**

---

## ✨ Features

### 🤖 Six Specialized Agents

| Agent       | Purpose                                     | Key Approach                                                              |
| ----------- | ------------------------------------------- | ------------------------------------------------------------------------- |
| **Agent 1** | Multilingual Symptom Intake                 | LangChain Gemini — conversational, language-aware                         |
| **Agent 2** | Intelligent Triage & Severity Assessment    | Claude AI — confidence score, escalation, second opinion                  |
| **Agent 3** | Real-time Nearest Hospital Finder           | Google Places API + Python logic — LLM for summary only                   |
| **Agent 4** | Smart Booking & Coordination                | Python-first — slot conflict detection, reminders, hospital notifications |
| **Agent 5** | Transparent Cost Estimator                  | Python logic + Insurance API + Razorpay payment links                     |
| **Agent 6** | Medical Summary & Insurance Claim Generator | Claude AI + CraftMyPDF — PDF generation                                   |

### 💡 Key Capabilities

- **🌍 Multilingual Support**: English, Hindi, Bengali, Spanish, French, Arabic, and 15+ more
- **🏥 Real-time Hospital Discovery**: Google Places Nearby Search with live ratings, distance, and ambulance routing
- **🩺 Intelligent Triage**: Severity scoring with confidence rating, red flag detection, age/gender adjustment, and second opinion for borderline cases
- **📅 Smart Booking**: Slot conflict detection, cancellation/rescheduling flow, hospital-side notifications, 1-hour reminders
- **💰 Transparent Pricing**: Insurance API verification, pre-authorization checks, Razorpay payment links, cheaper alternative suggestions
- **📋 Professional Documentation**: Auto-generated medical summaries and insurance claim letters
- **🚨 Emergency Escalation**: Automatic protocol based on severity — Python logic, not LLM prompts

### 🧠 Core Design Principle

> **Python handles logic. LLM handles language.**

Every agent follows this rule:

- Sorting, filtering, math, ranking, conflict detection → **pure Python**
- Friendly messages, multilingual summaries, medical reasoning → **LLM**

---

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI + Uvicorn
- **AI Models**:
  - Anthropic Claude 3.5 Sonnet (triage, booking messages, cost summaries, documents)
  - Google Gemini 2.5 Flash via LangChain (multilingual chat — Agent 1 only)
- **Database**: MongoDB with Motor (async driver)
- **External APIs**:
  - Google Places API (Nearby Search + Text Search for hospitals)
  - Google Directions API (real-time ambulance routing)
  - Insurance API (coverage verification + pre-authorization)
  - Razorpay API (payment link generation)
  - CraftMyPDF (PDF generation for Agent 6)
  - Clerk API (authentication)
  - Svix (webhook handling)

### Frontend

- **Framework**: Next.js 16.2 with TypeScript
- **UI Components**: Shadcn/ui with Radix UI
- **Authentication**: Clerk
- **Styling**: Tailwind CSS v4
- **Icons**: Lucide React

### Deployment & Infrastructure

- Backend: FastAPI server (Docker-ready)
- Frontend: Next.js (Vercel-ready)
- Database: MongoDB Atlas (cloud)

---

## 📁 Project Structure

```bash
MediGuide/
├── backend/
│   ├── agent1.py              # Multilingual chat & intake (LangChain Gemini)
│   ├── agent2.py              # Triage — confidence score, escalation, second opinion
│   ├── agent3.py              # Hospital finder — Python logic + ambulance routing
│   ├── agent4.py              # Booking — conflict detection, reminders, hospital notify
│   ├── agent5.py              # Cost — insurance API, pre-auth, payment links, alternatives
│   ├── agent6.py              # Document generation — medical summary + claim letter PDF
│   ├── orchestrator.py        # Main pipeline orchestrator
│   ├── main.py                # FastAPI server
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── src/
│       ├── utils.py           # Utility functions
│       └── routes/
│           └── webhooks.py    # Webhook handlers
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout with auth
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   └── ui/                # Shadcn UI components
│   ├── lib/
│   │   └── utils.ts           # Client utilities
│   ├── public/                # Static assets
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── README.md
│
├── README.md
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (or local MongoDB)
- API Keys (see Environment Variables section)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cat > .env << EOF
# AI
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Google APIs
GOOGLE_PLACES_API_KEY=...
GOOGLE_DIRECTIONS_API_KEY=...

# Database
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/mediguide

# Auth
CLERK_SECRET_KEY=...

# Insurance API
INSURANCE_API_URL=https://your-insurer-api.com
INSURANCE_API_KEY=...

# Payment
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...

# Document Generation
CRAFT_MY_PDF_API_KEY=...
EOF

# 5. Run the FastAPI server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

cat > .env.local << EOF
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

npm run dev
```

---

## 🏗️ Architecture

### Agent Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (Web/Mobile)                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    AGENT 1      │
                    │  Multilingual   │
                    │  Chat & Intake  │
                    │  (Gemini)       │
                    └────────┬────────┘
                             │ symptoms, language, duration
                    ┌────────▼─────────┐
                    │    AGENT 2       │
                    │  Triage +        │
                    │  Confidence +    │
                    │  Escalation Path │
                    └────────┬─────────┘
                             │ severity, specialty, escalation
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      ┌───▼────┐    ┌────────▼───────┐    ┌────▼────┐
      │AGENT 3 │    │  EMERGENCY?    │    │AGENT 4  │
      │Hospital│    │  score >= 10   │    │ Booking │
      │Finder  │    │  → Call 112    │    │+Conflict│
      │+Routing│    └────────────────┘    │+Remind  │
      └───┬────┘                          └────┬────┘
          │                                    │
          └──────────────┬─────────────────────┘
                         │
               ┌─────────▼──────────┐
               │     AGENT 5        │
               │  Cost Estimator    │
               │  + Insurance API   │
               │  + Payment Link    │
               │  + Alternatives    │
               └─────────┬──────────┘
                         │
               ┌─────────▼──────────┐
               │     AGENT 6        │
               │  Doc Generator     │
               │  Medical PDF +     │
               │  Claim Letter      │
               └─────────┬──────────┘
                         │
               ┌─────────▼──────────────────┐
               │  Final Output              │
               │  • Booking confirmation    │
               │  • Cost breakdown          │
               │  • Payment link            │
               │  • Medical documents       │
               │  • Insurance claim letter  │
               └────────────────────────────┘
```

### Key Design Decisions

1. **Python-first logic**: Sorting, filtering, conflict detection, math, and escalation routing are all pure Python — not delegated to LLM prompts
2. **LLM for language only**: Each agent uses LLM only for tasks that require natural language (multilingual messages, triage reasoning, document text)
3. **Graceful fallbacks**: Every external API (Google, Insurance, Razorpay) has a mock fallback so the pipeline never crashes
4. **Single client per agent**: All agents use either Anthropic OR LangChain Gemini — never mixed in the same file
5. **Sequential agent chain**: Each agent passes structured output to the next, building context progressively

---

## 🎯 Agent Details

### Agent 1: Multilingual Chat Agent

<<<<<<< HEAD

=======

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **AI**: Google Gemini 2.5 Flash via LangChain (`.invoke()`)
- **Inputs**: Tourist's free-text symptom description in any language
- **Outputs**: Structured intake JSON — symptoms, duration, allergies, detected language
- **Key features**:
  - Detects language and responds in same language throughout
  - `<INTAKE_COMPLETE>` XML tag signals pipeline handoff
  - `<EMERGENCY>true</EMERGENCY>` triggers immediate emergency protocol
  - Multi-turn conversation until sufficient data is collected

<<<<<<< HEAD

### Agent 2: Triage & Severity Assessment _(Upgraded)_

=======

### Agent 2: Triage & Severity Assessment _(Upgraded)_

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **AI**: Claude claude-opus-4-5
- **Inputs**: Intake data from Agent 1, optional age + gender
- **Outputs**: Severity score, specialty, confidence score, escalation path
- **Upgrades added**:
  - **Confidence score** (0.0–1.0): How certain the triage is, based on completeness of intake data
  - **Escalation path**: Python maps every urgency level to a concrete action (CALL_EMERGENCY / PRIORITY_BOOKING / TELEMEDICINE)
  - **Age/gender adjustment**: Pure Python rules adjust severity for children under 5, elderly with cardiac symptoms, pregnant patients, males 40+ with chest pain
  - **Second opinion**: Triggered automatically when score is borderline (5 or 6) — second LLM call reviews independently, higher score wins
  - **Python red flag safety net**: Keyword scan catches critical terms (chest pain, can't breathe) independent of LLM output

<<<<<<< HEAD

### Agent 3: Nearest Hospital Finder _(Refactored)_

=======

### Agent 3: Nearest Hospital Finder _(Refactored)_

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **APIs**: Google Places Nearby Search + Google Directions API
- **AI**: Claude — only for final tourist-facing message
- **Inputs**: Triage result, tourist location (lat/lon)
- **Outputs**: Best hospital match with real travel time
- **Key design**:
  - All ranking logic is pure Python (`pick_best_hospital()` weighted scoring)
  - High severity (8+): sort purely by distance
  - Normal: 60% distance weight + 40% rating weight
  - Real-time ambulance routing via Directions API for severity 7+
  - Mock hospital fallback when Google API unavailable

<<<<<<< HEAD

### Agent 4: Booking & Coordination _(Upgraded)_

=======

### Agent 4: Booking & Coordination _(Upgraded)_

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **AI**: Claude — only for generating notification messages
- **Inputs**: Matched provider, triage result, tourist info
- **Outputs**: Booking confirmation, notifications sent status
- **Upgrades added**:
  - **Slot conflict detection**: `SLOTS_DB` tracks locked slots — raises `ValueError` on double-booking
  - **Cancellation flow**: `cancel()` method releases slot, notifies tourist + hospital, cancels reminder
  - **Rescheduling flow**: `reschedule()` validates new slot, releases old, stores history, schedules new reminder
  - **Hospital-side notification**: Separate `hospital_portal` channel with professional message template
  - **1-hour reminder**: Python `threading.Thread` fires reminder to tourist + hospital before appointment (replace with Celery in production)

<<<<<<< HEAD

### Agent 5: Cost Estimator _(Upgraded)_

=======

### Agent 5: Cost Estimator _(Upgraded)_

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **AI**: Claude — only for friendly cost summary text
- **Inputs**: Triage result, matched provider, tourist info (with insurance plan + home currency)
- **Outputs**: Full cost breakdown, insurance coverage, payment link, alternatives
- **Upgrades added**:
  - **Insurance API integration**: `verify_insurance_coverage()` calls real insurer API; falls back to local plan data with `"source": "local_benchmark"` flag
  - **Pre-authorization check**: Pure Python threshold logic — auto-generates pre-auth reference and submits to insurer API when cost exceeds plan limit
  - **Payment link generation**: Razorpay API creates real INR payment link for out-of-pocket amount; mock fallback for development
  - **Cheaper alternatives**: Pure Python lookup returns up to 3 concrete options (government OPD, telemedicine, local clinic) — only for severity ≤ 6 and out-of-pocket > ₹1,000

### Agent 6: Document Generator

<<<<<<< HEAD

=======

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

- **AI**: Claude claude-opus-4-5 + CraftMyPDF
- **Inputs**: Complete patient journey — intake, triage, booking, cost estimate
- **Outputs**: Medical summary PDF + insurance claim letter PDF
- **Key features**:
  - HIPAA-aware formatting
  - Claim letter includes supporting documents checklist
  - Translated to tourist's detected language

---

## 🔌 API Endpoints

### Health Check

```
GET /health
Response: { "status": "ok" }
```

### Webhook Integration

<<<<<<< HEAD

=======

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

```
POST /webhooks/clerk
POST /webhooks/events
Content-Type: application/json
```

### Usage Example

<<<<<<< HEAD

=======

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

```bash
# Health check
curl http://localhost:8000/health
```

---

## 🔑 Environment Variables

### Backend (.env)

<<<<<<< HEAD
| Variable | Description | Required |
| --------------------------- | ----------------------------- | ----------- |
| `ANTHROPIC_API_KEY` | Claude API key | ✅ |
| `GOOGLE_API_KEY` | Google Generative AI (Gemini) | ✅ |
| `GOOGLE_PLACES_API_KEY` | Hospital search + price level | ✅ |
| `GOOGLE_DIRECTIONS_API_KEY` | Ambulance routing | ⚪ Optional |
| `MONGODB_URI` | MongoDB connection string | ✅ |
| `CLERK_SECRET_KEY` | Auth backend secret | ✅ |
| `CRAFT_MY_PDF_API_KEY` | PDF generation | ✅ |
| `INSURANCE_API_URL` | Insurer REST API endpoint | ⚪ Optional |
| `INSURANCE_API_KEY` | Insurer API auth key | ⚪ Optional |
| `RAZORPAY_KEY_ID` | Payment gateway key | ⚪ Optional |
| `RAZORPAY_KEY_SECRET` | Payment gateway secret | ⚪ Optional |
=======
| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | ✅ |
| `GOOGLE_API_KEY` | Google Generative AI (Gemini) | ✅ |
| `GOOGLE_PLACES_API_KEY` | Hospital search + price level | ✅ |
| `GOOGLE_DIRECTIONS_API_KEY` | Ambulance routing | ⚪ Optional |
| `MONGODB_URI` | MongoDB connection string | ✅ |
| `CLERK_SECRET_KEY` | Auth backend secret | ✅ |
| `CRAFT_MY_PDF_API_KEY` | PDF generation | ✅ |
| `INSURANCE_API_URL` | Insurer REST API endpoint | ⚪ Optional |
| `INSURANCE_API_KEY` | Insurer API auth key | ⚪ Optional |
| `RAZORPAY_KEY_ID` | Payment gateway key | ⚪ Optional |
| `RAZORPAY_KEY_SECRET` | Payment gateway secret | ⚪ Optional |

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

> ⚪ Optional keys enable real integrations. Without them, agents fall back to mock data gracefully — the pipeline never crashes.

### Frontend (.env.local)

<<<<<<< HEAD
| Variable | Description |
| ----------------------------------- | ------------------ |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend key |
| `CLERK_SECRET_KEY` | Clerk backend key |
| `NEXT_PUBLIC_API_URL` | Backend API URL |
=======
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk frontend key |
| `CLERK_SECRET_KEY` | Clerk backend key |
| `NEXT_PUBLIC_API_URL` | Backend API URL |

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

---

## 🧪 Running the Pipeline

### Interactive Mode

```bash
cd backend
python orchestrator.py
```

### Demo Mode (sample data, no typing)

<<<<<<< HEAD

```bash
python orchestrator.py --demo
```

### Test Individual Agents

=======

```bash
python orchestrator.py --demo
```

### Test Individual Agents

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

```bash
python agent2.py    # Triage with sample chest pain case
python agent4.py    # Booking — tests conflict, reschedule, cancel
python agent5.py    # Cost estimate with mock insurance + payment link
```

---

## 🔐 Security Considerations

1. **API Keys**: Never commit `.env` to git (included in `.gitignore`)
2. **Authentication**: Clerk handles user auth on the frontend
3. **Data Privacy**: Medical data encrypted in MongoDB
4. **CORS**: Requests allowed only from whitelisted origins
5. **Rate Limiting**: Recommended for all public API endpoints
6. **HIPAA**: PDF generation follows HIPAA formatting guidelines
7. **Slot locking**: In production, replace in-memory `SLOTS_DB` with DB-level transactions to prevent race conditions

---

## 📊 Database Schema (MongoDB)

<<<<<<< HEAD
| Collection | Contents |
| --------------- | ----------------------------------------------------- |
| `users` | Tourist profiles and preferences |
| `consultations` | Medical consultation records |
| `bookings` | Hospital appointment bookings with reschedule history |
| `documents` | Generated medical PDFs |
| `costs` | Cached cost estimates |
| `notifications` | Full notification log (SMS, email, hospital portal) |
=======
| Collection | Contents |
|---|---|
| `users` | Tourist profiles and preferences |
| `consultations` | Medical consultation records |
| `bookings` | Hospital appointment bookings with reschedule history |
| `documents` | Generated medical PDFs |
| `costs` | Cached cost estimates |
| `notifications` | Full notification log (SMS, email, hospital portal) |

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

---

## 🚀 Deployment

### Backend (FastAPI)

```bash
# Docker
docker build -t mediguide-backend .
docker run -p 8000:8000 --env-file .env mediguide-backend
```

Cloud options: Railway, Render, AWS ECS, GCP Cloud Run

### Frontend (Next.js)

```bash
# Vercel (recommended)
npm install -g vercel
vercel

# Or self-hosted
npm run build && npm start
```

---

## 🐛 Troubleshooting

<<<<<<< HEAD
| Problem | Solution |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'agent1'` | Run from `backend/` directory |
| `anthropic.APIConnectionError` | Check `ANTHROPIC_API_KEY` in `.env` |
| `ChatGoogleGenerativeAI` crash with `.messages.create()` | Use `.invoke()` for LangChain Gemini clients |
| Slot conflict on booking | Agent 4 returns `{"status": "conflict"}` — orchestrator should call Agent 3 for next available slot |
| Insurance coverage shows `"source": "local_benchmark"` | Set `INSURANCE_API_URL` + `INSURANCE_API_KEY` in `.env` for real verification |
| Payment link shows `"source": "mock_gateway"` | Set `RAZORPAY_KEY_ID` + `RAZORPAY_KEY_SECRET` for real payment links |
| `pymongo.errors.ServerSelectionTimeoutError` | Check MongoDB URI and network access |
=======
| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'agent1'` | Run from `backend/` directory |
| `anthropic.APIConnectionError` | Check `ANTHROPIC_API_KEY` in `.env` |
| `ChatGoogleGenerativeAI` crash with `.messages.create()` | Use `.invoke()` for LangChain Gemini clients |
| Slot conflict on booking | Agent 4 returns `{"status": "conflict"}` — orchestrator should call Agent 3 for next available slot |
| Insurance coverage shows `"source": "local_benchmark"` | Set `INSURANCE_API_URL` + `INSURANCE_API_KEY` in `.env` for real verification |
| Payment link shows `"source": "mock_gateway"` | Set `RAZORPAY_KEY_ID` + `RAZORPAY_KEY_SECRET` for real payment links |
| `pymongo.errors.ServerSelectionTimeoutError` | Check MongoDB URI and network access |

> > > > > > > 7985c1ce49d53d2f84a80c1216707adb9f7fbb92

---

## 📈 Future Enhancements

- [ ] SMS/WhatsApp integration via Twilio
- [ ] Video consultation (Telemedicine API)
- [ ] Prescription fulfillment integration
- [ ] Real-time chat via WebSocket
- [ ] Master orchestrator agent (decides which agents to skip based on severity)
- [ ] Session memory — returning tourist recognition
- [ ] Feedback loop — triage accuracy improvement from post-visit ratings
- [ ] Analytics dashboard for hospitals
- [ ] Celery + Redis for production-grade reminder scheduling
- [ ] LangGraph integration for parallel agent execution (Agent 5 + Agent 6 simultaneously)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a Pull Request

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 🙏 Acknowledgments

- **Anthropic** for Claude AI — primary reasoning engine
- **Google** for Places API, Directions API, and Gemini
- **Razorpay** for payment infrastructure
- **Clerk** for authentication
- **Vercel** for Next.js framework and deployment
- **CraftMyPDF** for document generation
