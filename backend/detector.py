import os
import sys

# Add current folder to path to handle relative imports during testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sms_detector import SMSDetector
from url_detector import URLDetector
from transaction_detector import TransactionDetector
from notifier import Notifier


class FraudShield:
    def __init__(self):
        print("[Fraud Shield] Initializing master security core...")
        self.sms_detector = SMSDetector()
        self.url_detector = URLDetector()
        self.transaction_detector = TransactionDetector()
        self.notifier = Notifier()
        print("[Fraud Shield] Master core fully online! [SHIELD]")

    def analyze(self, input_type: str, data: any) -> dict:
        """
        Coordinates and routes input to the correct ML detector.
        Inputs:
            input_type (str): "sms", "url", or "transaction"
            data (any): string for sms/url, dict for transaction
        Returns:
            dict: Unified response layout
        """
        input_type = input_type.strip().lower()

        if input_type == "sms":
            result = self.sms_detector.detect(str(data))
            final_risk = result["risk_level"]
            
            if final_risk == "HIGH":
                user_alert = "⚠️ This message looks like a scam! It is trying to trick you into clicking a link, sharing an OTP, or claiming fake lottery money. Please do NOT reply and delete it."
                safety_tip = "💡 Digital Rule: Never share your login SMS OTP with anyone, not even bank officers. Real banks will never ask for it."
            elif final_risk == "MEDIUM":
                user_alert = "⚠️ This message looks a bit suspicious. It mentions cash or accounts. Please read it carefully before responding."
                safety_tip = "💡 Digital Rule: If a message asks you to 'click a link to get a prize', it is almost always a lie."
            else:
                user_alert = "✅ This message appears to be safe and friendly. No typical fraud patterns were found."
                safety_tip = "💡 Digital Rule: Always double-check if the sender name looks correct."

        elif input_type == "url":
            result = self.url_detector.detect(str(data))
            final_risk = result["risk_level"]

            if final_risk == "HIGH":
                user_alert = "⚠️ DANGER! This website link is a fake trap! It is designed to look like a real login page to steal your bank password or mobile secrets. Do NOT open it!"
                safety_tip = "💡 Digital Rule: Safe websites usually begin with 'https://' and have a small padlock icon next to the address in your browser."
            elif final_risk == "MEDIUM":
                user_alert = "⚠️ Careful! This link contains multiple security warnings (like using a cheap extension or weird spelling). It could be a trap."
                safety_tip = "💡 Digital Rule: Never enter your ATM PIN or netbanking password on websites you clicked from a chat message."
            else:
                user_alert = "✅ This website link looks safe. It matches standard trusted destinations."
                safety_tip = "💡 Digital Rule: Bookmark your important banking sites so you never click fake versions by mistake."

        elif input_type == "transaction":
            if not isinstance(data, dict):
                raise ValueError("Transaction data must be a dictionary.")
            
            result = self.transaction_detector.detect(data)
            final_risk = result["risk_level"]

            if final_risk == "HIGH":
                user_alert = "⚠️ WARNING! We detected a highly suspicious payment! It was made at an unusual late-night hour, for a very large amount, or from a completely new phone/device. Please check immediately if this was actually you."
                safety_tip = "💡 Digital Rule: If your phone receives a call asking you to 'approve a transaction' you did not make, hang up and lock your card immediately!"
            elif final_risk == "MEDIUM":
                user_alert = "⚠️ Attention: This payment has some abnormal signs (like being sent to a new unknown recipient or from a different location). Please review it."
                safety_tip = "💡 Digital Rule: Always send a tiny ₹1 test payment to a new recipient to confirm their identity before sending large amounts."
            else:
                user_alert = "✅ This transaction looks normal and safe. It matches your typical spending patterns."
                safety_tip = "💡 Digital Rule: Keep checking your monthly statements to stay on top of your bank accounts."

        else:
            raise ValueError(f"Unknown input_type: {input_type}. Must be 'sms', 'url', or 'transaction'.")

        # Prepare unified response
        unified_response = {
            "input_type": input_type,
            "result": result,
            "final_risk": final_risk,
            "user_alert": user_alert,
            "safety_tip": safety_tip
        }

        # Automatically trigger real email/Twilio/file logging in notifier
        alert_details = self.notifier.trigger_alerts(input_type, data, unified_response)
        
        # Merge alert delivery details into the unified response for frontend visualization
        unified_response["alert_delivery"] = {
            "logged": True,
            "record_id": alert_details["record"]["id"],
            "email_sent": alert_details["email_sent"],
            "email_status": alert_details["email_status"],
            "phone_called": alert_details["phone_called"],
            "phone_status": alert_details["phone_status"]
        }

        return unified_response


if __name__ == "__main__":
    shield = FraudShield()

    print("\n==========================================")
    print("[SHIELD] RUNNING MASTER CORE INTEGRATED TESTING [SHIELD]")
    print("==========================================\n")

    # 1. Test SMS
    print("--- 1. Testing High Risk SMS ---")
    sms_data = "Congratulations! You have won Rs 50,000 lottery! Click here to claim your prize now: http://fake-lotto-win.xyz"
    sms_res = shield.analyze("sms", sms_data)
    print(f"Risk Level: {sms_res['final_risk']}")
    print(f"Alert Message: {sms_res['user_alert']}")
    print(f"Notifications Status: {sms_res['alert_delivery']}")
    print("-" * 50 + "\n")

    # 2. Test URL
    print("--- 2. Testing High Risk Phishing URL ---")
    url_data = "http://192.168.1.1/update-account-bank-verify.xyz"
    url_res = shield.analyze("url", url_data)
    print(f"Risk Level: {url_res['final_risk']}")
    print(f"Alert Message: {url_res['user_alert']}")
    print(f"Notifications Status: {url_res['alert_delivery']}")
    print("-" * 50 + "\n")

    # 3. Test Transaction
    print("--- 3. Testing Suspicious Transaction ---")
    trans_data = {
        "amount": 95000,
        "hour": 3,
        "frequency_today": 12,
        "location_change": 1,
        "new_recipient": 1,
        "device_change": 1
    }
    trans_res = shield.analyze("transaction", trans_data)
    print(f"Risk Level: {trans_res['final_risk']}")
    print(f"Alert Message: {trans_res['user_alert']}")
    print(f"Notifications Status: {trans_res['alert_delivery']}")
    print("-" * 50 + "\n")
