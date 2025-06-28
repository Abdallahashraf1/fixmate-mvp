// app/page.tsx
"use client";

import { useRouter } from "next/navigation";
import {
  SignedIn,
  SignedOut,
  useUser,
} from "@clerk/nextjs";
import { useEffect } from "react";

import HeroSection from "../components/hero-section";
import ContentSection from "../components/content-1";
import Features from "../components/features-2";
import Pricing from "../components/pricing";
import TeamSection from "../components/team";
import FooterSection from "../components/footer";

export default function Home() {
  const router = useRouter();
  const { isSignedIn } = useUser();

  // Redirect signed‐in users to /chat
  useEffect(() => {
    if (isSignedIn) {
      router.replace("/chat");
    }
  }, [isSignedIn, router]);

  return (
    <>
      <SignedIn>
        {/* signed in → redirect */}
        <div />
      </SignedIn>

      <SignedOut>
        {/* Landing page */}
        <HeroSection />
        <Features />
        <ContentSection />
        <Pricing />
        <TeamSection />
        <FooterSection />
      </SignedOut>
    </>
  );
}
