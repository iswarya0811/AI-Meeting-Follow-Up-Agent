import React from "react";
import ActionItemCard from "./ActionItemCard";

export default function AnalysisPanel({ results }) {
  if (!results) {
    return (
      <div className="analysis-panel empty-state">
        <h3>MEETING ANALYSIS</h3>
        <div className="empty-content">
          <p className="empty-title">No analysis yet</p>
          <p className="empty-desc">Paste a meeting transcript or email and click Analyze.</p>
        </div>
      </div>
    );
  }

  const { label, action_items, follow_up_required } = results;

  return (
    <div className="analysis-panel">
      <div className="analysis-header-row">
        <h3>MEETING ANALYSIS</h3>
        <span className="classification-tag">
          Classification: <strong className={label === "ACTION" ? "text-action" : "text-non-action"}>{label}</strong>
        </span>
      </div>

      {!follow_up_required || action_items.length === 0 ? (
        <div className="non-action-state animate-fade-in">
          <span className="success-icon">✓</span>
          <p>No follow-up action required.</p>
        </div>
      ) : (
        <div className="analysis-content">
          <div className="analysis-section-title">
            <span>ACTION ITEMS ({action_items.length})</span>
          </div>
          <div className="analysis-list">
            {action_items.map((item, idx) => (
              <ActionItemCard key={idx} item={item} index={idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
