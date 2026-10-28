import React from "react";
import PriorityBadge from "./PriorityBadge";

export default function ActionItemCard({ item, index }) {
  const { action_item, assignee, deadline, priority } = item;

  return (
    <div className="action-item-card animate-fade-in">
      <div className="card-top-row">
        <PriorityBadge priority={priority} />
        <span className="card-assignee">👤 {assignee}</span>
      </div>
      <div className="card-middle-row">
        <p className="card-action-text">{action_item}</p>
      </div>
      <div className="card-bottom-row">
        <span className="card-deadline">📅 {deadline}</span>
      </div>
    </div>
  );
}
