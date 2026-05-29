try:
    import numpy as np
except ImportError:
    np = None

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None


class TransactionDetector:
    def __init__(self):
        self.model = None
        self.error_state = False

        # Step 1: Generate synthetic normal transaction data (200 samples)
        # Features: [amount, hour, frequency_today, location_change, new_recipient, device_change]
        n_samples = 200

        try:
            if np is None or IsolationForest is None:
                raise ImportError("numpy or scikit-learn not available")
            np.random.seed(42)
            # Generate normal amounts: 100 to 5000 INR
            amounts = np.random.uniform(100, 5000, n_samples)
            # Generate normal hours: 8 AM to 10 PM (8 to 22)
            hours = np.random.randint(8, 23, n_samples)
            # Low frequency: 1 to 5 per day
            frequencies = np.random.randint(1, 6, n_samples)
            # location_change mostly 0 (95% same city, 5% different city)
            locations = np.random.choice([0, 1], size=n_samples, p=[0.95, 0.05])
            # new_recipient mostly 0 (90% known recipient, 10% new recipient)
            recipients = np.random.choice([0, 1], size=n_samples, p=[0.90, 0.10])
            # device_change mostly 0 (97% same device, 3% new device)
            devices = np.random.choice([0, 1], size=n_samples, p=[0.97, 0.03])

            # Combine into dataset
            X_train = np.column_stack((amounts, hours, frequencies, locations, recipients, devices))

            if IsolationForest is not None:
                # Step 2: Fit IsolationForest
                # contamination represents expected percentage of anomalies (e.g. 5%)
                self.model = IsolationForest(contamination=0.05, random_state=42)
                self.model.fit(X_train)
                print("[Transaction Detector] IsolationForest model trained successfully.")
            else:
                print("[Transaction Detector] Warning: scikit-learn missing. Running in rule-based mode.")
                self.error_state = True
        except Exception as e:
            print(f"[Transaction Detector] Initialization failed: {e}. Falling back to rules.")
            self.error_state = True

    def detect(self, transaction: dict) -> dict:
        """
        Analyzes a transaction for anomalies.
        Input format:
        {
            "amount": float,
            "hour": int,
            "frequency_today": int,
            "location_change": int,
            "new_recipient": int,
            "device_change": int
        }
        """
        amount = float(transaction.get("amount", 0.0))
        hour = int(transaction.get("hour", 12))
        frequency = int(transaction.get("frequency_today", 1))
        location_change = int(transaction.get("location_change", 0))
        new_recipient = int(transaction.get("new_recipient", 0))
        device_change = int(transaction.get("device_change", 0))

        # Check and flag reasons manually for transparent output
        flagged = []
        if amount > 50000:
            flagged.append(f"Very large amount (₹{amount:,.2f})")
        if hour < 6 or hour > 23:
            flagged.append(f"Late night transaction time ({hour}:00)")
        if frequency > 8:
            flagged.append(f"Unusual high speed of transactions ({frequency} times today)")
        if location_change == 1:
            flagged.append("Transacted from a completely new city")
        if new_recipient == 1:
            flagged.append("Money sent to a new, unverified person")
        if device_change == 1:
            flagged.append("Done from a new device/phone")

        # Create feature vector
        X_test = [amount, hour, frequency, location_change, new_recipient, device_change]

        if self.error_state or self.model is None:
            return self._fallback_detect(transaction, flagged)

        try:
            # IsolationForest predict returns 1 for inliers, -1 for outliers (anomalies)
            pred = self.model.predict([X_test])[0]
            # IsolationForest decision_function returns anomaly scores (lower = more anomalous)
            score = float(self.model.decision_function([X_test])[0])
            
            # Normalize anomaly score to [0.0, 1.0] where 1.0 is extremely anomalous
            # In scikit-learn, decision_function returns scores around [-0.5, 0.5]
            # Lower score = anomalous. Let's map it to an intuitive index:
            raw_anomaly_index = -score
            normalized_score = min(max((raw_anomaly_index + 0.5) / 1.0, 0.0), 1.0)

            is_suspicious = (pred == -1)

            # High risk rules if critical variables triggered
            if is_suspicious or amount > 80000 or (amount > 10000 and device_change == 1 and location_change == 1):
                is_suspicious = True
                risk_level = "HIGH" if (amount > 50000 or len(flagged) >= 3) else "MEDIUM"
                explanation = "This transaction is highly unusual compared to your normal spending habits."
            else:
                risk_level = "LOW"
                explanation = "This transaction looks normal and matches safe behavior patterns."

            return {
                "label": "SUSPICIOUS" if is_suspicious else "NORMAL",
                "anomaly_score": round(normalized_score, 4),
                "risk_level": risk_level,
                "flagged_reasons": flagged,
                "explanation": explanation
            }

        except Exception as e:
            print(f"[Transaction Detector] Inference error: {e}. Falling back to rules.")
            return self._fallback_detect(transaction, flagged)

    def _fallback_detect(self, transaction: dict, flagged: list) -> dict:
        """Rule-based backup scanner if sklearn is missing."""
        amount = float(transaction.get("amount", 0.0))
        device_change = int(transaction.get("device_change", 0))
        location_change = int(transaction.get("location_change", 0))

        # Basic logic
        is_suspicious = len(flagged) >= 2 or amount > 50000 or (device_change == 1 and location_change == 1)
        
        score = len(flagged) / 5.0
        score = min(max(score, 0.1), 0.95)

        if is_suspicious:
            risk_level = "HIGH" if (amount > 50000 or len(flagged) >= 3) else "MEDIUM"
            explanation = "Transaction shows signs of account takeover or credit abuse."
        else:
            risk_level = "LOW"
            explanation = "Transaction passes basic security guidelines."

        return {
            "label": "SUSPICIOUS" if is_suspicious else "NORMAL",
            "anomaly_score": round(score, 2),
            "risk_level": risk_level,
            "flagged_reasons": flagged,
            "explanation": explanation
        }


if __name__ == "__main__":
    detector = TransactionDetector()
    test_cases = [
        # Normal
        {"amount": 500, "hour": 14, "frequency_today": 2, "location_change": 0, "new_recipient": 0, "device_change": 0},
        # High Risk
        {"amount": 95000, "hour": 3, "frequency_today": 12, "location_change": 1, "new_recipient": 1, "device_change": 1},
        # Medium Risk
        {"amount": 6000, "hour": 23, "frequency_today": 4, "location_change": 0, "new_recipient": 1, "device_change": 1}
    ]

    print("\n--- RUNNING TRANSACTION DETECTOR TEST ---")
    for idx, tc in enumerate(test_cases, 1):
        res = detector.detect(tc)
        print(f"\nCase #{idx}: {tc}")
        print(f"Result: {res}")
