import re
from urllib.parse import urlparse
try:
    import numpy as np
except ImportError:
    np = None

try:
    from sklearn.ensemble import RandomForestClassifier
except ImportError:
    RandomForestClassifier = None


class URLDetector:
    def __init__(self):
        self.model = None
        self.error_state = False
        
        # Hardcoded 20 training URLs: 10 Safe, 10 Phishing
        # Columns match the 10 features extracted in _extract_features:
        # [length, has_ip, dots, hyphens, has_at, double_slash, has_https, keyword_score, tld_risk, subdomains]
        self.training_data = [
            # Safe URLs (Label 0)
            ("https://www.google.com", 0),
            ("https://www.wikipedia.org", 0),
            ("https://www.github.com", 0),
            ("https://www.amazon.in", 0),
            ("https://www.microsoft.com", 0),
            ("https://www.nytimes.com", 0),
            ("https://www.ndtv.com", 0),
            ("https://www.onlinesbi.sbi", 0),
            ("https://www.hdfcbank.com", 0),
            ("https://www.python.org", 0),
            # Phishing URLs (Label 1)
            ("http://192.168.1.1/secure-login-bank-verify.xyz", 1),
            ("http://free-gift-card-win-prize.tk", 1),
            ("http://verify-your-bank-account-update.ml", 1),
            ("http://secure-login.paytm-refund-cash.ga", 1),
            ("http://amazon-offers-free-shopping.cf", 1),
            ("http://login.hsbcc-verify-netbanking.gq", 1),
            ("http://netflix-free-premium-account.xyz", 1),
            ("http://login-sbi-netbanking-portal.tk", 1),
            ("http://facebook-security-check-update.ml", 1),
            ("http://claim-your-lotto-cash-now.cf", 1)
        ]

        try:
            if RandomForestClassifier is not None:
                # Train the model
                X = []
                y = []
                for url, label in self.training_data:
                    X.append(self._extract_features(url))
                    y.append(label)
                
                self.model = RandomForestClassifier(n_estimators=10, random_state=42)
                self.model.fit(X, y)
                print("[URL Detector] RandomForestClassifier trained successfully offline.")
            else:
                print("[URL Detector] Warning: scikit-learn is not installed. Running in rule-based mode.")
                self.error_state = True
        except Exception as e:
            print(f"[URL Detector] Model training failed: {e}. Falling back to rule-based logic.")
            self.error_state = True

    def _extract_features(self, url: str) -> list:
        """
        Extracts 10 numerical features from a URL for machine learning.
        """
        # Feature 1: URL Length
        url_length = len(url)

        # Feature 2: Has IP Address
        # Match pattern like http://192.168.1.1/... or http://203.0.113.5/...
        ip_pattern = r"https?://(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
        has_ip_address = 1 if re.search(ip_pattern, url) else 0

        # Feature 3: Count Dots
        count_dots = url.count(".")

        # Feature 4: Count Hyphens
        count_hyphens = url.count("-")

        # Feature 5: Count At Symbol (@)
        count_at_symbol = 1 if "@" in url else 0

        # Feature 6: Count Double Slashes (except after http:/https:)
        parsed = urlparse(url)
        count_double_slash = url.count("//") - 1
        count_double_slash = max(0, count_double_slash)

        # Feature 7: Has HTTPS
        has_https = 1 if url.lower().startswith("https") else 0

        # Feature 8: Suspicious Keywords Score
        suspicious_words = ["login", "verify", "bank", "update", "secure", "account", "free", "click", "win", "prize"]
        suspicious_keywords_score = sum(1 for word in suspicious_words if word in url.lower())

        # Feature 9: TLD Risk
        risky_tlds = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq"]
        tld_risk = 0
        for tld in risky_tlds:
            if tld in url.lower():
                tld_risk = 1
                break

        # Feature 10: Subdomain Count
        # e.g., login.verification.sbi-secure.xyz has domain sbi-secure.xyz and subdomains login, verification
        host = parsed.netloc or url.split("/")[2] if len(url.split("/")) > 2 else ""
        parts = host.split(".")
        subdomain_count = max(0, len(parts) - 2)

        return [
            url_length,
            has_ip_address,
            count_dots,
            count_hyphens,
            count_at_symbol,
            count_double_slash,
            has_https,
            suspicious_keywords_score,
            tld_risk,
            subdomain_count
        ]

    def detect(self, url: str) -> dict:
        """
        Scans a URL and determines whether it is phishing or safe.
        """
        if not url or not url.strip():
            return {
                "label": "SAFE",
                "confidence": 1.0,
                "risk_level": "LOW",
                "triggered_features": [],
                "explanation": "No link entered."
            }

        # Format URL if missing protocol
        url_formatted = url.strip()
        if not url_formatted.lower().startswith(("http://", "https://")):
            url_formatted = "http://" + url_formatted

        features = self._extract_features(url_formatted)
        
        # Track which features triggered/flagged the warning
        triggered = []
        if features[1] == 1: triggered.append("Uses raw IP address instead of domain")
        if features[2] > 3: triggered.append("High number of dots in domain")
        if features[3] > 2: triggered.append("Excessive hyphens in URL")
        if features[4] == 1: triggered.append("Contains '@' symbol (often hides actual destination)")
        if features[5] > 0: triggered.append("Redirect slash '//' detected inside link")
        if features[6] == 0: triggered.append("Does not use secure HTTPS protocol")
        if features[7] >= 2: triggered.append("Contains multiple scam keywords like 'login' or 'free'")
        if features[8] == 1: triggered.append("Uses an untrustworthy or risky domain extension (TLD)")
        if features[9] >= 2: triggered.append("Excessive subdomains")

        # Fallback to rule-based classification if model has an error
        if self.error_state or self.model is None:
            return self._fallback_detect(url_formatted, triggered)

        try:
            # Predict probability
            prob = self.model.predict_proba([features])[0]
            phishing_confidence = float(prob[1])
            is_phishing = phishing_confidence >= 0.5
            
            confidence = phishing_confidence if is_phishing else prob[0]
            
            # Formulate risk level
            if is_phishing:
                risk_level = "HIGH" if confidence > 0.75 else "MEDIUM"
                explanation = "This link looks highly suspicious. It mimics a bank or a login page to steal details."
            else:
                # If there are highly dangerous indicators, force high risk
                if features[1] == 1 or (features[6] == 0 and features[8] == 1):
                    is_phishing = True
                    confidence = 0.9
                    risk_level = "HIGH"
                    explanation = "This link is unsafe because it uses a raw IP address or insecure domain."
                else:
                    risk_level = "LOW"
                    explanation = "This link appears to be safe and points to a verified destination."

            return {
                "label": "PHISHING" if is_phishing else "SAFE",
                "confidence": round(confidence, 4),
                "risk_level": risk_level,
                "triggered_features": triggered,
                "explanation": explanation
            }
        except Exception as e:
            print(f"[URL Detector] Prediction error: {e}. Falling back to rule-based.")
            return self._fallback_detect(url_formatted, triggered)

    def _fallback_detect(self, url: str, triggered: list) -> dict:
        """Rule-based backup scanner if sklearn is missing."""
        is_phishing = len(triggered) >= 2 or any(
            x in ["Uses raw IP address instead of domain", "Uses an untrustworthy or risky domain extension (TLD)"]
            for x in triggered
        )

        confidence = 0.5 + (len(triggered) * 0.1)
        confidence = min(max(confidence, 0.5), 0.95)

        if is_phishing:
            risk_level = "HIGH" if len(triggered) >= 4 else "MEDIUM"
            explanation = "This link contains several security flags and could be a trap to steal passwords."
        else:
            risk_level = "LOW"
            explanation = "No major security flags were found in this link."

        return {
            "label": "PHISHING" if is_phishing else "SAFE",
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "triggered_features": triggered,
            "explanation": explanation
        }


if __name__ == "__main__":
    detector = URLDetector()
    test_urls = [
        "https://www.google.com",
        "http://192.168.1.1/bank-login-verify.xyz",
        "https://secure-login-hdfc-netbanking.tk/login.php"
    ]

    print("\n--- RUNNING URL DETECTOR TEST ---")
    for url in test_urls:
        res = detector.detect(url)
        print(f"\nURL: {url}")
        print(f"Result: {res}")
