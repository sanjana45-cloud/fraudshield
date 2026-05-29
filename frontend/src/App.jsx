import React, { useState, useEffect } from "react";
import "./App.css";
import ExplainerButton from "./ExplainerButton";
import {
  Shield, ShieldCheck, ShieldAlert,
  Link as LinkIcon, MessageSquare, CreditCard,
  AlertTriangle, XCircle, CheckCircle,
  Loader2, Wifi, Zap, Bell, Lightbulb, Flag,
  PhoneCall, PhoneOff, Phone, Volume2,
  MapPin, UserPlus, Smartphone
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

function App() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [activeTab, setActiveTab] = useState("sms");

  // Input fields
  const [smsText, setSmsText] = useState("");
  const [urlText, setUrlText] = useState("");
  const [amount, setAmount] = useState("");
  const [hour, setHour] = useState("");
  const [frequency, setFrequency] = useState("");
  const [locChange, setLocChange] = useState(0);
  const [recipChange, setRecipChange] = useState(0);
  const [devChange, setDevChange] = useState(0);

  // Settings configs
  const [registeredEmail, setRegisteredEmail] = useState("demo-user@example.com");
  const [registeredPhone, setRegisteredPhone] = useState("+919876543210");
  const [alertSettingsMsg, setAlertSettingsMsg] = useState("");
  const [isUpdatingSettings, setIsUpdatingSettings] = useState(false);

  // Status variables
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);

  // Ringing Phone Call Simulator States
  const [showCallModal, setShowCallModal] = useState(false);
  const [callState, setCallState] = useState("ringing");
  const [simulatedWarningText, setSimulatedWarningText] = useState("");

  // WhatsApp toast
  const [showWhatsAppToast, setShowWhatsAppToast] = useState(false);

  // Sound generator helper for call ringing & speech warning
  const playAlertSound = (type) => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (type === "ring") {
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();
        osc1.type = "sine";
        osc1.frequency.setValueAtTime(440, ctx.currentTime);
        osc2.type = "sine";
        osc2.frequency.setValueAtTime(480, ctx.currentTime);
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);
        osc1.start();
        osc2.start();
        setTimeout(() => {
          osc1.stop();
          osc2.stop();
        }, 800);
      } else if (type === "voice") {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(220, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 0.5);
        gain.gain.setValueAtTime(0.05, ctx.currentTime);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        setTimeout(() => osc.stop(), 500);

        if ('speechSynthesis' in window) {
          const msg = new SpeechSynthesisUtterance();
          msg.text = "Warning! Fraud Shield detected a high risk scam. Please check your screen now. Do not share passwords or pay money.";
          msg.voice = window.speechSynthesis.getVoices().find(v => v.lang.includes("en")) || null;
          window.speechSynthesis.speak(msg);
        }
      }
    } catch (e) {
      console.warn("Audio context not supported or user gesture needed:", e);
    }
  };

  // Ringing loop
  useEffect(() => {
    let interval;
    if (showCallModal && callState === "ringing") {
      playAlertSound("ring");
      interval = setInterval(() => {
        playAlertSound("ring");
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [showCallModal, callState]);

  // Fetch Audit Logs on load
  const fetchAuditLogs = async () => {
    setLogsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alerts/records`);
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error("Error fetching logs:", err);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  // Update backend config
  const handleUpdateConfig = async (e) => {
    e.preventDefault();
    setIsUpdatingSettings(true);
    setAlertSettingsMsg("");
    try {
      const res = await fetch(`${API_BASE}/alerts/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: registeredEmail, phone: registeredPhone })
      });
      if (res.ok) {
        setAlertSettingsMsg("Security contacts updated.");
        setTimeout(() => setAlertSettingsMsg(""), 3000);
      } else {
        setAlertSettingsMsg("Failed to save configurations.");
      }
    } catch (err) {
      setAlertSettingsMsg("Network connection failed.");
    } finally {
      setIsUpdatingSettings(false);
    }
  };

  const getRawInputForExplainer = () => {
    if (activeTab === "sms") return smsText;
    if (activeTab === "url") return urlText;
    if (activeTab === "transaction") return `Amount: ₹${amount}, Hour: ${hour}, Frequency: ${frequency}, New Loc: ${locChange}, New Device: ${devChange}`;
    return "";
  };

  // Core analysis runner
  const handleScan = async (type) => {
    setLoading(true);
    setError(null);
    setResult(null);

    let endpoint = "";
    let payload = {};

    if (type === "sms") {
      if (!smsText.trim()) {
        setError("Please paste a text message first.");
        setLoading(false);
        return;
      }
      endpoint = "/analyze/sms";
      payload = { message: smsText };
    } else if (type === "url") {
      if (!urlText.trim()) {
        setError("Please enter a link/URL first.");
        setLoading(false);
        return;
      }
      endpoint = "/analyze/url";
      payload = { url: urlText };
    } else if (type === "transaction") {
      if (!amount || !hour || !frequency) {
        setError("Please fill out all numerical transaction fields.");
        setLoading(false);
        return;
      }
      endpoint = "/analyze/transaction";
      payload = {
        amount: parseFloat(amount),
        hour: parseInt(hour),
        frequency_today: parseInt(frequency),
        location_change: locChange,
        new_recipient: recipChange,
        device_change: devChange
      };
    }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("Service unavailable. Verify backend API is running.");
      }

      const data = await res.json();
      setResult(data);

      // Trigger Ringing call warning popup for HIGH risk
      if (data.final_risk === "HIGH") {
        setSimulatedWarningText(data.user_alert);
        setCallState("ringing");
        setShowCallModal(true);

        // Show WhatsApp toast
        setShowWhatsAppToast(true);
        setTimeout(() => setShowWhatsAppToast(false), 4000);
      }

      fetchAuditLogs();
    } catch (err) {
      setError(err.message || "Something went wrong. Please check your network and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerCall = () => {
    setCallState("answered");
    playAlertSound("voice");
  };

  const handleHangupCall = () => {
    setCallState("hungup");
    setTimeout(() => {
      setShowCallModal(false);
    }, 800);
  };

  // ─── WELCOME SCREEN ───────────────────────────────────
  if (showWelcome) {
    return (
      <div className="welcome-container">
        <div className="welcome-card fade-in">
          <div className="welcome-icon-wrap">
            <Shield size={64} className="welcome-logo" />
          </div>
          <h1 className="welcome-title">FRAUD SHIELD</h1>
          <p className="welcome-subtitle">
            Advanced AI-Powered Cybersecurity Protocol<br />
            for Real-Time Fraud Detection
          </p>
          <div className="welcome-divider" />
          <button className="scan-btn" onClick={() => setShowWelcome(false)}>
            <Zap size={16} /> INITIALIZE SECURITY CORE
          </button>
        </div>
      </div>
    );
  }

  // ─── MAIN DASHBOARD ───────────────────────────────────
  return (
    <>
      {/* HEADER */}
      <header className="app-header">
        <div className="logo-section">
          <Shield size={28} className="logo-icon" />
          <div className="logo-text-group">
            <h1>FRAUD SHIELD</h1>
            <span className="subtitle">Real-time fraud protection</span>
          </div>
        </div>
        <div className="system-status">
          <div className="status-dot" /> System Active
        </div>
      </header>

      <div className="App-container">
        {/* DASHBOARD GRID */}
        <div className="dashboard-grid">

          {/* LEFT COLUMN: SCANNERS */}
          <div className="main-scanner-card">
            {/* TABS */}
            <div className="tabs-header">
              <button
                className={`tab-btn ${activeTab === "sms" ? "active" : ""}`}
                onClick={() => { setActiveTab("sms"); setResult(null); setError(null); }}
              >
                <MessageSquare size={16} /> <span className="tab-label">Check Message</span>
              </button>
              <button
                className={`tab-btn ${activeTab === "url" ? "active" : ""}`}
                onClick={() => { setActiveTab("url"); setResult(null); setError(null); }}
              >
                <LinkIcon size={16} /> <span className="tab-label">Check Link</span>
              </button>
              <button
                className={`tab-btn ${activeTab === "transaction" ? "active" : ""}`}
                onClick={() => { setActiveTab("transaction"); setResult(null); setError(null); }}
              >
                <CreditCard size={16} /> <span className="tab-label">Check Payment</span>
              </button>
            </div>

            {/* TAB CONTENTS */}
            <div className="tabs-content">
              {activeTab === "sms" && (
                <div className="input-group fade-in">
                  <label>Paste the SMS or message below</label>
                  <textarea
                    placeholder="e.g. Congratulations! You won Rs 50,000 cash reward. Click here to claim: http://fake-lotto.xyz"
                    value={smsText}
                    onChange={(e) => setSmsText(e.target.value)}
                    rows="4"
                  />
                  <button
                    className={`scan-btn ${loading ? 'scanning' : ''}`}
                    disabled={loading}
                    onClick={() => handleScan("sms")}
                  >
                    {loading ? <Loader2 size={16} className="spinner" /> : <><Zap size={16} /> ANALYZE MESSAGE</>}
                  </button>
                </div>
              )}

              {activeTab === "url" && (
                <div className="input-group fade-in">
                  <label>Paste the website link below</label>
                  <input
                    type="text"
                    className="input-url"
                    placeholder="e.g. http://192.168.1.1/update-account-bank-verify.xyz"
                    value={urlText}
                    onChange={(e) => setUrlText(e.target.value)}
                  />
                  <button
                    className={`scan-btn ${loading ? 'scanning' : ''}`}
                    disabled={loading}
                    onClick={() => handleScan("url")}
                  >
                    {loading ? <Loader2 size={16} className="spinner" /> : <><Zap size={16} /> ANALYZE URL</>}
                  </button>
                </div>
              )}

              {activeTab === "transaction" && (
                <div className="input-group fade-in">
                  <label className="section-title">Transaction Details</label>

                  <div className="form-row">
                    <div className="form-col">
                      <label>Amount (₹)</label>
                      <input
                        type="number"
                        placeholder="e.g. 15000"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                      />
                    </div>
                    <div className="form-col">
                      <label>Hour of Day (0-23)</label>
                      <input
                        type="number"
                        placeholder="e.g. 14 for 2 PM"
                        min="0"
                        max="23"
                        value={hour}
                        onChange={(e) => setHour(e.target.value)}
                      />
                    </div>
                    <div className="form-col">
                      <label>Payments Today</label>
                      <input
                        type="number"
                        placeholder="e.g. 3"
                        value={frequency}
                        onChange={(e) => setFrequency(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="toggles-container">
                    <div className="toggle-item">
                      <span className="toggle-item-label">
                        <MapPin size={16} /> New City / Location Change?
                      </span>
                      <button
                        className={`toggle-btn ${locChange === 1 ? "active" : ""}`}
                        onClick={() => setLocChange(locChange === 1 ? 0 : 1)}
                      >
                        {locChange === 1 ? "YES" : "NO"}
                      </button>
                    </div>
                    <div className="toggle-item">
                      <span className="toggle-item-label">
                        <UserPlus size={16} /> Sent to a New Recipient?
                      </span>
                      <button
                        className={`toggle-btn ${recipChange === 1 ? "active" : ""}`}
                        onClick={() => setRecipChange(recipChange === 1 ? 0 : 1)}
                      >
                        {recipChange === 1 ? "YES" : "NO"}
                      </button>
                    </div>
                    <div className="toggle-item">
                      <span className="toggle-item-label">
                        <Smartphone size={16} /> Done from a New Device?
                      </span>
                      <button
                        className={`toggle-btn ${devChange === 1 ? "active" : ""}`}
                        onClick={() => setDevChange(devChange === 1 ? 0 : 1)}
                      >
                        {devChange === 1 ? "YES" : "NO"}
                      </button>
                    </div>
                  </div>

                  <button
                    className={`scan-btn ${loading ? 'scanning' : ''}`}
                    disabled={loading}
                    onClick={() => handleScan("transaction")}
                  >
                    {loading ? <Loader2 size={16} className="spinner" /> : <><Zap size={16} /> ANALYZE PAYMENT</>}
                  </button>
                </div>
              )}

              {/* ERROR DISPLAY */}
              {error && (
                <div className="alert-box error-alert fade-in">
                  <AlertTriangle size={18} />
                  <div>
                    <h4>Scan Error</h4>
                    <p>{error}</p>
                  </div>
                </div>
              )}

              {/* RESULT */}
              {result && (
                <div className={`result-card fade-in border-${result.final_risk.toLowerCase()}`}>
                  <div className="result-header">
                    <h3><Shield size={16} /> Scan Result</h3>
                    <span className={`risk-badge badge-${result.final_risk.toLowerCase()}`}>
                      <div className="dot" />
                      {result.final_risk} RISK
                    </span>
                  </div>

                  <div className="result-body">
                    <div className="alert-message">
                      <p>{result.user_alert}</p>
                    </div>

                    {result.result.confidence && (
                      <div className="stat-row">
                        <span>AI Detection Confidence</span>
                        <strong>{(result.result.confidence * 100).toFixed(1)}%</strong>
                      </div>
                    )}

                    {result.result.triggered_features && result.result.triggered_features.length > 0 && (
                      <div className="feature-flags">
                        <span>Security Flags Tripped</span>
                        <ul>
                          {result.result.triggered_features.map((f, i) => (
                            <li key={i}><Flag size={14} /> {f}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.result.flagged_reasons && result.result.flagged_reasons.length > 0 && (
                      <div className="feature-flags">
                        <span>Suspicious Actions Flagged</span>
                        <ul>
                          {result.result.flagged_reasons.map((r, i) => (
                            <li key={i}><Flag size={14} /> {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="tip-box-ui">
                      <h4><Lightbulb size={14} /> What to do now</h4>
                      <p>{result.safety_tip}</p>
                    </div>

                    <ExplainerButton
                      riskLevel={result.final_risk}
                      inputType={result.input_type || activeTab}
                      rawInput={getRawInputForExplainer()}
                      userAlert={result.user_alert}
                    />

                    {/* Notification Status */}
                    <div className="notif-bar">
                      <span className="notif-bar-label">
                        <Bell size={12} /> Alert Delivery
                      </span>
                      <span className="notif-pill">
                        {result.alert_delivery.email_sent
                          ? <><CheckCircle size={12} /> Email Sent</>
                          : <><XCircle size={12} /> Email Off</>}
                      </span>
                      <span className="notif-pill">
                        {result.alert_delivery.phone_called
                          ? <><CheckCircle size={12} /> Call Dialed</>
                          : <><XCircle size={12} /> Call Off</>}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: SIDEBAR */}
          <div className="side-column">
            {/* ALERT SETTINGS */}
            <div className="side-card">
              <h3><Bell size={16} /> Alert Targets</h3>
              <p className="card-desc">Configure emergency notification contacts.</p>

              <form onSubmit={handleUpdateConfig} className="settings-form">
                <div className="input-row">
                  <label>Registered Email</label>
                  <input
                    type="email"
                    value={registeredEmail}
                    onChange={(e) => setRegisteredEmail(e.target.value)}
                    placeholder="name@example.com"
                    required
                  />
                </div>
                <div className="input-row">
                  <label>Phone Number</label>
                  <input
                    type="tel"
                    value={registeredPhone}
                    onChange={(e) => setRegisteredPhone(e.target.value)}
                    placeholder="+919876543210"
                    required
                  />
                </div>

                <button type="submit" disabled={isUpdatingSettings} className="save-settings-btn">
                  {isUpdatingSettings ? "Saving..." : "UPDATE CONFIG"}
                </button>

                {alertSettingsMsg && <p className="settings-msg">{alertSettingsMsg}</p>}
              </form>
            </div>

            {/* LIVE THREAT FEED */}
            <div className="side-card audit-log-card">
              <div className="audit-header">
                <h3><Wifi size={14} /> Live Threat Feed</h3>
              </div>
              <p className="feed-subtitle">Updated in real-time</p>

              {logsLoading ? (
                <div>
                  <div className="skeleton-card" />
                  <div className="skeleton-card" />
                  <div className="skeleton-card" />
                </div>
              ) : auditLogs.length === 0 ? (
                <p className="log-empty-text">No threats detected in the last hour</p>
              ) : (
                <div className="log-list">
                  {auditLogs.map((log) => (
                    <div key={log.id} className={`log-item border-${log.risk_level.toLowerCase()}`}>
                      <div className="log-item-header">
                        <span className="log-id">{log.id}</span>
                        <span className="log-time">{log.timestamp}</span>
                      </div>
                      <div className="log-item-body">
                        <div>
                          <strong>{log.event_type} Scan</strong>
                          <span className={`log-badge badge-${log.risk_level.toLowerCase()}`}>
                            {log.risk_level}
                          </span>
                        </div>
                        <p className="log-preview">"{log.data_preview}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* FOOTER */}
        <footer className="dashboard-footer">
          <Shield size={14} /> Fraud Shield — AI-Powered Real-Time Cybersecurity System
        </footer>
      </div>

      {/* WHATSAPP TOAST */}
      {showWhatsAppToast && (
        <div className="whatsapp-toast">
          <CheckCircle size={16} /> WhatsApp alert dispatched
        </div>
      )}

      {/* CALL MODAL */}
      {showCallModal && (
        <div className="call-modal-overlay">
          <div className={`call-modal-card ${callState === "hungup" ? "scale-out" : ""}`}>
            {callState === "ringing" && (
              <div className="ringing-view fade-in">
                <div className="incoming-header">CRITICAL SYSTEM ALERT</div>
                <div className="phone-icon-container">
                  <PhoneCall size={36} />
                </div>
                <div className="caller-name">FRAUD SHIELD ADVISORY</div>
                <div className="caller-subtitle">Automated Security Call</div>
                <p className="ringing-caption">Ringing user at {registeredPhone}...</p>
                <div className="call-actions">
                  <button className="answer-btn" onClick={handleAnswerCall}>
                    <Phone size={16} /> Accept Warning Call
                  </button>
                  <button className="decline-btn" onClick={handleHangupCall}>
                    <PhoneOff size={16} /> Ignore Call
                  </button>
                </div>
              </div>
            )}

            {callState === "answered" && (
              <div className="answered-view fade-in">
                <div className="call-duration">
                  <span className="live-dot" /> VOICE BROADCAST ACTIVE
                </div>
                <div className="speaker-avatar">
                  <Volume2 size={28} />
                </div>
                <div className="broadcast-title">FRAUD SHIELD GUARD</div>

                <div className="transcript-box">
                  <span className="transcript-label">
                    <span className="pulse-dot" /> AUDIO TRANSCRIPT
                  </span>
                  <p className="transcript-text">
                    "Warning! We detected a highly dangerous scam attempt on your device. Please look at the dashboard alert now. Do not send OTPs, passwords, or payments to untrusted accounts. Fraud Shield has successfully logged the record for your security."
                  </p>
                </div>

                <button className="hangup-btn" onClick={handleHangupCall}>
                  <PhoneOff size={16} /> Disconnect Call
                </button>
              </div>
            )}

            {callState === "hungup" && (
              <div className="hungup-view fade-in">
                <div style={{ color: 'var(--color-text-muted)', marginBottom: '16px' }}>
                  <PhoneOff size={32} />
                </div>
                <h3 style={{ color: 'var(--color-text-primary)', marginBottom: '8px' }}>Call Discarded</h3>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>Alert event recorded in security logs.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default App;
