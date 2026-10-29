import os
import smtplib
import json
import urllib.request
import urllib.error
from email.message import EmailMessage

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email using Resend HTTP API (if RESEND_API_KEY is present)
    or standard Python smtplib / EmailMessage as fallback.
    """
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
        brevo_key = os.getenv("BREVO_API_KEY", "").strip()
    if brevo_key:
        brevo_sender = os.getenv("BREVO_SENDER", "").strip()
        if not brevo_sender:
            raise ValueError("BREVO_SENDER is not set.")
        payload = {
            "sender": {"name": "Meeting Agent", "email": brevo_sender},
            "to": [{"email": recipient}],
            "subject": subject,
            "textContent": body,
        }
        headers = {
            "api-key": brevo_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "meeting-followup-agent/1.0",
        }
        try:
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201):
                    return True
                raise ConnectionError(f"Brevo returned status {resp.status}")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            raise ConnectionError(f"Brevo API error ({he.code}): {err_body}")
    
    # ---------------- 1. RESEND HTTP API (Modern Cloud Delivery over HTTPS) ----------------
    if resend_api_key:
        url = "https://api.resend.com/emails"
        from_email = "onboarding@resend.dev"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "meeting-followup-agent/1.0"
}
        payload = {
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "text": body
        }
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers, 
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in [200, 201]:
                    return True
                raise ConnectionError(f"Resend API returned status {resp.status}")
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8', errors='ignore')
            raise ConnectionError(f"Resend API error ({he.code}): {err_body}")
        except Exception as e:
            raise ConnectionError(f"Resend delivery failed: {str(e)}")

    # ---------------- 2. STANDARD SMTP FALLBACK (Local / Direct) ----------------
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = os.getenv("SMTP_PORT", "").strip()
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip().strip('"').strip("'")
    email_from = os.getenv("EMAIL_FROM", "").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not all([smtp_host, smtp_port, smtp_username, smtp_password, email_from]):
        missing = [
            var for var, val in {
                "SMTP_HOST": smtp_host,
                "SMTP_PORT": smtp_port,
                "SMTP_USERNAME": smtp_username,
                "SMTP_PASSWORD": smtp_password,
                "EMAIL_FROM": email_from
            }.items() if not val
        ]
        raise ValueError(
            f"Email configuration is incomplete. Missing variables: {', '.join(missing)} (or configure RESEND_API_KEY)."
        )

    try:
        port = int(smtp_port)
    except ValueError:
        raise ValueError(f"Invalid SMTP_PORT: '{smtp_port}'. Must be an integer.")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = recipient
    msg.set_content(body)

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.ehlo()
            if smtp_use_tls:
                server.starttls()
                server.ehlo()
            
        if smtp_username and (smtp_host not in ["127.0.0.1", "localhost"] or port != 1025):
            server.login(smtp_username, smtp_password)
            
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        raise ConnectionError(f"SMTP connection or send failed: {str(e)}")
