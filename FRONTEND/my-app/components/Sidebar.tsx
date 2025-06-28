// components/Sidebar.tsx
"use client";

import React from "react";
import Image from "next/image";
import { useChat } from "../context/ChatContext";
import { PlusCircle, X } from "lucide-react";

export default function Sidebar() {
  const { sessions, newSession, selectSession, current, toggleSidebar } =
    useChat();
  const PREVIEW_LENGTH = 25;

  return (
    <div className="h-full flex flex-col bg-card border-r border-border overflow-hidden">
      {/* Mini-header: logo.png + title + close */}
      <div className="flex h-16 items-center justify-between px-4 bg-card">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="FixMate" width={24} height={24} />
          <span className="text-lg font-semibold text-foreground">
            FixMate
          </span>
        </div>
        <button
          onClick={toggleSidebar}
          className="p-1 rounded hover:bg-muted/20"
          aria-label="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>

      {/* New Chat: add extra top margin so it sits lower */}
      <div className="px-4 mt-6">
        <button
          onClick={newSession}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 transition-colors"
        >
          <PlusCircle className="h-5 w-5" />
          <span>New Chat</span>
        </button>
      </div>

      <hr className="border-border mx-4 my-4" />

      {/* History list */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1">
        {sessions
          .filter((s) => s.summary?.trim().length! > 0)
          .map((s) => {
            const full = s.summary!.trim();
            const preview =
              full.length > PREVIEW_LENGTH
                ? full.slice(0, PREVIEW_LENGTH) + "…"
                : full;
            const isActive = current?.session_id === s.session_id;
            return (
              <button
                key={s.session_id}
                onClick={() => selectSession(s)}
                className={`
                  w-full text-left px-3 py-2 rounded-lg transition-colors
                  ${isActive
                    ? "bg-gray-200 font-semibold"
                    : "hover:bg-gray-100"}
                `}
                title={full}
              >
                {preview}
              </button>
            );
          })}
      </div>
    </div>
  );
}
