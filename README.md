# AI Meeting Follow-Up Agent

The **AI Meeting Follow-Up Agent** is a full-stack, end-to-end machine learning application that analyzes meeting transcripts or emails to automatically extract action items, assignees, deadlines, priorities, and decisions. When action items are identified, the system generates follow-up Email and SMS notifications, allowing users to review, edit, and send them directly through real integration services.

Turn messy, multi-sentence meeting transcripts and long email chains into structured, actionable items in seconds.

---

## 🏗️ Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                   React Frontend (Vite)                │
       └───────────┬────────────────────────────────▲───────────┘
                   │                                │
                   │  POST /predict (JSON Text)     │  JSON Predictions
                   │                                │  & Follow-up Templates
                   ▼                                │
       ┌────────────────────────────────────────────┴───────────┐
       │                   FastAPI Backend                      │
       └─────┬────────────────────────────────────────────────▲─┘
             │                                                │
             │  Send Requests                                 │
             ▼                                                │
       ┌───────────┐                                          │
       │ Send API  ├──────────────────┐                       │
       └─────┬─────┘                  │                       │
             │                        │                       │
             ▼ (SMTP)                 ▼ (Twilio API)          │
       ┌───────────┐            ┌───────────┐                 │
       │ SMTP Mail │            │ Twilio SMS│                 │
       │ Server    │            │ Gateway   │                 │
       └─────┬─────┘            └─────┬─────┘                 │
             │                        │                       │
             ▼ (Recipients)           ▼ (Recipients)          │
                                                              │
             ┌───────────────────────────────────────────┐    │
             │             ML Inference Pipeline         ├────┘
             │  - Line-by-line Sentence Segmentation     │
             │  - Preprocessing & Preserving Temporals   │
             │  - TF-IDF Vectorizer Transform            │
             │  - Logistic Regression (Primary)          │
             │  - Keyword Lookup Fallbacks (OOD Inputs)  │
             └───────────────────────────────────────────┘
```

---

## 📂 Folder Structure

```text
Follow Up Agent/
│
├── dataset/
│   └── AI_Meeting_Follow_Up_Preprocessed_Clean.xlsx  # Training data
│
├── backend/
│   ├── app.py                     # FastAPI server, schemas & route handlers
│   ├── requirements.txt           # Python library dependencies
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── preprocess.py          # Lowercasing, whitespace & temporal normalization
│   │   ├── train.py               # Model training script
│   │   ├── predict.py             # Inference pipeline with hybrid fallback extraction
│   │   └── evaluate.py            # Macro precision, recall, F1 computation
│   │
│   ├── models/                    # Serialized joblib artifacts
│   │   ├── tfidf_vectorizer.pkl
│   │   ├── label_model.pkl
│   │   └── ...
│   │
│   └── services/
│       ├── __init__.py
│       ├── followup_generator.py  # Email and SMS template compilers
│       ├── email_service.py       # SMTP wrapper
│       └── sms_service.py         # Twilio REST API wrapper
│
├── frontend/
│   ├── package.json               # Node modules list
│   ├── vite.config.js             # Vite development configurations
│   ├── index.html                 # Entry point page
│   └── src/
│       ├── components/            # Reusable UI modules
│       │   ├── Header.jsx
│       │   ├── InputSection.jsx
│       │   ├── AnalysisResults.jsx (Displays multiple action cards)
│       │   ├── FollowUp.jsx        (Send email and SMS forms)
│       │   ├── PriorityBadge.jsx
│       │   └── LoadingState.jsx
│       ├── services/
│       │   └── api.js             # Fetch API wrapper
│       ├── App.jsx                # Main controller React file
│       ├── main.jsx               # Render mounting root
│       └── styles/
│           └── App.css            # Custom responsive HSL dashboard stylesheet
│
├── .env.example                   # Environmental placeholders
├── README.md
└── .gitignore
```

---

## 📊 Dataset & Model Details

The model is trained on the dataset: `dataset/AI_Meeting_Follow_Up_Preprocessed_Clean.xlsx`.

### Targets Trained:
* **`label`**: Classifies text as `ACTION` or `NON_ACTION` (100% Accuracy).
* **`action_item`**: Extracts specific task names (e.g. `Login module`, `Database schema`) (100% Accuracy).
* **`assignee`**: Extracts the person assigned to the task (e.g. `Nikhil`, `Sneha`) (100% Accuracy).
* **`deadline`**: Extracts timeframe phrases (e.g. `by the next sprint`, `tomorrow`) (100% Accuracy).
* **`decision`**: Identifies meeting decisions (e.g. `discussion only`, `not applicable`) (100% Accuracy).
* **`priority`**: Evaluates task priority (`high`, `medium`, `low`). Due to uniform distribution across other variables in the dataset (i.e. priority is random relative to text keywords), the model gets `~55% Accuracy`. The API supports this by outputting the model prediction but noting limitations.

---

## 🚀 Setup & Installation

### Prerequisite
Ensure you have `Python 3.8+` and `Node.js 16+` installed.

### 1. Environmental Variables Configuration
Create a `.env` file in the project root folder. Copy the contents of `.env.example` and fill in your actual SMTP mail server and Twilio gateway credentials:

```bash
cp .env.example .env
```

Edit the `.env` file:
```env
# SMTP Mail Server
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Twilio SMS Gateway
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### 2. Backend Setup & Model Training
Open a terminal in the project root:

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run model training and validation
python ml/train.py
```

### 3. Start the Backend API
From the `backend/` directory (with virtual environment active):

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`. You can visit documentation at `http://localhost:8000/docs`.

