"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { Session, Message, ChatRequest } from "../lib/types";
import {
  fetchSessions,
  createSession,
  fetchHistory,
  streamChat,
} from "../lib/api";

interface ChatContextValue {
  sessions: Session[];
  current: Session | null;
  conversation: Message[];
  role: "Car Owner" | "Car Specialist";
  make: string;
  model: string;
  showSidebar: boolean;
  setRole: (r: "Car Owner" | "Car Specialist") => void;
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
  const [role, setRole] = useState<"Car Owner" | "Car Specialist">(
    "Car Specialist"
  );
  const [make, setMake] = useState<string>("");
  const [model, setModel] = useState<string>("");

  // NEW: sidebar visibility
  const [showSidebar, setShowSidebar] = useState<boolean>(true);
  const toggleSidebar = () => setShowSidebar((v) => !v);

  // reload sessions list
  const loadSessions = () => {
    if (!user_id) return;
    fetchSessions(user_id).then(setSessions).catch(console.error);
  };
  useEffect(loadSessions, [user_id]);

  async function selectSession(sess: Session) {
    setCurrent(sess);
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
      } catch (e) {
        console.error(e);
        return;
      }
    }

    setConversation((prev) => [
      ...prev,
      { role: "user", content: query },
      { role: "assistant", content: "" },
    ]);

    let buffer = "";
    const fallback =
      "I specialize in vehicle diagnostics 🚗. Please ask about components or repair steps.";

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
        buffer += delta;
        setConversation((prev) => {
          const c = [...prev];
          c[c.length - 1] = { role: "assistant", content: buffer };
          return c;
        });
      },
      async () => {
        if (buffer.trim() === fallback) {
          return;
        }
        try {
          const full = await fetchHistory(sess!.session_id, user_id);
          setConversation(full);
        } catch (e) {
          console.error(e);
        }
        loadSessions();
      },
      (err) => {
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
