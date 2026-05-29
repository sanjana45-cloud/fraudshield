import os
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from dotenv import load_dotenv

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

load_dotenv()

# Add the backend folder to PYTHONPATH to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detector import FraudShield

app = FastAPI(
    title="🛡️ Fraud Shield API",
    description="AI-powered security core detecting SMS Spam, URL Phishing, and Transaction Anomalies.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global master detector instance initialized ONCE at startup
shield_core = None

def send_whatsapp_alert(input_type: str, result_dict: dict):
    """Helper to send WhatsApp alerts via Twilio Sandbox."""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        to_whatsapp = os.getenv("USER_WHATSAPP_NUMBER", "")
        content_sid = os.getenv("TWILIO_CONTENT_SID", "")

        if not account_sid or not auth_token or not to_whatsapp:
            print("⚠️ WhatsApp alert skipped: Twilio credentials or destination number missing in .env")
            return
        if TwilioClient is None:
            print("⚠️ WhatsApp alert skipped: twilio library not installed")
            return

        client = TwilioClient(account_sid, auth_token)

        user_alert = result_dict.get("user_alert", "A high risk threat was detected.")
        safety_tip = result_dict.get("safety_tip", "Stay vigilant.")

        # Try content template first (works reliably on Sandbox)
        if content_sid:
            try:
                import json as _json
                message = client.messages.create(
                    from_=from_whatsapp,
                    content_sid=content_sid,
                    content_variables=_json.dumps({
                        "1": input_type.upper(),
                        "2": user_alert[:100]
                    }),
                    to=to_whatsapp
                )
                print(f"📲 WhatsApp template alert sent! SID: {message.sid}")
                return
            except Exception as template_err:
                print(f"⚠️ WhatsApp template send failed ({template_err}), trying freeform body...")

        # Fallback: freeform body message
        msg_body = (
            f"🚨 Fraud Shield Alert\n\n"
            f"Risk Level: HIGH\n"
            f"Type: {input_type.upper()}\n"
            f"Warning: {user_alert}\n\n"
            f"Tip: {safety_tip}\n\n"
            f"Stay safe. — Fraud Shield 🛡️"
        )

        message = client.messages.create(
            body=msg_body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        print(f"📲 WhatsApp freeform alert sent! SID: {message.sid}")
    except Exception as e:
        print(f"⚠️ WhatsApp alert failed: {e}")


@app.on_event("startup")
def startup_event():
    global shield_core
    print("\n------------------------------------------")
    print("🛡️ Fraud Shield API is live")
    print("------------------------------------------\n")
    shield_core = FraudShield()


# --- REQUEST & RESPONSE SCHEMAS ---

class SMSRequest(BaseModel):
    message: str

class URLRequest(BaseModel):
    url: str

class TransactionRequest(BaseModel):
    amount: float
    hour: int
    frequency_today: int
    location_change: int  # 0 or 1
    new_recipient: int    # 0 or 1
    device_change: int    # 0 or 1

class ConfigRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


# --- ENDPOINTS ---

@app.get("/health")
def health_check():
    """Verify that the FastAPI backend is operational."""
    return {"status": "ok", "message": "Fraud Shield is running and securing your device."}


@app.post("/analyze/sms")
def analyze_sms(body: SMSRequest, background_tasks: BackgroundTasks):
    """Scan an SMS or chat message for fraud and triggers alerts if high-risk."""
    if shield_core is None:
        raise HTTPException(status_code=503, detail="Fraud Shield Master Core is not fully loaded.")
    try:
        result = shield_core.analyze("sms", body.message)
        if result.get("final_risk") == "HIGH":
            background_tasks.add_task(send_whatsapp_alert, "SMS", result)
        return result
    except Exception as e:
        print(f"[API ERROR] SMS scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal scanning error: {str(e)}")


@app.post("/analyze/url")
def analyze_url(body: URLRequest, background_tasks: BackgroundTasks):
    """Scan a link/URL for phishing attempts and triggers alerts if high-risk."""
    if shield_core is None:
        raise HTTPException(status_code=503, detail="Fraud Shield Master Core is not fully loaded.")
    try:
        result = shield_core.analyze("url", body.url)
        if result.get("final_risk") == "HIGH":
            background_tasks.add_task(send_whatsapp_alert, "URL", result)
        return result
    except Exception as e:
        print(f"[API ERROR] URL scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal scanning error: {str(e)}")


@app.post("/analyze/transaction")
def analyze_transaction(body: TransactionRequest, background_tasks: BackgroundTasks):
    """Scan a banking/UPI transaction for anomalies and triggers alerts if high-risk."""
    if shield_core is None:
        raise HTTPException(status_code=503, detail="Fraud Shield Master Core is not fully loaded.")
    
    # Validation
    if body.hour < 0 or body.hour > 23:
        raise HTTPException(status_code=400, detail="Hour of day must be between 0 and 23.")
    if body.amount < 0:
        raise HTTPException(status_code=400, detail="Transaction amount cannot be negative.")
        
    try:
        data_dict = {
            "amount": body.amount,
            "hour": body.hour,
            "frequency_today": body.frequency_today,
            "location_change": body.location_change,
            "new_recipient": body.new_recipient,
            "device_change": body.device_change
        }
        result = shield_core.analyze("transaction", data_dict)
        if result.get("final_risk") == "HIGH":
            background_tasks.add_task(send_whatsapp_alert, "Transaction", result)
        return result
    except Exception as e:
        print(f"[API ERROR] Transaction scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal scanning error: {str(e)}")


@app.get("/alerts/records")
def get_alerts_records():
    """Retrieve the audit log of all flagged fraud events (latest first)."""
    if shield_core is None:
        raise HTTPException(status_code=503, detail="Fraud Shield Master Core is not fully loaded.")
    try:
        records = shield_core.notifier.get_records()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit log: {str(e)}")


@app.post("/alerts/config")
def update_alerts_config(body: ConfigRequest):
    """Dynamically update the target email and phone number for security alerts."""
    if shield_core is None:
        raise HTTPException(status_code=503, detail="Fraud Shield Master Core is not fully loaded.")
    try:
        shield_core.notifier.update_config(email=body.email, phone=body.phone)
        return {
            "status": "success",
            "message": "Security contact targets updated successfully.",
            "current_email": shield_core.notifier.target_email,
            "current_phone": shield_core.notifier.target_phone
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configurations: {str(e)}")


# Run with: uvicorn main:app --reload
