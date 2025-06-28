"use client";

import React, { useState } from "react";
import { useChat } from "../context/ChatContext";

export default function ChatInput() {
  const { sendMessage, make, model } = useChat();
  const [text, setText] = useState("");

  const disabled = !text.trim() || !make || !model;

  async function onSend() {
    if (disabled) return;
    await sendMessage(text.trim());
    setText("");
  }

  return (
    <div className="p-4 border-t flex gap-2">
      <input
        className="flex-1 px-3 py-2 border rounded"
        placeholder="Enter your vehicle query"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onSend()}
      />
      <button onClick={onSend} disabled={disabled} className="px-4 py-2 bg-primary text-white rounded disabled:opacity-50">
        ➤
      </button>
    </div>
);
}
