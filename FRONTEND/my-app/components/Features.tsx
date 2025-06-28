// components/Features.tsx
"use client";

import React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Zap, FileText, Image as ImageIcon } from "lucide-react";

const features = [
  {
    title: "Instant Diagnostics",
    description:
      "Get step‑by‑step troubleshooting with OEM torque specs, voltages, and part numbers.",
    icon: <Zap size={32} />,
  },
  {
    title: "Context‑Aware",
    description:
      "Leverages your vehicle’s own service‑manual content for pinpoint‑accurate guidance.",
    icon: <FileText size={32} />,
  },
  {
    title: "Figures & Diagrams",
    description:
      "Inline charts, wiring diagrams and exploded views right where you need them.",
    icon: <ImageIcon size={32} />,
  },
];

export default function Features() {
  return (
    <section id="features" className="py-16 md:py-32">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center">
          <h2 className="text-4xl font-semibold lg:text-5xl">Why FixMate?</h2>
          <p className="mt-4">
            Fast, reliable diagnostics for every make and model—no shop visit
            required.
          </p>
        </div>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {features.map((f, i) => (
            <Card key={i} className="group border-0 shadow-none text-center">
              <CardHeader className="flex justify-center pb-3">
                <div className="rounded-full bg-muted/10 p-4">
                  {f.icon}
                </div>
              </CardHeader>
              <CardContent>
                <h3 className="mt-4 font-bold">{f.title}</h3>
                <p className="mt-2 text-sm">{f.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
