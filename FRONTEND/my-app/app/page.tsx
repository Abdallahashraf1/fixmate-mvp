// app/page.tsx
"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import ContentSection from "../components/content-1";
import Features from "../components/features-2";
import FooterSection from "../components/footer";
import HeroSection from "../components/hero-section";
import Pricing from "../components/pricing";
import TeamSection from "../components/team";

export default function Home() {
  const router = useRouter();
  const { isSignedIn } = useUser();

  useEffect(() => {
    if (isSignedIn) {
      router.replace("/chat");
    }
  }, [isSignedIn, router]);

  if (isSignedIn) {
    return null;
  }

  return (
    <>
      <HeroSection />
      <Features />
      <ContentSection />
      <Pricing />
      <TeamSection />
      <FooterSection />
    </>
  );
}
