import os
import sys
import re
import time
import threading
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Ensure the backend directory is in the system path to allow clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables from .env file (if present)
load_dotenv()

from ml.predict import predict_text
from services.followup_generator import generate_multi_followup_email, generate_multi_followup_sms
from services.email_service import send_email
from services.sms_service import send_sms_via_twilio

app = FastAPI(
    title="AI Meeting Follow-Up Agent API",
    description="Updated API supporting sentence segmentation, multiple action items, and live/simulated email/SMS sending.",
    version="2.3.0"
)

# CORS Configuration - Allows Vite development server on port 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- PYDANTIC SCHEMAS -----------------

class PredictionRequest(BaseModel):
    text: str = Field(..., description="The full meeting transcript or email content.")

class ActionItemDetail(BaseModel):
    action_item: str
    assignee: str
    deadline: str
    priority: str
    decision: str
    speaker: Optional[str] = None
    original_sentence: str

class EmailTemplate(BaseModel):
    subject: str
    body: str

class FollowUpDetails(BaseModel):
    email: EmailTemplate
    sms: str

class PredictionResponse(BaseModel):
    label: str
    follow_up_required: bool
    action_items: List[ActionItemDetail]
    follow_up: Optional[FollowUpDetails] = None

class EmailSendRequest(BaseModel):
    recipient: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject line.")
    body: str = Field(..., description="Email body content.")
    simulation_mode: bool = Field(False, description="Enable simulation mode to log emails to a file locally. Default is False.")

class SmsSendRequest(BaseModel):
    phone_number: str = Field(..., description="Recipient phone number (E.164 format, e.g. +1234567890).")
    message: str = Field(..., description="SMS text content.")
    simulation_mode: bool = Field(False, description="Enable simulation mode to log SMS messages to a file locally. Default is False.")

class SendResponse(BaseModel):
    success: bool
    message: str

class ScheduleEmailRequest(BaseModel):
    recipient: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject line.")
    body: str = Field(..., description="Email body content.")
    send_at: str = Field(..., description="ISO 8601 timestamp to send the email at.")
    timezone: str = Field("Asia/Kolkata", description="Timezone of the request.")

# ----------------- SQLITE & APSCHEDULER PERSISTENT SCHEDULER -----------------
import sqlite3
import uuid
from zoneinfo import ZoneInfo
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")
tz_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
app_tz = ZoneInfo(tz_name)

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=app_tz)
scheduler.start()

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id TEXT PRIMARY KEY,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            send_at TEXT NOT NULL,
            timezone TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_active_scheduled_count():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scheduled_jobs WHERE sent = 0")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_sent_today_count():
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    tz = ZoneInfo(tz_name)
    today_str = datetime.now(tz).strftime('%Y-%m-%d')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scheduled_jobs WHERE sent = 1 AND substr(send_at, 1, 10) = ?", (today_str,))
    count = c.fetchone()[0]
    conn.close()
    return count

def send_scheduled_email_job(job_id, recipient, subject, body):
    try:
        from services.email_service import send_email
        smtp_host = os.getenv("SMTP_HOST")
        if smtp_host and smtp_host != "your-email@gmail.com":
            try:
                send_email(recipient, subject, body)
                print(f"[JOB {job_id}] Sent email to {recipient}")
            except Exception as smtp_err:
                print(f"[JOB {job_id} SMTP FAIL] Falling back to simulation: {str(smtp_err)}")
                raise smtp_err
        else:
            raise ValueError("SMTP not configured")
    except Exception as ex:
        # Write simulation log
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_emails.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"=== [SCHEDULED EMAIL SIMULATION] TO: {recipient} ===\n")
            f.write(f"Subject: {subject}\n\n")
            f.write(body)
            f.write("\n" + "="*50 + "\n\n")
        print(f"[JOB {job_id}] Simulated email to {recipient} (saved to log)")
    
    # Update SQLite database to mark job as sent (sent = 1)
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE scheduled_jobs SET sent = 1 WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
    except Exception as db_err:
        print(f"[JOB {job_id} DB ERROR] Failed to update sent status: {str(db_err)}")

def load_jobs_from_db():
    init_db()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, recipient, subject, body, send_at, timezone, sent FROM scheduled_jobs WHERE sent = 0")
    rows = c.fetchall()
    
    now = datetime.now(app_tz)
    
    for row in rows:
        job_id, recipient, subject, body, send_at_str, job_tz_name, sent = row
        try:
            send_at = datetime.fromisoformat(send_at_str)
            if send_at.tzinfo is None:
                job_tz = ZoneInfo(job_tz_name)
                send_at = send_at.replace(tzinfo=job_tz)
            
            # Compare with now
            if send_at > now:
                # Schedule in APScheduler
                scheduler.add_job(
                    send_scheduled_email_job,
                    'date',
                    run_date=send_at,
                    args=[job_id, recipient, subject, body],
                    id=job_id,
                    misfire_grace_time=60,
                    replace_existing=True
                )
                print(f"[RELOAD] Scheduled future job {job_id} for {send_at}")
            else:
                # Mark as missed (sent = 2). Do not execute!
                c.execute("UPDATE scheduled_jobs SET sent = 2 WHERE id = ?", (job_id,))
                print(f"[RELOAD] Marked past job {job_id} as missed (scheduled time was {send_at_str})")
        except Exception as e:
            print(f"[RELOAD ERROR] Failed to load job {job_id}: {str(e)}")
            
    conn.commit()
    conn.close()

