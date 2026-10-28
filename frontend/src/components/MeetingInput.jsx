import React, { useState } from "react";

export default function MeetingInput({ text, setText, onAnalyze, onClear, isLoading }) {
  const [activeTab, setActiveTab] = useState("transcript");

  const samples = {
    transcript: {
      action: "Priya: Rahul, please fix the mobile login issues and test the login flow by Thursday.\nPriya: Ananya, please update the API error handling and add proper validation for invalid requests. Please complete it by Wednesday.",
      nonAction: "We discussed the new dashboard design but no specific tasks were assigned during the call."
    },
    email: {
      action: "Hi Sneha, could you please prepare the presentation slides by Monday for the weekly review? We need it ready beforehand.",
      nonAction: "Hello all, the product requirements were reviewed during the meeting yesterday. Thanks!"
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    onClear();
  };

  const handleSampleClick = (type) => {
    setText(samples[activeTab][type]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onAnalyze();
  };

  return (
    <div className="meeting-input-card">
      <div className="input-header-row">
        <h3>MEETING INPUT</h3>
        <div className="tabs">
          <button
            type="button"
            className={`tab-btn ${activeTab === "transcript" ? "active" : ""}`}
            onClick={() => handleTabChange("transcript")}
            disabled={isLoading}
          >
            💬 Meeting Transcript
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === "email" ? "active" : ""}`}
            onClick={() => handleTabChange("email")}
            disabled={isLoading}
          >
            ✉️ Email
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your meeting transcript or email here..."
          disabled={isLoading}
          required
        />

        <div className="actions-bar">
          <div className="sample-triggers">
            <span className="sample-label">Try a sample:</span>
            <button
              type="button"
              className="sample-btn"
              onClick={() => handleSampleClick("action")}
              disabled={isLoading}
            >
              Action Item
            </button>
            <button
              type="button"
              className="sample-btn"
              onClick={() => handleSampleClick("nonAction")}
              disabled={isLoading}
            >
              Non-Action
            </button>
          </div>

          <div className="button-group">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClear}
              disabled={isLoading || !text}
            >
              Clear
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || !text.trim()}
            >
              {isLoading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
