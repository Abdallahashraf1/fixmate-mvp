"use client";

import { useUser } from "@clerk/nextjs";
import React, { createContext, useContext, useEffect, useState } from "react";
import { ChatRequest, Message, Session } from "../lib/types";
import {
  createSession,
  fetchHistory,
  fetchSessions,
  streamChat,
} from "../lib/api";

type ChatRole = "Car Owner" | "Car Specialist";

const STREAM_REVEAL_INTERVAL_MS = 14;
const STREAM_CHARS_PER_TICK = 4;

interface ChatContextValue {
  sessions: Session[];
  current: Session | null;
  conversation: Message[];
  role: ChatRole;
  make: string;
  model: string;
  freshSession: boolean;
  showSidebar: boolean;
  setRole: (r: ChatRole) => void;
  setMake: (m: string) => void;
  setModel: (m: string) => void;
  selectSession: (s: Session) => void;
  newSession: () => void;
  sendMessage: (query: string) => Promise<void>;
  toggleSidebar: () => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export default function ChatProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useUser();
  const user_id = user?.id || "";

  const [sessions, setSessions] = useState<Session[]>([]);
  const [current, setCurrent] = useState<Session | null>(null);
  const [conversation, setConversation] = useState<Message[]>([]);
  const [role, setRole] = useState<ChatRole>("Car Specialist");
  const [make, setMake] = useState<string>("");
  const [model, setModel] = useState<string>("");
  const [freshSession, setFreshSession] = useState<boolean>(true);
  const [showSidebar, setShowSidebar] = useState<boolean>(true);

  const toggleSidebar = () => setShowSidebar((v) => !v);

  const loadSessions = () => {
    if (!user_id) return;
    fetchSessions(user_id).then(setSessions).catch(console.error);
  };

  useEffect(loadSessions, [user_id]);

  async function selectSession(sess: Session) {
    setCurrent(sess);
    setFreshSession(false);
    try {
      const hist = await fetchHistory(sess.session_id, user_id);
      setConversation(hist);
    } catch (e) {
      console.error(e);
    }
    setRole("Car Specialist");
  }

  async function newSession() {
    if (!user_id) return;
    try {
      const sess = await createSession(user_id);
      setCurrent(sess);
      setConversation([]);
      setFreshSession(true);
      loadSessions();
    } catch (e) {
      console.error(e);
    }
  }

  async function sendMessage(query: string) {
    if (!user_id) return;

    let sess = current;
    if (!sess) {
      try {
        sess = await createSession(user_id);
        setCurrent(sess);
        setSessions((prev) => [sess!, ...prev]);
        setFreshSession(true);
      } catch (e) {
        console.error(e);
        return;
      }
    }

    setConversation((prev) => [
      ...prev,
      { role: "user", content: query },
      { role: "assistant", content: "", isLoading: true },
    ]);
    setFreshSession(false);

    let incomingBuffer = "";
    let displayedBuffer = "";
    let streamFinished = false;
    let finalHistory: Message[] | null = null;
    let sessionsReloaded = false;
    let revealTimer: ReturnType<typeof setInterval> | null = null;

    const updateAssistant = (message: Partial<Message>) => {
      setConversation((prev) => {
        const c = [...prev];
        const idx = c.length - 1;
        if (idx >= 0 && c[idx].role === "assistant") {
          c[idx] = { ...c[idx], ...message };
        }
        return c;
      });
    };

    const finishDisplay = () => {
      if (revealTimer) {
        clearInterval(revealTimer);
        revealTimer = null;
      }
      if (finalHistory?.length) {
        setConversation(finalHistory);
      } else {
        updateAssistant({ isLoading: false });
      }
      if (!sessionsReloaded) {
        sessionsReloaded = true;
        loadSessions();
      }
    };

    const maybeFinishDisplay = () => {
      if (streamFinished && displayedBuffer.length >= incomingBuffer.length) {
        finishDisplay();
      }
    };

    const ensureRevealTimer = () => {
      if (revealTimer) return;
      revealTimer = setInterval(() => {
        if (displayedBuffer.length < incomingBuffer.length) {
          const nextLength = Math.min(
            incomingBuffer.length,
            displayedBuffer.length + STREAM_CHARS_PER_TICK
          );
          displayedBuffer = incomingBuffer.slice(0, nextLength);
          updateAssistant({
            content: displayedBuffer,
            isLoading: displayedBuffer.length === 0,
          });
          maybeFinishDisplay();
          return;
        }

        if (streamFinished) {
          finishDisplay();
        }
      }, STREAM_REVEAL_INTERVAL_MS);
    };

    streamChat(
      {
        session_id: sess.session_id,
        user_id,
        role,
        make,
        model,
        query,
      } as ChatRequest,
      (delta) => {
        incomingBuffer += delta;
        ensureRevealTimer();
      },
      async () => {
        streamFinished = true;
        try {
          const full = await fetchHistory(sess!.session_id, user_id);
          if (full.length > 0) {
            finalHistory = full;
          }
        } catch (e) {
          console.error(e);
        }
        if (!incomingBuffer) {
          updateAssistant({ isLoading: false });
        }
        maybeFinishDisplay();
      },
      (err) => {
        streamFinished = true;
        if (!incomingBuffer) {
          updateAssistant({ isLoading: false });
        }
        maybeFinishDisplay();
        console.error("Stream error:", err);
      }
    );
  }

  return (
    <ChatContext.Provider
      value={{
        sessions,
        current,
        conversation,
        role,
        make,
        model,
        showSidebar,
        freshSession,
        setRole,
        setMake,
        setModel,
        selectSession,
        newSession,
        sendMessage,
        toggleSidebar,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be inside ChatProvider");
  return ctx;
}
