"use client";

import { SendHorizontal } from "lucide-react";
import React, { useState } from "react";
import { useChat } from "../context/ChatContext";

export default function ChatInput() {
  const { sendMessage, make, model } = useChat();
  const [text, setText] = useState("");

  const missingVehicle = !make || !model;
  const disabled = !text.trim() || missingVehicle;
  const placeholder = missingVehicle
    ? "Select a make and model first"
    : "Ask about symptoms, parts, repair steps, or diagrams...";

  async function onSend() {
    if (disabled) return;
    await sendMessage(text.trim());
    setText("");
  }

  return (
    <div className="border-t border-border bg-background/95 px-4 py-4 backdrop-blur">
      <div className="mx-auto flex max-w-4xl items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm transition-colors focus-within:border-foreground/30 focus-within:ring-2 focus-within:ring-ring/20">
        <textarea
          className="max-h-36 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm leading-6 text-foreground outline-none placeholder:text-muted-foreground"
          placeholder={placeholder}
          value={text}
          rows={1}
          disabled={missingVehicle}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void onSend();
            }
          }}
        />
        <button
          type="button"
          onClick={onSend}
          disabled={disabled}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
          aria-label="Send message"
          title="Send message"
        >
          <SendHorizontal className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
