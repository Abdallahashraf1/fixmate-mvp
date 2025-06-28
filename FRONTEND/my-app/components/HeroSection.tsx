// components/HeroSection.tsx
"use client";

import React from "react";
import { SignInButton, SignUpButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import HeaderBar from "./HeaderBar";
import { InfiniteSlider } from "@/components/ui/infinite-slider";
import { ProgressiveBlur } from "@/components/ui/progressive-blur";

export default function HeroSection() {
  return (
    <>
      <HeaderBar />

      <main id="hero" className="overflow-x-hidden">
        {/* Hero intro */}
        <section>
          <div className="pb-24 pt-12 md:pb-32 lg:pb-56 lg:pt-44">
            <div className="relative mx-auto flex max-w-6xl flex-col-reverse px-6 lg:flex-row lg:items-center">
              {/* Text */}
              <div className="mt-8 lg:mt-0 lg:w-1/2 text-center lg:text-left">
                <h1 className="text-balance text-5xl font-medium md:text-6xl xl:text-7xl">
                  Welcome to FixMate
                </h1>
                <p className="mt-6 text-pretty text-lg max-w-lg mx-auto lg:mx-0">
                  Your AI‑powered vehicle diagnostic assistant. Get instant
                  guidance on repairs, parts, and safety—right in your browser.
                </p>
                <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
                  <SignInButton>
                    <Button size="lg" className="px-6">
                      Try FixMate Now
                    </Button>
                  </SignInButton>
                  <SignUpButton>
                    <Button size="lg" variant="ghost" className="px-6">
                      Request a Demo
                    </Button>
                  </SignUpButton>
                </div>
              </div>

              {/* Hero image */}
              <div className="relative lg:w-1/2">
                <Image
                  src="/images/hero.jpg"
                  alt="Engine diagram"
                  width={1200}
                  height={800}
                  className="mx-auto h-56 w-full object-cover sm:h-96 lg:h-auto lg:w-auto"
                />
              </div>
            </div>
          </div>
        </section>

        {/* “Trusted by” slider */}
        <section className="bg-background pb-16 md:pb-32">
          <div className="group relative mx-auto max-w-6xl px-6">
            <div className="flex flex-col items-center md:flex-row">
              <div className="md:max-w-44 md:border-r md:pr-6 text-end mb-4 md:mb-0">
                <p className="text-sm">Trusted by top garages</p>
              </div>
              <div className="relative py-6 md:w-[calc(100%-11rem)]">
                <InfiniteSlider speedOnHover={20} speed={40} gap={112}>
                  {[
                    "/images/logos/toyota.svg",
                    "/images/logos/ford.svg",
                    "/images/logos/bmw.svg",
                    "/images/logos/mercedes.svg",
                    "/images/logos/audi.svg",
                  ].map((src, i) => (
                    <div key={i} className="flex">
                      <div className="mx-auto h-8 w-auto relative">
                        <Image
                          src={src}
                          alt="Brand logo"
                          fill
                          className="object-contain dark:invert"
                        />
                      </div>
                    </div>
                  ))}
                </InfiniteSlider>

                {/* fades */}
                <div className="bg-linear-to-r from-background absolute inset-y-0 left-0 w-20" />
                <div className="bg-linear-to-l from-background absolute inset-y-0 right-0 w-20" />
                <ProgressiveBlur
                  className="pointer-events-none absolute left-0 top-0 h-full w-20"
                  direction="left"
                  blurIntensity={1}
                />
                <ProgressiveBlur
                  className="pointer-events-none absolute right-0 top-0 h-full w-20"
                  direction="right"
                  blurIntensity={1}
                />
              </div>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
