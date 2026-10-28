import os
import smtplib
from email.message import EmailMessage

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email using standard Python smtplib and EmailMessage.
    
    Reads server configuration and login credentials from environment variables.
    """
    # 1. Fetch environment variables
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # 2. Check if configuration is missing
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
            f"SMTP configuration is incomplete. Missing variables: {', '.join(missing)}."
        )

    # Convert port to integer
    try:
        port = int(smtp_port)
    except ValueError:
        raise ValueError(f"Invalid SMTP_PORT: '{smtp_port}'. Must be an integer.")

    # 3. Construct email using modern EmailMessage class
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = recipient
    msg.set_content(body)

    # 4. Connect to SMTP server and send
    try:
        # Use SMTP_SSL for port 465 (SMTPS), standard SMTP for others
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.ehlo()
            if smtp_use_tls:
                server.starttls()
                server.ehlo()
            
        # Authenticate if login credentials are provided
        # (Skip authentication if connecting to our local test server on port 1025)
        if smtp_username and (smtp_host not in ["127.0.0.1", "localhost"] or port != 1025):
            server.login(smtp_username, smtp_password)
            
        # Send using the modern send_message API
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        raise ConnectionError(f"SMTP connection or send failed: {str(e)}")
