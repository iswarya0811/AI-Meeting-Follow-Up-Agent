import React, { useState, useEffect } from "react";
import MeetingInput from "./components/MeetingInput";
import AnalysisPanel from "./components/AnalysisPanel";
import EmailPanel from "./components/EmailPanel";
import ScheduleModal from "./components/ScheduleModal";
import StatusBar from "./components/StatusBar";
import { analyzeText, getStats } from "./services/api";

import "./styles/App.css";

function App() {
  const [inputText, setInputText] = useState("");
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Scheduling modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalEmailData, setModalEmailData] = useState(null);
  const [scheduleSuccessMsg, setScheduleSuccessMsg] = useState(null);

  // Statistics state
  const [stats, setStats] = useState({ scheduled_count: 0, sent_today_count: 0 });
  const [apiConnected, setApiConnected] = useState(true);

  // Fetch stats on mount and poll every 5 seconds
  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
      setApiConnected(true);
    } catch (err) {
      setApiConnected(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);
    setScheduleSuccessMsg(null);

    try {
      const data = await analyzeText(inputText);
      setResults(data);
    } catch (err) {
      setError(err.message || "An unexpected error occurred while analyzing the text.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setInputText("");
    setResults(null);
    setError(null);
    setIsLoading(false);
    setScheduleSuccessMsg(null);
  };

  const handleOpenSchedule = (emailData) => {
    setModalEmailData(emailData);
    setIsModalOpen(true);
  };

  const handleScheduleSuccess = (message) => {
    setScheduleSuccessMsg(`✓ ${message}`);
    fetchStats();
  };

  // Get the first available assignee deadline to prefill schedule date helper
  const getFirstDeadline = () => {
    if (results && results.action_items && results.action_items.length > 0) {
      // Find the first action item with a deadline that isn't 'Not Applicable'
      const itemWithDeadline = results.action_items.find(
        (item) => item.deadline && item.deadline !== "Not Applicable"
      );
      return itemWithDeadline ? itemWithDeadline.deadline : "";
    }
    return "";
  };

  return (
    <div className="app-container">
      {/* Compact Header */}
      <header className="app-header">
        <div className="header-left">
          <h1>AI Meeting Follow-Up Agent</h1>
          <p className="subtitle">Turn meeting conversations into actionable follow-ups.</p>
        </div>
        <div className="header-right">
          <span className="status-indicator">
            <span className="dot online"></span> System Online
          </span>
        </div>
      </header>

      {/* Main Two-Column Layout */}
      <main className="main-content-grid">
        {/* Left Column (55%) */}
        <div className="left-column">
          <div className="top-section">
            <MeetingInput
              text={inputText}
              setText={setInputText}
              onAnalyze={handleAnalyze}
              onClear={handleClear}
              isLoading={isLoading}
            />
          </div>

          <div className="bottom-section">
            {error && (
              <div className="error-alert animate-fade-in">
                <div className="error-icon">⚠️</div>
                <div className="error-details">
                  <h4>Analysis Failed</h4>
                  <p>{error}</p>
                </div>
              </div>
            )}
            
            {isLoading && (
              <div className="loading-card animate-fade-in">
                <div className="spinner"></div>
                <p>Analyzing meeting... Extracting action items...</p>
              </div>
            )}

            {!isLoading && <AnalysisPanel results={results} />}
          </div>
        </div>

        {/* Right Column (45%) */}
        <div className="right-column">
          {scheduleSuccessMsg && (
            <div className="alert-box alert-success animate-fade-in mb-3">
              <span>{scheduleSuccessMsg}</span>
            </div>
          )}
          <EmailPanel
            results={results}
            onOpenSchedule={handleOpenSchedule}
            onActionCompleted={fetchStats}
          />
        </div>
      </main>

      {/* Bottom Status Bar */}
      <StatusBar
        scheduledCount={stats.scheduled_count}
        sentTodayCount={stats.sent_today_count}
        isConnected={apiConnected}
      />

      {/* Schedule Modal Dialog */}
      <ScheduleModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        emailData={modalEmailData}
        deadlineText={getFirstDeadline()}
        onScheduleSuccess={handleScheduleSuccess}
      />
    </div>
  );
}

export default App;
