// app/layout.tsx
import "./globals.css";
import { ClerkProvider, SignedIn, SignedOut, SignInButton, SignUpButton } from "@clerk/nextjs";

export const metadata = { title: "FixMate", description: "Vehicle diagnostic AI assistant" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY!}>
      <html lang="en">
        <body className="flex flex-col h-screen">
          <SignedOut>
            {/* simple wrapper for landing */}
            <main className="flex-1">{children}</main>
          </SignedOut>

          <SignedIn>
            {/* only the children of signed‐in routes get rendered here */}
            {children}
          </SignedIn>
        </body>
      </html>
    </ClerkProvider>
  );
}
