"use client";

import Image from "next/image";

export default function HeroSection() {
  return (
    <section className="flex min-h-[calc(100vh-12rem)] items-center justify-center px-6 py-12">
      <div className="grid w-full max-w-5xl items-center gap-10 lg:grid-cols-[1fr_420px]">
        <div>
          <h1 className="max-w-xl text-5xl font-semibold leading-tight text-foreground md:text-6xl">
            Welcome to FixMate
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-muted-foreground">
            Select a make and model, then ask a repair or diagnostic question.
          </p>
        </div>

        <div className="relative hidden aspect-[4/3] lg:block">
          <Image
            src="/images/hero.svg"
            alt="Vehicle diagnostic illustration"
            fill
            priority
            className="object-contain"
          />
        </div>
      </div>
    </section>
  );
}
