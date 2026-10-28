import React, { useState, useEffect } from "react";
import { sendEmail } from "../services/api";

export default function EmailPanel({ results, onOpenSchedule, onActionCompleted }) {
  // Recipient input states
  const [emailRecipient, setEmailRecipient] = useState("");
  // Editable message contents
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [simulationMode, setSimulationMode] = useState(false);

  // Operations feedback states
  const [isSending, setIsSending] = useState(false);
  const [sendSuccess, setSendSuccess] = useState(null);
  const [sendError, setSendError] = useState(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // Sync state whenever follow-up predictions update from parent
  useEffect(() => {
    if (results && results.follow_up) {
      setEmailSubject(results.follow_up.email.subject || "");
      setEmailBody(results.follow_up.email.body || "");
      setSendSuccess(null);
      setSendError(null);
      setCopySuccess(false);
    } else {
      setEmailSubject("");
      setEmailBody("");
      setSendSuccess(null);
      setSendError(null);
      setCopySuccess(false);
    }
  }, [results]);

  // Clipboard copy handler
  const handleCopy = async () => {
    try {
      const textToCopy = `Subject: ${emailSubject}\n\n${emailBody}`;
      await navigator.clipboard.writeText(textToCopy);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  // Send Email Handler
  const handleSendEmail = async (e) => {
    e.preventDefault();
    setSendError(null);
    setSendSuccess(null);

    // Validate email format
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRecipient.trim() || !emailRegex.test(emailRecipient.trim())) {
      setSendError("Please enter a valid email address.");
      return;
    }

    setIsSending(true);

    try {
      const response = await sendEmail(
        emailRecipient.trim(),
        emailSubject.trim(),
        emailBody.trim(),
        simulationMode
      );
      if (response.success) {
        if (simulationMode) {
          setSendSuccess(`✓ [SIMULATION] Email saved to received_emails.log for recipient ${emailRecipient}`);
        } else {
          setSendSuccess(`✓ Email sent successfully to ${emailRecipient}`);
        }
        if (onActionCompleted) onActionCompleted();
      } else {
        setSendError(response.message || "Email could not be sent.");
      }
    } catch (error) {
      setSendError("✕ Email could not be sent. Please check the email address and SMTP configuration.");
    } finally {
      setIsSending(false);
    }
  };

  const handleScheduleClick = () => {
    // Validate email address before opening scheduler modal
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRecipient.trim() || !emailRegex.test(emailRecipient.trim())) {
      setSendError("Please enter a valid recipient email before scheduling.");
      return;
    }
    setSendError(null);
    onOpenSchedule({
      recipient: emailRecipient,
      subject: emailSubject,
      body: emailBody
    });
  };

  if (!results) {
    return (
      <div className="email-panel empty-state">
        <h3>FOLLOW-UP EMAIL</h3>
        <p className="subtitle">Review and send the generated meeting follow-up.</p>
        <div className="empty-content">
          <p className="empty-desc">No analysis yet. Email preview will appear here.</p>
        </div>
      </div>
    );
  }

  if (!results.follow_up_required || !results.follow_up) {
    return (
      <div className="email-panel empty-state">
        <h3>FOLLOW-UP EMAIL</h3>
        <p className="subtitle">Review and send the generated meeting follow-up.</p>
        <div className="empty-content">
          <p className="empty-desc">✓ No follow-up email is required.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="email-panel">
      <div className="email-header-row">
        <div>
          <h3>FOLLOW-UP EMAIL</h3>
          <p className="subtitle">Review and send the generated meeting follow-up.</p>
        </div>
        <div className="simulation-toggle">
          <label>
            <input
              type="checkbox"
              checked={simulationMode}
              onChange={(e) => setSimulationMode(e.target.checked)}
              disabled={isSending}
            />
            <span>Simulation Mode</span>
          </label>
        </div>
      </div>

      {sendSuccess && (
        <div className="alert-box alert-success animate-fade-in">
          <span>{sendSuccess}</span>
        </div>
      )}

      {sendError && (
        <div className="alert-box alert-error animate-fade-in">
          <span>⚠️ {sendError}</span>
        </div>
      )}

      <form onSubmit={handleSendEmail} className="email-form">
        <div className="form-group">
          <label htmlFor="emailRecipient">Recipient Email</label>
          <input
            id="emailRecipient"
            type="email"
            value={emailRecipient}
            onChange={(e) => setEmailRecipient(e.target.value)}
            placeholder="e.g. team@company.com"
            required
            disabled={isSending}
          />
        </div>

        <div className="form-group">
          <label htmlFor="emailSubject">Subject</label>
          <input
            id="emailSubject"
            type="text"
            value={emailSubject}
            onChange={(e) => setEmailSubject(e.target.value)}
            placeholder="Subject line..."
            required
            disabled={isSending}
          />
        </div>

        <div className="form-group flex-fill">
          <label htmlFor="emailBody">Message</label>
          <textarea
            id="emailBody"
            value={emailBody}
            onChange={(e) => setEmailBody(e.target.value)}
            placeholder="Generated follow-up email body..."
            required
            disabled={isSending}
          />
        </div>

        <div className="email-actions-row">
          <button
            type="button"
            className="btn-secondary"
            onClick={handleCopy}
            disabled={isSending}
          >
            {copySuccess ? "✓ Copied!" : "📋 Copy Email"}
          </button>

          <div className="primary-actions">
            <button
              type="button"
              className="btn-schedule"
              onClick={handleScheduleClick}
              disabled={isSending}
            >
              📅 Schedule Reminder
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSending}
            >
              {isSending ? "Sending..." : "📧 Send Now"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