# Initialize DB and load jobs
load_jobs_from_db()

# ----------------- API ENDPOINTS -----------------

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "AI Meeting Follow-Up Agent API is running.",
        "configuration": {
            "smtp_configured": bool(os.getenv("SMTP_HOST")),
            "twilio_configured": bool(os.getenv("TWILIO_ACCOUNT_SID"))
        }
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    text_content = request.text.strip()
    if not text_content:
        raise HTTPException(
            status_code=400, 
            detail="Input text cannot be empty. Please provide a meeting transcript or email content."
        )
        
    try:
        # Split by lines (each line is a speaker's turn / utterance)
        lines = text_content.split('\n')
        action_items = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse speaker
            speaker = None
            content = line
            match = re.match(r'^([^:\n]+):\s*(.*)$', line)
            if match:
                potential_speaker = match.group(1).strip()
                if len(potential_speaker) < 50 and not re.search(r'[^a-zA-Z0-9\s]', potential_speaker):
                    speaker = potential_speaker
                    content = match.group(2).strip()
                    
            # Split line into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            # Active action item for this specific line/speaker turn
            line_action = None
            
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                    
                preds = predict_text(s)
                
                if preds.get("label") == "ACTION":
                    assignee = preds.get("assignee")
                    action_item = preds.get("action_item")
                    deadline = preds.get("deadline")
                    priority = preds.get("priority")
                    decision = preds.get("decision")
                    
                    # Case 1: Sentence contains actual task/assignee info
                    if assignee != "Not Applicable" or action_item != "Not Applicable":
                        # Save current active line action if we are starting a new one
                        if line_action:
                            action_items.append(line_action)
                            
                        line_action = ActionItemDetail(
                            action_item=action_item,
                            assignee=assignee,
                            deadline=deadline,
                            priority=priority,
                            decision=decision,
                            speaker=speaker,
                            original_sentence=s
                        )
                    # Case 2: Sentence has no task/assignee, but has a deadline, and we have an active task to merge into
                    elif line_action and deadline != "Not Applicable":
                        line_action.deadline = deadline
                        line_action.original_sentence += " " + s
                    # Case 3: Standalone sentence (no active task), only add if it has deadline or priority
                    else:
                        if deadline != "Not Applicable" or priority != "not applicable":
                            line_action = ActionItemDetail(
                                action_item=action_item,
                                assignee=assignee,
                                deadline=deadline,
                                priority=priority,
                                decision=decision,
                                speaker=speaker,
                                original_sentence=s
                            )
            
            # Save final action item for this speaker turn
            if line_action:
                action_items.append(line_action)
        
        # 3. Aggregate results
        follow_up_required = len(action_items) > 0
        overall_label = "ACTION" if follow_up_required else "NON_ACTION"
        
        follow_up_data = None
        if follow_up_required:
            items_dict = [item.model_dump() for item in action_items]
            
            email_data = generate_multi_followup_email(items_dict)
            sms_text = generate_multi_followup_sms(items_dict)
            
            follow_up_data = FollowUpDetails(
                email=EmailTemplate(
                    subject=email_data["subject"],
                    body=email_data["body"]
                ),
                sms=sms_text
            )
            
        return PredictionResponse(
            label=overall_label,
            follow_up_required=follow_up_required,
            action_items=action_items,
            follow_up=follow_up_data
        )
        
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=503, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/send-email", response_model=SendResponse)
def send_email_endpoint(request: EmailSendRequest):
    # 1. Validate email address format
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, request.recipient):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
        
    if not request.subject.strip():
        raise HTTPException(status_code=400, detail="Subject line cannot be empty.")
    if not request.body.strip():
        raise HTTPException(status_code=400, detail="Email body cannot be empty.")
        
    # Get app timezone
    from zoneinfo import ZoneInfo
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    tz = ZoneInfo(tz_name)
    now_str = datetime.now(tz).isoformat()
    job_id = str(uuid.uuid4())

    # 2. Handle Simulation Mode (Optional Dev workflow, NOT default)
    if request.simulation_mode:
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_emails.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"=== [SIMULATION EMAIL] TO: {request.recipient} ===\n")
                f.write(f"Subject: {request.subject}\n\n")
                f.write(request.body)
                f.write("\n" + "="*50 + "\n\n")
            print(f"[SIMULATION EMAIL] Written to received_emails.log for recipient {request.recipient}")
            
            # Log immediately as sent in SQLite
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("INSERT INTO scheduled_jobs (id, recipient, subject, body, send_at, timezone, sent) VALUES (?, ?, ?, ?, ?, ?, 1)",
                      (job_id, request.recipient, request.subject, request.body, now_str, tz_name))
            conn.commit()
            conn.close()
            
            return SendResponse(success=True, message=f"[SIMULATION] Email saved to received_emails.log")
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"Simulation writing failed: {str(ex)}")

    # 3. Call SMTP sending service (Default Production Mode)
    try:
        send_email(request.recipient, request.subject, request.body)
        
        # Log immediately as sent in SQLite
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO scheduled_jobs (id, recipient, subject, body, send_at, timezone, sent) VALUES (?, ?, ?, ?, ?, ?, 1)",
                  (job_id, request.recipient, request.subject, request.body, now_str, tz_name))
        conn.commit()
        conn.close()
        
        return SendResponse(success=True, message="Email sent successfully.")
    except ValueError as ve:
        raise HTTPException(
            status_code=503, 
            detail="Email sending is not configured. Please configure SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD and EMAIL_FROM."
        )
    except (ConnectionError, Exception) as e:
        print(f"[SMTP FAIL] Diagnostic error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Email could not be sent. Please check your SMTP configuration and try again."
        )

