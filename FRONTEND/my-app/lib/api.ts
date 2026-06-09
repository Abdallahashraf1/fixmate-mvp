// lib/api.ts

import { ChatRequest, ChatResponse, Session, Message } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL;

type ApiValidationError = {
  msg?: string;
};

type ApiErrorBody = {
  detail?: string | ApiValidationError[];
};

async function readErrorBody(res: Response): Promise<ApiErrorBody | null> {
  try {
    return (await res.json()) as ApiErrorBody;
  } catch {
    return null;
  }
}

function formatError(detail: ApiErrorBody["detail"], fallback: string): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join("; ") || fallback;
  }
  return fallback;
}

/**
 * Fetch list of sessions for a user
 */
export async function fetchSessions(user_id: string): Promise<Session[]> {
  // NOTE the trailing slash after "sessions/"
  const res = await fetch(
    `${BASE}/sessions/?user_id=${encodeURIComponent(user_id)}`
  );
  if (!res.ok) {
    const errJson = await readErrorBody(res);
    throw new Error(
      formatError(errJson?.detail, `Failed to load sessions (status ${res.status})`)
    );
  }
  return res.json();
}

/**
 * Create a new session
 */
export async function createSession(user_id: string): Promise<Session> {
  // already had trailing slash here
  const res = await fetch(`${BASE}/sessions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id }),
  });
  if (!res.ok) {
    const errJson = await readErrorBody(res);
    throw new Error(
      formatError(errJson?.detail, `Failed to create session (status ${res.status})`)
    );
  }
  return res.json();
}

/**
 * Fetch full chat history for a session
 */
export async function fetchHistory(
  session_id: string,
  user_id: string
): Promise<Message[]> {
  // history endpoint is /sessions/{id}/history — no trailing slash needed
  const res = await fetch(
    `${BASE}/sessions/${encodeURIComponent(
      session_id
    )}/history?user_id=${encodeURIComponent(user_id)}`
  );
  if (!res.ok) {
    const errJson = await readErrorBody(res);
    throw new Error(
      formatError(errJson?.detail, `Failed to load history (status ${res.status})`)
    );
  }
  return res.json();
}

/**
 * One‐shot (non‐streaming) chat
 */
export async function sendChat(
  req: ChatRequest
): Promise<ChatResponse & { session_id: string }> {
  const res = await fetch(`${BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const errJson = await readErrorBody(res);
    if (!errJson) {
      throw new Error(`Chat error (status ${res.status})`);
    }
    const message = formatError(
      errJson.detail,
      `Chat error (status ${res.status})`
    );
    throw new Error(message);
  }
  const data = await res.json();
  return { ...data, session_id: data.session_id || req.session_id! };
}

/**
 * Streaming chat
 */
export function streamChat(
  req: ChatRequest,
  onDelta: (delta: string) => void,
  onDone: () => void,
  onError: (err: unknown) => void
): void {
  fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
    .then(async (res) => {
      if (!res.ok) {
        const errJson = await readErrorBody(res);
        if (!errJson) {
          throw new Error(`Stream failed: ${res.status}`);
        }
        const msg = formatError(errJson.detail, `Stream failed: ${res.status}`);
        throw new Error(msg);
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder("utf-8");

      function read() {
        reader
          .read()
          .then(({ done, value }) => {
            if (done) {
              onDone();
              return;
            }
            const chunk = decoder.decode(value, { stream: true });
            onDelta(chunk);
            read();
          })
          .catch(onError);
      }

      read();
    })
    .catch(onError);
}
