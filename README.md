# 🛡️ Fraud Shield
> **Your Digital Safety Guard**

Fraud Shield is an AI-powered, real-time cybersecurity web application specifically designed to protect first-time internet and smartphone users from digital fraud.

**Hackathon:** Secure India Cyber Initiative  
**Domain:** AI + Cybersecurity + FinTech  

---

## 🎯 Problem Statement
As digital adoption accelerates, millions of first-time users are entering the online ecosystem. Unfortunately, these users are extremely vulnerable to SMS phishing, fake bank websites, and transaction fraud. Fraud Shield acts as an invisible protective layer, intercepting dangerous threats and explaining them in simple, jargon-free language to educate and protect the user.

---

## ✨ Features
- **💬 Real-Time SMS Analysis**: Instantly detects lottery scams, fake OTP requests, and spam.
- **🔗 Phishing Link Scanner**: Analyzes URL structures and TLDs to catch fake banking and login pages without needing an internet lookup.
- **💸 Transaction Anomaly Engine**: Learns your spending habits and flags highly unusual transaction amounts, times, or device changes.
- **📞 Live Voice Call Alerts**: Integrates Twilio API to automatically dial the user's phone with an urgent voice warning if a high-risk threat is scanned!
- **📧 Automated Email Reporting**: Dispatches comprehensive HTML incident reports directly to a registered safety email.
- **📜 Security Audit Ledger**: Maintains a permanent, real-time log of all detected cybersecurity threats.

---

## 🤖 AI/ML Models Used
| Model / Algorithm | Purpose | Library / Technology |
| --- | --- | --- |
| **mshenoda/roberta-spam** | SMS & Chat Spam Detection | HuggingFace Transformers |
| **RandomForestClassifier** | Feature-Engineered Phishing URL Detection | scikit-learn |
| **IsolationForest** | Unsupervised Transaction Anomaly Detection | scikit-learn / PyOD |

*(Note: The system features robust pure-Python fallbacks. If heavy ML packages are missing, the AI core automatically shifts to an optimized rule-based engine to ensure zero downtime!)*

---

## 🏗️ Tech Stack
| Layer | Technology |
| --- | --- |
| **Frontend** | React (Vite), HTML5, CSS3 Glassmorphism |
| **Backend API** | Python, FastAPI, Uvicorn |
| **Machine Learning** | PyTorch, Scikit-learn, Transformers |
| **Notifications** | Twilio SDK (Voice/SMS), smtplib (Email) |

---

## 📁 Project Structure
```text
fraud-shield/
├── backend/
│   ├── sms_detector.py        # RoBERTa message spam detector
│   ├── url_detector.py        # RF phishing URL detector
│   ├── transaction_detector.py# Isolation Forest anomaly detector
│   ├── notifier.py            # Email alerts & Twilio calls
│   ├── detector.py            # Master coordinated detector
│   ├── main.py                # FastAPI REST API with CORS
│   └── test_api.py            # Backend automated test script
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Premium Tabbed Dashboard UI & Ringing Simulator
│   │   └── App.css            # Dark Navy Glassmorphism styling
├── requirements.txt           # Python backend dependencies
└── .env                       # Credentials config file
```

---

## ⚙️ Setup & Installation

### 1. Backend Setup
Open a terminal and navigate to the `fraud-shield` directory:
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup
Open a second terminal and navigate to the `frontend` directory:
```bash
cd frontend
npm install
```

---

## 🚀 Running the App

**Start the FastAPI Backend:**
```bash
# Make sure your virtual environment is activated!
uvicorn backend.main:app --reload
```
*The backend will be live at `http://localhost:8000`*

**Start the React Frontend:**
```bash
cd frontend
npm run dev
```
*The dashboard will be live at `http://localhost:5173`*

---

## 🧪 Testing

To run the automated backend test suite (which tests the ML detectors across normal and suspicious payloads):
```bash
python backend/test_api.py
```

---

## 👥 Team Details
- **Developer 1**: AI & Backend Engineering
- **Developer 2**: React Frontend & UI/UX
- **Developer 3**: Cybersecurity & Integrations
