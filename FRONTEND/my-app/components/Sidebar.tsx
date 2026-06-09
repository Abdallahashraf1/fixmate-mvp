// components/Sidebar.tsx
"use client";

import Image from "next/image";
import { PlusCircle, X } from "lucide-react";
import { useChat } from "../context/ChatContext";

export default function Sidebar() {
  const { sessions, newSession, selectSession, current, toggleSidebar } =
    useChat();

  const cleanSummary = (summary: string) =>
    summary.trim().replace(/^["']+|["']+$/g, "");

  return (
    <div className="flex h-full flex-col overflow-hidden border-r border-border bg-card">
      <div className="flex h-16 items-center justify-between bg-card px-4">
        <div className="flex items-center gap-2">
          <Image src="/images/logo.svg" alt="FixMate" width={28} height={28} />
          <span className="text-lg font-semibold text-foreground">FixMate</span>
        </div>
        <button
          onClick={toggleSidebar}
          className="rounded p-1 hover:bg-muted/20"
          aria-label="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>

      <div className="mt-6 px-4">
        <button
          onClick={newSession}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
        >
          <PlusCircle className="h-5 w-5" />
          <span>New Chat</span>
        </button>
      </div>

      <hr className="mx-4 my-4 border-border" />

      <div className="flex-1 space-y-1 overflow-y-auto px-4 pb-4">
        {sessions
          .filter((s) => Boolean(s.summary?.trim()))
          .map((s) => {
            const full = cleanSummary(s.summary);
            const isActive = current?.session_id === s.session_id;

            return (
              <button
                key={s.session_id}
                onClick={() => selectSession(s)}
                className={`
                  block w-full truncate rounded-md px-2.5 py-1.5 text-left text-sm leading-5 transition-colors
                  ${
                    isActive
                      ? "bg-sky-100 font-medium text-sky-950"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }
                `}
                title={full}
              >
                {full}
              </button>
            );
          })}
      </div>
    </div>
  );
}
