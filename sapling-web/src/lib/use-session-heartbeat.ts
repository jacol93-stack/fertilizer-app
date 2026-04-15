"use client";

import { useEffect, useRef } from "react";
import { api, API_URL } from "@/lib/api";

const HEARTBEAT_INTERVAL_MS = 60_000; // 60 seconds
const SESSION_KEY = "sapling_session_id";

export function getSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(SESSION_KEY);
}

export function setSessionId(id: string | null) {
  if (typeof window === "undefined") return;
  if (id) {
    sessionStorage.setItem(SESSION_KEY, id);
  } else {
    sessionStorage.removeItem(SESSION_KEY);
  }
}

/**
 * Start a new session by calling the API. Stores session_id in sessionStorage.
 */
export async function startSession(): Promise<string | null> {
  try {
    const result = await api.post<{ session_id: string }>("/api/sessions/start", {
      user_agent: navigator.userAgent,
    });
    if (result.session_id) {
      setSessionId(result.session_id);
      return result.session_id;
    }
  } catch (e) {
    console.warn("Failed to start session:", e);
  }
  return null;
}

/**
 * End the current session. Uses sendBeacon for reliability on page unload.
 */
export async function endSession() {
  const sessionId = getSessionId();
  if (!sessionId) return;

  try {
    await api.post("/api/sessions/end", { session_id: sessionId });
  } catch {
    // Best effort
  }
  setSessionId(null);
}

/**
 * End session via sendBeacon (for beforeunload). Fire-and-forget.
 */
function endSessionBeacon() {
  const sessionId = getSessionId();
  if (!sessionId) return;

  const url = `${API_URL}/api/sessions/end`;
  const body = JSON.stringify({ session_id: sessionId });

  // sendBeacon doesn't support custom headers, so we use a regular fetch with keepalive
  try {
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  } catch {
    // Fire and forget
  }
}

/**
 * Hook: sends heartbeat every 60s while the user has an active session.
 * Also registers beforeunload to end session on tab close.
 */
export function useSessionHeartbeat() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Start heartbeat interval
    intervalRef.current = setInterval(() => {
      const sessionId = getSessionId();
      if (!sessionId) return;

      api.post("/api/sessions/heartbeat", { session_id: sessionId }).catch(() => {});
    }, HEARTBEAT_INTERVAL_MS);

    // Register beforeunload for session end
    window.addEventListener("beforeunload", endSessionBeacon);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      window.removeEventListener("beforeunload", endSessionBeacon);
    };
  }, []);
}
