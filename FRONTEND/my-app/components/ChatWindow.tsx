// components/ChatWindow.tsx
"use client";

import React, { useEffect, useRef } from "react";
import { useChat } from "../context/ChatContext";
import AssistantMessage from "./AssistantMessage";
import ChatInput from "./ChatInput";
import HeroSection from "./HeroSection";

export default function ChatWindow() {
  const { conversation, freshSession } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll into view at bottom each time messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  const isNew = freshSession && conversation.length === 0;

  return (
    <div className="flex flex-col flex-1 h-full">
      {/* Message pane + hero */}
      <div className="flex-1 space-y-6">
        {isNew && (
          <div className="mb-8">
            <HeroSection />
            <p className="text-center text-muted-foreground">
              Ask a question to get started...
            </p>
          </div>
        )}

        {conversation.map((m, i) =>
          m.role === "assistant" ? (
            <AssistantMessage key={i} msg={m} />
          ) : (
            <div key={i} className="text-right my-2">
              <div className="inline-block bg-[#DCF8C6] rounded-lg px-4 py-2">
                {m.content}
              </div>
            </div>
          )
        )}

        <div ref={bottomRef} />
      </div>

      {/* Chat input pinned at bottom */}
      <ChatInput />
    </div>
  );
}
