# 📋 AI Meeting Follow-Up Agent

Turn meeting conversations into actionable follow-ups. Paste a transcript, and the app detects action items, assignees, deadlines and priorities with an ML pipeline, then drafts and sends a follow-up email.

**Live demo:** https://ai-meeting-follow-up-agent-gamma.vercel.app
**Backend API:** https://meeting-agent-backend-31zj.onrender.com

> The backend runs on Render's free tier, so the first request after a period of inactivity can take 30-60 seconds while the server wakes up.

---

## ✨ Features

- **Action item detection:** classifies a transcript as `ACTION` or `NON-ACTION`
- **Smart extraction:** pulls out assignee, task, deadline and priority for each action item
- **Auto-generated follow-up email:** editable subject and message before sending
- **Real email delivery** through an HTTPS email API (Brevo or Resend)
- **Simulation Mode:** test the full flow without sending a real email
- **Copy Email / Schedule Reminder** actions
- **Live status bar:** ML status, API status, scheduled and sent counters

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite |
| Backend | Python 3.11, FastAPI |
| ML / NLP | scikit-learn (TF-IDF + Logistic Regression), rule-based NLP fallbacks |
| Email | Brevo API / Resend API over HTTPS (SMTP as fallback) |
| Hosting | Vercel (frontend), Render (backend) |

---

## 🗂️ Project Structure

```
.
├── backend/
│   ├── app.py                  # FastAPI app and endpoints
│   ├── services/
│   │   └── email_service.py    # Email sending (Brevo / Resend / SMTP)
│   ├── requirements.txt
│   └── ...                     # ML models and pipeline
├── frontend/
│   ├── src/
│   │   └── ...                 # React components (EmailPanel.jsx, etc.)
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/predict` | Analyzes a transcript and returns the classification and action items |
| `POST` | `/send-email` | Sends the follow-up email (or simulates it) |

**`POST /send-email` body**

```json
{
  "recipient": "someone@example.com",
  "subject": "Meeting Follow-Up — Action Items",
  "body": "Hi team, ...",
  "simulation_mode": false
}
```

---

## 🚀 Run Locally

### 1. Clone

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Point the frontend at your backend by setting its API URL (for example `VITE_API_URL=http://localhost:8000` in `frontend/.env`). Use whichever variable name your code reads.

---

## 🔐 Environment Variables (Backend)

Set these in a `.env` file locally, or in the Render dashboard under **Environment**. Never commit real keys.

| Variable | Description |
|---|---|
| `BREVO_API_KEY` | Brevo API key (starts with `xkeysib-`) |
| `BREVO_SENDER` | Verified sender email in Brevo |
| `RESEND_API_KEY` | Resend API key (starts with `re_`), used if Brevo is not set |
| `RESEND_FROM` | Sender address for Resend, e.g. `Meeting Agent <noreply@yourdomain.com>` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` | SMTP fallback (works locally, blocked on Render's free tier) |

Provider priority: **Brevo, then Resend, then SMTP**.

---

## 📧 Email Setup Notes

Render's free tier blocks outbound SMTP ports (25, 465, 587), so email is sent over HTTPS (port 443) using an email API.

- **Brevo:** verify a sender, create an API key with **Transactional email = All**, and set `BREVO_API_KEY` and `BREVO_SENDER`. The free plan allows 300 emails/day.
- **Resend:** the sandbox sender `onboarding@resend.dev` only delivers to the email you signed up with. To email anyone, verify your own domain and set `RESEND_FROM`.
- Python's default `urllib` User-Agent gets blocked by Cloudflare (error `1010`), so the code sends a custom `User-Agent` header.
- Emails sent from a Gmail address may land in spam. Ask recipients to check their spam folder.

---

## ☁️ Deployment

**Backend (Render)**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Add the environment variables above

**Frontend (Vercel)**
- Framework preset: Vite
- Set the backend API URL environment variable to your Render URL

---

## 🛠️ Troubleshooting

| Problem | Cause and fix |
|---|---|
| `Network is unreachable` on send | SMTP is blocked on Render. Use the Brevo or Resend API. |
| `403 error code: 1010` | Cloudflare blocked the default Python User-Agent. Add a custom `User-Agent` header. |
| `403 validation_error` (Resend) | Sandbox sender limit. Verify a domain or use Brevo. |
| `401` | Invalid API key. Regenerate it and update Render. |
| First request is very slow | Render free tier is waking up. Wait and retry. |

---

## 👥 Team

Built by **Team ProcastiNOTers**.

---

## 📄 License

Add your license here (for example MIT).
