import React, { useState, useEffect } from "react";
import { scheduleEmail } from "../services/api";

export default function ScheduleModal({ isOpen, onClose, emailData, deadlineText, timezoneFromBackend, onScheduleSuccess }) {
  const [recipient, setRecipient] = useState("");
  const [reminderType, setReminderType] = useState("deadline"); // 'deadline', '1day', '2days', 'custom'
  const [targetDate, setTargetDate] = useState(""); // YYYY-MM-DD
  const [targetTime, setTargetTime] = useState("09:00"); // HH:MM
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (timezoneFromBackend) {
      setTimezone(timezoneFromBackend);
    }
  }, [timezoneFromBackend, isOpen]);

  useEffect(() => {
    if (emailData) {
      setRecipient(emailData.recipient || "");
    }
  }, [emailData]);

  // Compute date based on reminderType and deadlineText
  useEffect(() => {
    if (!isOpen) return;

    const parseDeadline = (text) => {
      const now = new Date();
      if (!text) {
        // Fallback to tomorrow
        const tom = new Date();
        tom.setDate(now.getDate() + 1);
        return tom;
      }
      
      const lower = text.toLowerCase();
      if (lower.includes("tomorrow")) {
        const d = new Date();
        d.setDate(now.getDate() + 1);
        return d;
      }

      const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
      for (let i = 0; i < 7; i++) {
        if (lower.includes(days[i])) {
          const targetDay = i;
          const currentDay = now.getDay();
          let diff = targetDay - currentDay;
          if (diff <= 0) {
            diff += 7; // Next week's day
          }
          const d = new Date();
          d.setDate(now.getDate() + diff);
          return d;
        }
      }

      // Default to tomorrow
      const d = new Date();
      d.setDate(now.getDate() + 1);
      return d;
    };

    const baseDate = parseDeadline(deadlineText);

    let finalDate = new Date(baseDate);
    if (reminderType === "1day") {
      finalDate.setDate(baseDate.getDate() - 1);
    } else if (reminderType === "2days") {
      finalDate.setDate(baseDate.getDate() - 2);
    }

    // Format finalDate as YYYY-MM-DD
    const yyyy = finalDate.getFullYear();
    const mm = String(finalDate.getMonth() + 1).padStart(2, '0');
    const dd = String(finalDate.getDate()).padStart(2, '0');
    setTargetDate(`${yyyy}-${mm}-${dd}`);
  }, [reminderType, deadlineText, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Create sendAt ISO string in local timezone (or UTC if we append timezone offset)
      // Since timezone is Asia/Kolkata (+05:30), we can parse targetDate + targetTime as ISO
      // E.g. "2026-08-19T09:00:00"
      const sendAtString = `${targetDate}T${targetTime}:00`;
      
      // Let's create an actual Date object or send the ISO string.
      // To ensure correct parsing, we can convert it to ISO string format:
      // If we construct a Date object, the browser parses it locally.
      // Let's construct a date representation.
      // If the backend parses ISO fromisoformat, it's safer to just send the local ISO string
      // and let the backend treat it as target date/time, e.g. sendAtString.
      // Let's make sure it has the correct tz offset or is naive. If timezone is Asia/Kolkata,
      // it's GMT+5:30. Let's send it in ISO format: "2026-08-20T09:00:00+05:30"
      let tzOffset = "+05:30"; // Asia/Kolkata
      if (timezone !== "Asia/Kolkata") {
        // simple offset calculation or naive
        tzOffset = "";
      }
      const isoSendAt = `${sendAtString}${tzOffset}`;

      const response = await scheduleEmail(
        recipient,
        emailData.subject,
        emailData.body,
        isoSendAt,
        timezone
      );

      if (response.success) {
        onScheduleSuccess(response.message);
        onClose();
      } else {
        setError(response.message || "Failed to schedule email.");
      }
    } catch (err) {
      setError("✕ Reminder could not be scheduled.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content animate-slide-up">
        <div className="modal-header">
          <h3>Schedule Follow-Up</h3>
          <button type="button" className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="modalRecipient">Recipient:</label>
            <input
              id="modalRecipient"
              type="email"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label>Reminder:</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="reminderType"
                  value="deadline"
                  checked={reminderType === "deadline"}
                  onChange={() => setReminderType("deadline")}
                  disabled={isLoading}
                />
                <span>On deadline</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="reminderType"
                  value="1day"
                  checked={reminderType === "1day"}
                  onChange={() => setReminderType("1day")}
                  disabled={isLoading}
                />
                <span>1 day before</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="reminderType"
                  value="2days"
                  checked={reminderType === "2days"}
                  onChange={() => setReminderType("2days")}
                  disabled={isLoading}
                />
                <span>2 days before</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="reminderType"
                  value="custom"
                  checked={reminderType === "custom"}
                  onChange={() => setReminderType("custom")}
                  disabled={isLoading}
                />
                <span>Custom</span>
              </label>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group col-6">
              <label htmlFor="modalDate">Date:</label>
              <input
                id="modalDate"
                type="date"
                value={targetDate}
                onChange={(e) => {
                  setTargetDate(e.target.value);
                  setReminderType("custom");
                }}
                required
                disabled={isLoading}
              />
            </div>

            <div className="form-group col-6">
              <label htmlFor="modalTime">Time:</label>
              <input
                id="modalTime"
                type="time"
                value={targetTime}
                onChange={(e) => setTargetTime(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="modalTimezone">Timezone:</label>
            <select
              id="modalTimezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              disabled={isLoading}
            >
              <option value="Asia/Kolkata">Asia/Kolkata (GMT+5:30)</option>
              <option value="UTC">Coordinated Universal Time (UTC)</option>
            </select>
          </div>

          <div className="modal-preview-text">
            <span>Will be scheduled for: <strong>{targetDate}</strong> at <strong>{targetTime} ({timezone})</strong></span>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? "Scheduling..." : "Schedule Reminder"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
