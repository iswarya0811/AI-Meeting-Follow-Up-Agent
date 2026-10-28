import React from "react";

export default function StatusBar({ scheduledCount, sentTodayCount, isConnected }) {
  return (
    <footer className="status-bar animate-fade-in">
      <div className="status-group">
        <span className="status-item">
          ML <span className="status-dot online">●</span> Online
        </span>
        <span className="status-item">
          API <span className={`status-dot ${isConnected ? "online" : "offline"}`}>●</span> {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
      <div className="status-group">
        <span className="status-counter">Scheduled: <strong>{scheduledCount}</strong></span>
        <span className="status-counter">Sent Today: <strong>{sentTodayCount}</strong></span>
      </div>
    </footer>
  );
}
