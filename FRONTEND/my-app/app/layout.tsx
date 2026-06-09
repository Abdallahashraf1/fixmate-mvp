// app/layout.tsx
import { ClerkProvider, Show } from "@clerk/nextjs";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "FixMate",
  description: "Vehicle diagnostic AI assistant",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!}>
      <html lang="en">
        <body className="flex flex-col h-screen">
          <Show when="signed-out">
            <main className="flex-1">{children}</main>
          </Show>

          <Show when="signed-in">{children}</Show>
        </body>
      </html>
    </ClerkProvider>
  );
}
