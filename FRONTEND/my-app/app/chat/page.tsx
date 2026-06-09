// app/chat/page.tsx
"use client";

import Sidebar from "../../components/Sidebar";
import ChatWindow from "../../components/ChatWindow";
import { useChat } from "../../context/ChatContext";

export default function ChatPage() {
  const { showSidebar } = useChat();

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`
            fixed top-0 left-0 h-screen bg-card border-r border-border
            transition-all duration-300 ease-in-out overflow-hidden
            ${showSidebar ? "w-64" : "w-0"}
          `}
        >
          <Sidebar />
        </aside>

        {/* Main chat area */}
        <main
          className={`
            flex-1 transition-margin duration-300 ease-in-out
            ${showSidebar ? "ml-64" : "ml-0"}
            h-[calc(100vh-4rem)] overflow-y-auto
          `}
        >
          <div className="mx-auto w-full max-w-4xl p-4 flex flex-col h-full">
            <ChatWindow />
          </div>
        </main>
      </div>
    </div>
  );
}
