// app/chat/layout.tsx
import { RedirectToSignIn, Show } from "@clerk/nextjs";
import type { ReactNode } from "react";
import ChatProvider from "../../context/ChatContext";
import HeaderBar from "../../components/HeaderBar";

export default function ChatLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Show when="signed-in">
        <ChatProvider>
          <HeaderBar />
          {children}
        </ChatProvider>
      </Show>
      <Show when="signed-out">
        <RedirectToSignIn />
      </Show>
    </>
  );
}
