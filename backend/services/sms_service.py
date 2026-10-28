import os
from twilio.rest import Client

def send_sms_via_twilio(phone_number: str, message: str) -> bool:
    """
    Connects to Twilio API and sends the SMS.
    
    Loads configuration from environment variables.
    """
    # 1. Fetch environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

    # 2. Check if configuration is missing
    if not all([account_sid, auth_token, twilio_phone]):
        missing = [
            var for var, val in {
                "TWILIO_ACCOUNT_SID": account_sid,
                "TWILIO_AUTH_TOKEN": auth_token,
                "TWILIO_PHONE_NUMBER": twilio_phone
            }.items() if not val
        ]
        raise ValueError(
            f"Twilio configuration is incomplete. Missing variables: {', '.join(missing)}. "
            "Please check your .env configuration."
        )

    # 3. Connect to Twilio and send
    try:
        client = Client(account_sid, auth_token)
        sent_message = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )
        # Check if message sid is generated
        if sent_message.sid:
            return True
        else:
            raise ConnectionError("Twilio failed to return a message SID.")
    except Exception as e:
        raise ConnectionError(f"Twilio API error occurred: {str(e)}")
