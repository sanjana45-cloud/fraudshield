import requests
import json
import time

BASE_URL = "http://localhost:8000"


def print_separator(title=None):
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print(f"\n{'-'*60}")


def test_health():
    print_separator("TESTING BACKEND HEALTH")
    try:
        res = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Error: FastAPI server is not running! Start it with: uvicorn main:app --reload")
        return False
    return True


def test_sms():
    print_separator("TESTING SMS ANALYZER")
    
    test_cases = [
        {"message": "Congratulations! You have won a lottery of Rs 50,000! Click here to claim your cash reward now: http://prize-win.xyz"},
        {"message": "Hey friend, are we still meeting for lunch today at 1 PM?"},
        {"message": "URGENT: Your HDFC bank account is locked. Please share your OTP 4821 to unlock immediately."}
    ]

    for tc in test_cases:
        try:
            res = requests.post(f"{BASE_URL}/analyze/sms", json=tc)
            data = res.json()
            print(f"\n[Input Message]: \"{tc['message']}\"")
            print(f"Risk Level:     [{data['final_risk']}]")
            print(f"User Alert:     {data['user_alert']}")
            print(f"Safety Tip:     {data['safety_tip']}")
            print(f"Alert Delivery: {data['alert_delivery']}")
        except Exception as e:
            print(f"Failed to scan message: {e}")


def test_url():
    print_separator("TESTING URL ANALYZER")
    
    test_cases = [
        {"url": "http://192.168.1.1/secure-bank-login-verify.php"},
        {"url": "https://www.google.com"},
        {"url": "http://free-iphone-claim.tk/win"}
    ]

    for tc in test_cases:
        try:
            res = requests.post(f"{BASE_URL}/analyze/url", json=tc)
            data = res.json()
            print(f"\n[Input URL]:    \"{tc['url']}\"")
            print(f"Risk Level:     [{data['final_risk']}]")
            print(f"User Alert:     {data['user_alert']}")
            print(f"Safety Tip:     {data['safety_tip']}")
            print(f"Alert Delivery: {data['alert_delivery']}")
        except Exception as e:
            print(f"Failed to scan URL: {e}")


def test_transaction():
    print_separator("TESTING TRANSACTION ANALYZER")
    
    test_cases = [
        # Suspicious Transaction
        {
            "amount": 95000.0,
            "hour": 3,
            "frequency_today": 12,
            "location_change": 1,
            "new_recipient": 1,
            "device_change": 1
        },
        # Normal Transaction
        {
            "amount": 450.0,
            "hour": 14,
            "frequency_today": 2,
            "location_change": 0,
            "new_recipient": 0,
            "device_change": 0
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        try:
            res = requests.post(f"{BASE_URL}/analyze/transaction", json=tc)
            data = res.json()
            print(f"\n[Transaction Case #{idx}]: Amount ₹{tc['amount']}, Hour {tc['hour']}, New Device: {tc['device_change']}")
            print(f"Risk Level:     [{data['final_risk']}]")
            print(f"User Alert:     {data['user_alert']}")
            print(f"Safety Tip:     {data['safety_tip']}")
            print(f"Alert Delivery: {data['alert_delivery']}")
        except Exception as e:
            print(f"Failed to scan Transaction: {e}")


def test_audit_logs():
    print_separator("TESTING AUDIT LOG RETRIEVAL")
    try:
        res = requests.get(f"{BASE_URL}/alerts/records")
        records = res.json()
        print(f"Successfully retrieved {len(records)} logged fraud events.")
        if records:
            print(f"Latest logged record details:")
            print(json.dumps(records[0], indent=2))
    except Exception as e:
        print(f"Failed to fetch records: {e}")


if __name__ == "__main__":
    print("🚀 STARTING E2E BACKEND API VERIFICATION SUITE...")
    if test_health():
        test_sms()
        test_url()
        test_transaction()
        test_audit_logs()
        print_separator("TESTING COMPLETE!")
