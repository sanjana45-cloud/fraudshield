import React, { useState } from 'react';
import { ChevronDown, Loader2 } from 'lucide-react';
import './ExplainerButton.css';

const GEMINI_API_KEY = "AIzaSyDsuWHZru9U1mxEVVcw8By9-yPemnxML-Y";
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;

function ExplainerButton({ riskLevel, inputType, rawInput, userAlert }) {
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState(null);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    
    const prompt = `You are a digital safety assistant for first-time internet users in India.

A fraud detection system just flagged this as ${riskLevel} risk:
- Type: ${inputType}
- What was scanned: ${rawInput}
- Warning given: ${userAlert}

Explain this to the user in simple Hindi-English (Hinglish) mixed language.
Structure your response in exactly this format:

🔴 Kya hua? (What happened?)
[2 sentences — what this scam/threat is]

😨 Aapke saath kya ho sakta tha? (What could have happened?)
[2 sentences — what the scammer wanted to do]

✅ Abhi kya karein? (What to do right now?)
[3 bullet points — simple actions]

💡 Yaad rakhein (Remember this)
[1 line — memorable safety rule]

Keep it very simple. No technical words. Write like you are talking to someone's grandmother.`;

    try {
      const response = await fetch(GEMINI_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        })
      });

      if (!response.ok) {
        throw new Error("API call failed");
      }

      const data = await response.json();
      const text = data.candidates[0].content.parts[0].text;
      setExplanation(text);
    } catch (err) {
      console.error("Gemini API Error:", err);
      setError("Could not load explanation. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Only show button if risk is HIGH or MEDIUM
  if (riskLevel !== "HIGH" && riskLevel !== "MEDIUM" && riskLevel !== "MEDIUM-HIGH") {
    return null;
  }

  return (
    <div className="explainer-container">
      {!explanation && !loading && (
        <button className="explainer-btn fade-in" onClick={fetchExplanation}>
          <ChevronDown size={16} /> Explain This to Me
        </button>
      )}

      {loading && (
        <div className="explainer-loading fade-in">
          <Loader2 size={16} className="spinner-explainer" /> Explaining...
        </div>
      )}

      {error && <div className="explainer-error fade-in">⚠️ {error}</div>}

      {explanation && (
        <div className="explainer-card fade-in">
          <div className="explainer-content">
            {explanation.split('\n').map((line, i) => {
              if (line.trim() === "") return <br key={i} />;
              // Make headers slightly bold
              if (line.includes("Kya hua?") || line.includes("Aapke saath kya ho sakta tha?") || line.includes("Abhi kya karein?") || line.includes("Yaad rakhein")) {
                return <h4 key={i} className="explainer-header">{line}</h4>;
              }
              return <p key={i}>{line}</p>;
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default ExplainerButton;
