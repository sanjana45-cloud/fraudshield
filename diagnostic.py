import os
import json
import urllib.request
from dotenv import load_dotenv

# Try importing Twilio
try:
    from twilio.rest import Client
except ImportError:
    Client = None

load_dotenv()

print("==========================================")
print("🔍 FRAUD SHIELD DIAGNOSTIC TESTER")
print("==========================================\n")

# 1. Test Gemini API Feature
print("--- 1. TESTING GEMINI EXPLAINABLE AI ---")
GEMINI_API_KEY = "AIzaSyDsuWHZru9U1mxEVVcw8By9-yPemnxML-Y"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

prompt = "Explain what a phishing URL is in 1 simple sentence in Hinglish."
data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
req = urllib.request.Request(GEMINI_URL, data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        print("✅ Gemini API SUCCESS!")
        print("Response:", res["candidates"][0]["content"]["parts"][0]["text"].strip())
except urllib.error.HTTPError as e:
    print("❌ Gemini API FAILED:", e.read().decode())
except Exception as e:
    print("❌ Gemini API FAILED:", e)

# 2. Test Twilio SMS, Voice, and WhatsApp
print("\n--- 2. TESTING TWILIO INTEGRATIONS ---")
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = "+15014060623"
to_number = "+918792783433"

print(f"Using Account SID: {account_sid}")
print(f"From Number: {from_number}")
print(f"To Number: {to_number}")

if not Client:
    print("❌ Twilio library not installed. Cannot proceed.")
else:
    try:
        client = Client(account_sid, auth_token)
        
        # Test SMS
        print("\nTesting SMS...")
        try:
            msg = client.messages.create(
                body="🚨 FRAUD SHIELD DIAGNOSTIC: SMS working!",
                from_=from_number,
                to=to_number
            )
            print("✅ SMS SUCCESS! SID:", msg.sid)
        except Exception as e:
            print("❌ SMS FAILED:", e)

        # Test Voice Call
        print("\nTesting Voice Call...")
        try:
            call = client.calls.create(
                twiml="<Response><Say>Fraud Shield Diagnostic test successful.</Say></Response>",
                to=to_number,
                from_=from_number
            )
            print("✅ Voice Call SUCCESS! SID:", call.sid)
        except Exception as e:
            print("❌ Voice Call FAILED:", e)

        # Test WhatsApp Message (via Sandbox)
        print("\nTesting WhatsApp Message (Sandbox)...")
        try:
            import json as _json
            msg = client.messages.create(
                from_="whatsapp:+14155238886",
                content_sid="HXb5b62575e6e4ff6129ad7c8efe1f983e",
                content_variables=_json.dumps({"1": "DIAGNOSTIC", "2": "Test alert"}),
                to=f"whatsapp:{to_number}"
            )
            print("✅ WhatsApp Sandbox SUCCESS! SID:", msg.sid)
        except Exception as e:
            print("❌ WhatsApp FAILED:", e)
            print("💡 TIP: Make sure you have joined the Twilio Sandbox by sending the join code from your WhatsApp to +14155238886.")

    except Exception as e:
        print("❌ Twilio Client Initialization FAILED:", e)

print("\n==========================================")