### 4. Frontend Setup & Run
Open another terminal in the project root:

```bash
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Run Vite dev server
npm run dev
```

The React dashboard will launch at `http://localhost:5173`.

---

## 🔌 API Endpoints

### 1. POST `/predict`
Segments the input text line-by-line, runs the prediction models on each line, groups related sentences (merging follow-up deadlines into their respective active tasks), and returns a list of action item details along with consolidated templates.

#### Request body:
```json
{
  "text": "Priya: Rahul, please fix the mobile login issues and test the login flow by Thursday.\nPriya: Ananya, please update the API error handling and add proper validation for invalid requests. Please complete it by Wednesday."
}
```

#### Response body:
```json
{
  "label": "ACTION",
  "follow_up_required": true,
  "action_items": [
    {
      "action_item": "Login module",
      "assignee": "Rahul",
      "deadline": "by Thursday",
      "priority": "medium",
      "decision": "action item assigned",
      "speaker": "Priya",
      "original_sentence": "Rahul, please fix the mobile login issues and test the login flow by Thursday."
    },
    {
      "action_item": "API integration",
      "assignee": "Ananya",
      "deadline": "by Wednesday",
      "priority": "low",
      "decision": "action item assigned",
      "speaker": "Priya",
      "original_sentence": "Ananya, please update the API error handling and add proper validation for invalid requests. Please complete it by Wednesday."
    }
  ],
  "follow_up": {
    "email": {
      "subject": "Meeting Follow-Up — Action Items",
      "body": "Hi team,\n\nHere are the action items discussed in the meeting:\n\n1. Rahul\n   Task: Login module\n   Deadline: by Thursday\n   Priority: Medium\n\n2. Ananya\n   Task: API integration\n   Deadline: by Wednesday\n   Priority: Low\n\nPlease complete the assigned tasks within the specified deadlines.\n\nRegards,\nAI Meeting Follow-Up Agent"
    },
    "sms": "Meeting Follow-Up: 1. Rahul (Login module: by Thursday) 2. Ananya (API integration: by Wednesday)"
  }
}
```

### 2. POST `/send-email`
Sends the email using the configured SMTP settings.

#### Request body:
```json
{
  "recipient": "user@example.com",
  "subject": "Meeting Follow-Up — Action Items",
  "body": "..."
}
```

#### Response:
```json
{
  "success": true,
  "message": "Email sent successfully to user@example.com"
}
```

### 3. POST `/send-sms`
Sends the SMS using the configured Twilio settings.

#### Request body:
```json
{
  "phone_number": "+1234567890",
  "message": "..."
}
```

#### Response:
```json
{
  "success": true,
  "message": "SMS sent successfully to +1234567890"
}
```

---

## ⚠️ Limitations & Troubleshooting

* **Out-of-Distribution Inputs**: Due to the template-based generation of the training dataset, Logistic Regression models can predict `Not Applicable` when names or tasks appear in combinations not seen during training. The prediction module uses a Named Entity lookup fallback to resolve this and extract the correct fields.
* **SMTP / Twilio Configuration**: If you click "Send" without configuring credentials in the `.env` file, the UI will report: `Email sending is not configured. Please configure the SMTP environment variables.` or `SMS sending is not configured. Please configure the Twilio environment variables.` (corresponding to `503 Service Unavailable` returned by the backend).
