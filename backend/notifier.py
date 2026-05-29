import os
import json
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# File path to keep records of fraud events
RECORDS_FILE = os.path.join(os.path.dirname(__file__), "fraud_records.json")

# Try importing Twilio
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None


class Notifier:
    def __init__(self):
        # Default alert targets (from .env or falling back)
        self.target_email = os.getenv("REGISTERED_EMAIL", "demo-user@example.com")
        self.target_phone = os.getenv("REGISTERED_PHONE", "+919876543210")

        # SMTP config
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")

        # Twilio config
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from = os.getenv("TWILIO_FROM_NUMBER", "")

        # Ensure records file exists
        if not os.path.exists(RECORDS_FILE):
            with open(RECORDS_FILE, "w") as f:
                json.dump([], f)

    def update_config(self, email: str, phone: str) -> None:
        """Update registered email and phone number dynamically from UI."""
        if email:
            self.target_email = email.strip()
        if phone:
            self.target_phone = phone.strip()
        print(f"[Notifier] Targets updated to: Email={self.target_email}, Phone={self.target_phone}")

    def log_fraud_event(self, event_type: str, data: any, risk_level: str, alert_message: str) -> dict:
        """Saves a permanent record of the fraud event in a local JSON database."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        record = {
            "id": f"FRD-{int(datetime.datetime.now().timestamp())}",
            "timestamp": timestamp,
            "event_type": event_type.upper(),
            "data_preview": str(data)[:200],  # Truncate very long texts
            "risk_level": risk_level,
            "alert_message": alert_message,
            "status": "FLAGGED_AND_ALERTED"
        }

        try:
            with open(RECORDS_FILE, "r") as f:
                records = json.load(f)
        except Exception:
            records = []

        # Add to beginning of list (latest first)
        records.insert(0, record)

        # Cap records at 100 entries for performance
        records = records[:100]

        try:
            with open(RECORDS_FILE, "w") as f:
                json.dump(records, f, indent=4)
            print(f"[Notifier] Fraud event logged successfully: {record['id']}")
        except Exception as e:
            print(f"[Notifier] Failed to write to log file: {e}")

        return record

    def get_records(self) -> list:
        """Retrieve audit history log."""
        try:
            with open(RECORDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def trigger_alerts(self, event_type: str, raw_data: any, analysis_result: dict) -> dict:
        """Triggers email and Twilio alerts for HIGH risk items."""
        risk_level = analysis_result.get("final_risk", "LOW")
        alert_message = analysis_result.get("user_alert", "A security alert occurred.")
        safety_tip = analysis_result.get("safety_tip", "Stay vigilant.")

        # Log the incident first (all cases)
        log_record = self.log_fraud_event(event_type, raw_data, risk_level, alert_message)

        # Trigger actual notifications ONLY for HIGH or MEDIUM-HIGH risk
        email_sent = False
        phone_called = False
        email_status = "Skipped (Low Risk)"
        phone_status = "Skipped (Low Risk)"

        if risk_level == "HIGH":
            # 1. Send Email Alert
            email_sent, email_status = self.send_email_alert(event_type, raw_data, alert_message, safety_tip, log_record["id"])
            # 2. Trigger Twilio Voice Call & SMS
            self.send_twilio_sms(event_type, raw_data, alert_message)
            phone_called, phone_status = self.make_twilio_call(event_type, alert_message)

        return {
            "record": log_record,
            "email_sent": email_sent,
            "email_status": email_status,
            "phone_called": phone_called,
            "phone_status": phone_status
        }

    def send_email_alert(self, event_type: str, data: any, alert: str, tip: str, incident_id: str) -> tuple:
        """Sends an HTML formatted security alert to the registered email."""
        if not self.smtp_username or not self.smtp_password or not self.sender_email:
            print("[Notifier] SMTP credentials not set. Simulated Email Alert logged.")
            return False, "Not configured (.env variables missing)"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 SECURITY WARNING: High Risk {event_type.upper()} Detected! 🛡️"
            msg["From"] = f"Fraud Shield Guard <{self.sender_email}>"
            msg["To"] = self.target_email

            # Professional responsive HTML body
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f6f9fc; color: #333333; }}
                    .card {{ background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); max-width: 600px; margin: 0 auto; overflow: hidden; border: 1px solid #e1e8ed; }}
                    .header {{ background: linear-gradient(135deg, #d32f2f, #b71c1c); color: #ffffff; padding: 30px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; letter-spacing: 0.5px; }}
                    .content {{ padding: 30px; line-height: 1.6; }}
                    .warning-box {{ background-color: #ffebee; border-left: 6px solid #d32f2f; padding: 15px; border-radius: 4px; margin-bottom: 25px; }}
                    .warning-box p {{ margin: 0; font-size: 16px; font-weight: bold; color: #b71c1c; }}
                    .detail-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; }}
                    .detail-table td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
                    .detail-table td.label {{ font-weight: bold; color: #555555; width: 35%; }}
                    .tip-box {{ background-color: #e3f2fd; border-left: 6px solid #1976d2; padding: 15px; border-radius: 4px; color: #0d47a1; margin-bottom: 25px; }}
                    .tip-box h4 {{ margin: 0 0 5px 0; font-size: 15px; }}
                    .tip-box p {{ margin: 0; }}
                    .footer {{ background-color: #f5f5f5; text-align: center; padding: 20px; font-size: 12px; color: #777777; border-top: 1px solid #e1e8ed; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="header">
                        <h1>🛡️ FRAUD SHIELD ALERT</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Real-Time Digital Safety Guard</p>
                    </div>
                    <div class="content">
                        <div class="warning-box">
                            <p>Warning: A high-risk security hazard has been detected!</p>
                        </div>
                        <table class="detail-table">
                            <tr>
                                <td class="label">Incident ID</td>
                                <td><code>{incident_id}</code></td>
                            </tr>
                            <tr>
                                <td class="label">Scan Type</td>
                                <td><b style="color: #d32f2f;">{event_type.upper()} SCAN</b></td>
                            </tr>
                            <tr>
                                <td class="label">Time Detected</td>
                                <td>{datetime.datetime.now().strftime("%I:%M %p, %d-%b-%Y")}</td>
                            </tr>
                            <tr>
                                <td class="label">Scanned Data</td>
                                <td style="word-break: break-all; font-family: monospace; background: #fafafa; padding: 8px; border: 1px solid #eee; border-radius: 4px;">{data}</td>
                            </tr>
                        </table>

                        <p style="font-size: 16px; font-weight: bold; color: #222222; margin-bottom: 8px;">🛡️ Safety Advisory:</p>
                        <p style="margin-top: 0; font-size: 15px; color: #444444;">"{alert}"</p>

                        <div class="tip-box">
                            <h4>💡 Actionable Safety Tip:</h4>
                            <p>{tip}</p>
                        </div>
                        
                        <p style="font-size: 13px; color: #666; text-align: center;">This is an automated safety alert from your Fraud Shield app to secure your transactions.</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 Fraud Shield Guard. Secure India Cyber Hackathon Initiative.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html, "html"))

            # SMTP Connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.sender_email, self.target_email, msg.as_string())
            server.quit()
            
            print(f"[Notifier] Real Email warning successfully delivered to {self.target_email}!")
            return True, "Delivered"
        except Exception as e:
            print(f"[Notifier] SMTP email sending failed: {e}")
            return False, f"Failed: {str(e)}"

    def make_twilio_call(self, event_type: str, warning_message: str) -> tuple:
        """Triggers a real voice call using Twilio API warning the user."""
        if not self.twilio_sid or not self.twilio_token or not self.twilio_from:
            print("[Notifier] Twilio credentials not set. Simulated call alert logged.")
            return False, "Not configured (.env variables missing)"

        if TwilioClient is None:
            print("[Notifier] Twilio SDK not installed. Simulated call alert logged.")
            return False, "Twilio library not installed"

        try:
            client = TwilioClient(self.twilio_sid, self.twilio_token)
            
            # Simple warning text converted to voice call TwiML instructions
            twiml_content = f"""<Response>
                <Say voice="alice" language="en-IN">
                    Attention! This is a dynamic call from Fraud Shield Security.
                    A high risk threat was just detected in your recent {event_type}. 
                    Warning details: {warning_message}
                    Please do not click any links, do not share any login passcodes, and keep your mobile safe.
                    Fraud Shield is securing your device now. Goodbye.
                </Say>
            </Response>"""

            call = client.calls.create(
                twiml=twiml_content,
                to=self.target_phone,
                from_=self.twilio_from
            )
            print(f"[Notifier] Twilio voice warning initiated! Call SID: {call.sid}")
            return True, f"Dialing (SID: {call.sid[:8]}...)"
        except Exception as e:
            print(f"[Notifier] Twilio API call failed: {e}")
            return False, f"Failed: {str(e)}"

    def send_twilio_sms(self, event_type: str, raw_data: any, warning_message: str) -> tuple:
        """Sends a structured SMS alert using Twilio API."""
        if not self.twilio_sid or not self.twilio_token or not self.twilio_from:
            return False, "Not configured"
        if TwilioClient is None:
            return False, "Twilio library not installed"
        try:
            client = TwilioClient(self.twilio_sid, self.twilio_token)
            
            sms_body = (
                f"🚨 FRAUD SHIELD ALERT 🚨\n\n"
                f"High-Risk {event_type.upper()} Detected!\n\n"
                f"Warning: {warning_message}\n\n"
                f"Payload:\n{str(raw_data)[:100]}\n\n"
                f"Stay Safe! Do not interact with the payload."
            )

            message = client.messages.create(
                body=sms_body,
                to=self.target_phone,
                from_=self.twilio_from
            )
            print(f"[Notifier] Twilio SMS warning sent! MSG SID: {message.sid}")
            return True, f"Sent (SID: {message.sid[:8]}...)"
        except Exception as e:
            print(f"[Notifier] Twilio SMS failed: {e}")
            return False, f"Failed: {str(e)}"



if __name__ == "__main__":
    notifier = Notifier()
    # Test logging
    notifier.log_fraud_event(
        "sms", 
        "Congratulations! Claim Rs. 50,000", 
        "HIGH", 
        "This message seems like a scam asking you to click link."
    )
    print("Logged events list:")
    print(notifier.get_records())
