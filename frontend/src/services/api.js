const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Sends a text input (meeting transcript line or email) to the backend for analysis.
 */
export async function analyzeText(text) {
  if (!text || !text.trim()) {
    throw new Error("Input text cannot be empty.");
  }

  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      let errorMessage = "Backend server returned an error.";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (e) {
        errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Cannot connect to the backend server. Please verify it is running on port 8000.");
    }
    throw error;
  }
}

/**
 * Request backend to send follow-up email.
 */
export async function sendEmail(recipient, subject, body, simulationMode = true) {
  try {
    const response = await fetch(`${API_BASE_URL}/send-email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        recipient, 
        subject, 
        body, 
        simulation_mode: simulationMode 
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to send email.");
    }

    return data;
  } catch (error) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Cannot connect to backend server. Connection failed.");
    }
    throw error;
  }
}

/**
 * Request backend to send follow-up SMS.
 */
export async function sendSms(phone_number, message, simulationMode = true) {
  try {
    const response = await fetch(`${API_BASE_URL}/send-sms`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        phone_number, 
        message, 
        simulation_mode: simulationMode 
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to send SMS.");
    }

    return data;
  } catch (error) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Cannot connect to backend server. Connection failed.");
    }
    throw error;
  }
}

/**
 * Request backend to schedule follow-up email.
 */
export async function scheduleEmail(recipient, subject, body, sendAt, timezone = "Asia/Kolkata") {
  try {
    const response = await fetch(`${API_BASE_URL}/schedule-email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        recipient, 
        subject, 
        body, 
        send_at: sendAt,
        timezone
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to schedule email.");
    }

    return data;
  } catch (error) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Cannot connect to backend server. Connection failed.");
    }
    throw error;
  }
}

/**
 * Fetch stats (scheduled count and sent today count) from backend.
 */
export async function getStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/stats`);
    if (!response.ok) {
      throw new Error("Failed to fetch stats.");
    }
    return await response.json();
  } catch (error) {
    console.error("Stats fetch error:", error);
    return { scheduled_count: 0, sent_today_count: 0 };
  }
}
