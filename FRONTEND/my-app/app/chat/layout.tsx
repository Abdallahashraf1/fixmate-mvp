// app/chat/layout.tsx
import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/nextjs";
import ChatProvider from "../../context/ChatContext";
import HeaderBar from "../../components/HeaderBar";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SignedIn>
        <ChatProvider>
          <HeaderBar />
          {children}
        </ChatProvider>
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}
