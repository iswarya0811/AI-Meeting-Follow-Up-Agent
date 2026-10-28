import React from "react";

export default function PriorityBadge({ priority }) {
  const prio = (priority || "").toLowerCase().trim();
  
  let badgeClass = "badge-gray";
  let label = "NOT APPLICABLE";
  
  if (prio === "high") {
    badgeClass = "badge-danger";
    label = "🔴 HIGH";
  } else if (prio === "medium") {
    badgeClass = "badge-warning";
    label = "🟡 MEDIUM";
  } else if (prio === "low") {
    badgeClass = "badge-info";
    label = "🔵 LOW";
  }
  
  return (
    <span className={`priority-badge ${badgeClass}`}>
      {label}
    </span>
  );
}
