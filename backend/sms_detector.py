import os
import sys

# Suppress Hugging Face warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

try:
    from transformers import pipeline
except ImportError:
    pipeline = None


class SMSDetector:
    def __init__(self):
        self.pipeline = None
        self.error_state = False
        print("[SMS Detector] Loading mshenoda/roberta-spam model...")
        try:
            if pipeline is not None:
                # Load RoBERTa spam model
                self.pipeline = pipeline("text-classification", model="mshenoda/roberta-spam")
                print("[SMS Detector] RoBERTa model loaded successfully.")
            else:
                print("[SMS Detector] Warning: transformers not installed. Running in simulation mode.")
                self.error_state = True
        except Exception as e:
            print(f"[SMS Detector] Error loading model: {e}. Falling back to rule-based detection.")
            self.error_state = True

    def detect(self, message: str) -> dict:
        """
        Detects if an SMS message is spam or safe.
        Returns:
            dict: {
                "label": "SPAM" or "SAFE",
                "confidence": float,
                "risk_level": "HIGH" or "LOW",
                "explanation": "Plain English description"
            }
        """
        if not message or not message.strip():
            return {
                "label": "SAFE",
                "confidence": 1.0,
                "risk_level": "LOW",
                "explanation": "No text provided to analyze."
            }

        # If model failed to load, fall back to robust rule-based logic
        if self.error_state or self.pipeline is None:
            return self._fallback_detect(message)

        try:
            # Run inference
            results = self.pipeline(message)
            if not results:
                return self._fallback_detect(message)

            result = results[0]
            label = result["label"].upper()  # Expecting 'LABEL_0' or 'LABEL_1' or 'SPAM'/'HAM'
            score = float(result["score"])

            # Map the model's labels
            # mshenoda/roberta-spam: LABEL_0 is typically Ham (Safe), LABEL_1 is Spam
            is_spam = False
            if label == "LABEL_1" or "SPAM" in label:
                is_spam = True

            # If confidence is low, cross check with basic keywords
            if is_spam:
                confidence = score
                risk_level = "HIGH" if confidence > 0.75 else "MEDIUM"
                explanation = "This message matches common patterns used in online scams or spam."
            else:
                confidence = score
                # Double-check for highly suspicious keywords even if model missed it
                trigger_words = ["won", "lottery", "gift card", "otp", "block", "verify", "click here", "cash prize", "rs."]
                matching = [w for w in trigger_words if w in message.lower()]
                if len(matching) >= 2:
                    is_spam = True
                    confidence = 0.8
                    risk_level = "HIGH"
                    explanation = f"Model classified as safe, but message contains multiple suspicious terms: {', '.join(matching)}."
                else:
                    risk_level = "LOW"
                    explanation = "This message appears safe. It does not contain typical scam patterns."

            return {
                "label": "SPAM" if is_spam else "SAFE",
                "confidence": round(confidence, 4),
                "risk_level": risk_level,
                "explanation": explanation
            }

        except Exception as e:
            print(f"[SMS Detector] Inference error: {e}. Using fallback.")
            return self._fallback_detect(message)

    def _fallback_detect(self, message: str) -> dict:
        """Rule-based backup scanner if transformers package or downloading fails."""
        msg_lower = message.lower()
        spam_keywords = [
            "win", "won", "lottery", "cash", "prize", "gift", "crore", "lakh", "rs.", "free",
            "click", "link", "claim", "verify", "update", "bank", "suspend", "otp", "paytm",
            "gpay", "phonepe", "upi", "card", "loan", "approved", "congratulations", "bonus"
        ]

        matches = [word for word in spam_keywords if word in msg_lower]
        score = len(matches) / 5.0  # Normalized score
        score = min(max(score, 0.1), 0.95)

        is_spam = len(matches) >= 2 or ("otp" in msg_lower and "share" in msg_lower) or ("click" in msg_lower and "claim" in msg_lower)

        if is_spam:
            risk_level = "HIGH" if len(matches) >= 4 else "MEDIUM"
            explanation = f"Detected multiple suspicious words like: {', '.join(matches[:3])}."
        else:
            risk_level = "LOW"
            explanation = "No typical spam keywords or patterns detected."

        return {
            "label": "SPAM" if is_spam else "SAFE",
            "confidence": round(score, 2),
            "risk_level": risk_level,
            "explanation": explanation
        }


if __name__ == "__main__":
    detector = SMSDetector()
    test_cases = [
        "Congratulations! You have won a cash prize of Rs 50,000! Click here to claim now: http://win-prize.xyz",
        "Hi Mom, I will be home by 6 PM. Please make tea.",
        "URGENT: Your bank account is locked. Please verify your OTP 8831 to unlock immediately."
    ]

    print("\n--- RUNNING SMS DETECTOR TEST ---")
    for tc in test_cases:
        res = detector.detect(tc)
        print(f"\nInput: {tc}")
        print(f"Result: {res}")
