import React from "react";

export default function LoadingState({ message = "Analyzing text with AI models..." }) {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  );
}
