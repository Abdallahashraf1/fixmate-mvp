"use client";

import React from "react";
import { SignInButton, SignUpButton } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { HeroHeader } from "./header";
import { InfiniteSlider } from "@/components/ui/infinite-slider";
import { ProgressiveBlur } from "@/components/ui/progressive-blur";

export default function HeroSection() {
  const brands = [
    "/images/logos/toyota.svg",
    "/images/logos/ford.svg",
    "/images/logos/bmw.svg",
    "/images/logos/mercedes.svg",
    "/images/logos/audi.svg",
  ];

  return (
    <>
      <HeroHeader />

      <main id="#" className="overflow-x-hidden">
        {/* Hero intro */}
        <section>
          <div className="pb-24 pt-12 md:pb-32 lg:pb-56 lg:pt-44">
            <div className="relative mx-auto flex max-w-6xl flex-col px-6 lg:flex-row lg:items-center">
              <div className="mx-auto max-w-lg text-center lg:ml-0 lg:w-1/2 lg:text-left">
                <h1 className="mt-8 max-w-2xl text-balance text-5xl font-medium md:text-6xl lg:mt-16 xl:text-7xl">
                  Welcome to FixMate
                </h1>
                <p className="mt-8 max-w-2xl text-pretty text-lg">
                  Your AI-powered vehicle diagnostic assistant. Get instant
                  guidance on repairs, parts, and safety—right in your browser.
                </p>

                <div className="mt-12 flex flex-col items-center justify-center gap-2 sm:flex-row lg:justify-start">
                  <SignInButton>
                    <Button size="lg" className="px-5 text-base">
                      Try FixMate Now
                    </Button>
                  </SignInButton>
                  <SignUpButton>
                    <Button
                      size="lg"
                      variant="ghost"
                      className="px-5 text-base"
                    >
                      Request a Demo
                    </Button>
                  </SignUpButton>
                </div>
              </div>

              {/* Vertically-centered hero image */}
              <div className="relative mt-8 lg:mt-0 lg:w-1/2">
                <Image
                  src="/images/hero.jpg"
                  alt="Engine diagram"
                  width={1200}
                  height={800}
                  className="w-full object-cover lg:absolute lg:top-1/2 lg:-translate-y-1/2 lg:right-0 lg:h-auto"
                />
              </div>
            </div>
          </div>
        </section>

        {/* “Trusted by” slider */}
        <section className="bg-background pb-16 md:pb-32">
          <div className="group relative mx-auto max-w-6xl px-6">
            <div className="flex flex-col items-center md:flex-row">
              <div className="md:max-w-44 md:border-r md:pr-6">
                <p className="text-end text-sm">Trusted by top garages</p>
              </div>
              <div className="relative py-6 md:w-[calc(100%-11rem)]">
                <InfiniteSlider speedOnHover={20} speed={40} gap={112}>
                  {brands.map((src, i) => (
                    <div key={i} className="flex">
                      <Image
                        src={src}
                        alt="Brand logo"
                        width={80}
                        height={40}
                        className="mx-auto dark:invert"
                      />
                    </div>
                  ))}
                </InfiniteSlider>

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