@app.post("/schedule-email", response_model=SendResponse)
def schedule_email_endpoint(request: ScheduleEmailRequest):
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, request.recipient):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if not request.subject.strip():
        raise HTTPException(status_code=400, detail="Subject line cannot be empty.")
    if not request.body.strip():
        raise HTTPException(status_code=400, detail="Email body cannot be empty.")
        
    try:
        # Determine the user's target timezone (or default to APP_TIMEZONE)
        tz_name = request.timezone if request.timezone else os.getenv("APP_TIMEZONE", "Asia/Kolkata")
        tz = ZoneInfo(tz_name)
        
        # Parse ISO send_at string
        dt_str = request.send_at.replace("Z", "+00:00")
        send_at_dt = datetime.fromisoformat(dt_str)
        
        # Localize or convert target datetime to ensure it is timezone-aware in the correct zone
        if send_at_dt.tzinfo is None:
            send_at_dt = send_at_dt.replace(tzinfo=tz)
        else:
            send_at_dt = send_at_dt.astimezone(tz)
            
        # Get current time in same timezone for accurate comparison
        now = datetime.now(tz)
        
        # Check if the requested time is already in the past (with a 10s grace/tolerance)
        # "If the reminder is exactly at the current time or within a very small past tolerance, treat it as invalid"
        if send_at_dt <= now + timedelta(seconds=10):
            raise HTTPException(
                status_code=400,
                detail="Selected reminder time has already passed. Please choose a future time."
            )
            
        # Create UUID job ID
        job_id = str(uuid.uuid4())
        
        # Insert into SQLite database
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO scheduled_jobs (id, recipient, subject, body, send_at, timezone, sent) VALUES (?, ?, ?, ?, ?, ?, 0)",
                  (job_id, request.recipient, request.subject, request.body, send_at_dt.isoformat(), tz_name))
        conn.commit()
        conn.close()
        
        # Schedule the job in APScheduler
        scheduler.add_job(
            send_scheduled_email_job,
            'date',
            run_date=send_at_dt,
            args=[job_id, request.recipient, request.subject, request.body],
            id=job_id,
            misfire_grace_time=60,
            replace_existing=True
        )
        
        print(f"[API] Successfully scheduled job {job_id} for {send_at_dt.isoformat()}")
        
        return SendResponse(
            success=True,
            message=f"Email scheduled successfully for {send_at_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schedule time format: {str(e)}")

@app.get("/stats")
def get_stats():
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    active_scheduled = get_active_scheduled_count()
    sent_today = get_sent_today_count()
    return {
        "scheduled_count": active_scheduled,
        "sent_today_count": sent_today,
        "app_timezone": tz_name
    }

@app.post("/send-sms", response_model=SendResponse)
def send_sms_endpoint(request: SmsSendRequest):
    # 1. Validate phone number format
    phone_regex = r"^\+?[1-9]\d{4,14}$"
    clean_phone = request.phone_number.replace(" ", "").replace("-", "")
    if not re.match(phone_regex, clean_phone):
        raise HTTPException(
            status_code=400, 
            detail="Please enter a valid phone number in E.164 format (e.g. +1234567890)."
        )
        
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="SMS message content cannot be empty.")
        
    # 2. Handle Simulation Mode (Optional Dev workflow, NOT default)
    if request.simulation_mode:
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_sms.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"=== [SIMULATION SMS] TO: {clean_phone} ===\n")
                f.write(request.message)
                f.write("\n" + "="*50 + "\n\n")
            print(f"[SIMULATION SMS] Written to received_sms.log for recipient {clean_phone}")
            return SendResponse(success=True, message=f"[SIMULATION] SMS saved to received_sms.log")
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"Simulation writing failed: {str(ex)}")

    # 3. Call Twilio sending service (Default Production Mode)
    try:
        send_sms_via_twilio(clean_phone, request.message)
        return SendResponse(success=True, message="SMS sent successfully.")
    except ValueError as ve:
        raise HTTPException(
            status_code=503, 
            detail="SMS sending is not configured. Please configure the Twilio environment variables."
        )
    except (ConnectionError, Exception) as e:
        print(f"[TWILIO FAIL] Diagnostic error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="SMS could not be sent. Please check your Twilio configuration and try again."
        )
