// components/features-2.tsx
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Zap, BookOpen, Image as ImageIcon } from "lucide-react";
import { ReactNode } from "react";

export default function Features() {
  return (
    <section id="features" className="py-16 md:py-32">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center">
          <h2 className="text-balance text-4xl font-semibold lg:text-5xl">
            Why FixMate?
          </h2>
          <p className="mt-4">
            Fast, reliable diagnostics for every make and model—no shop visit required.
          </p>
        </div>

        <div className="mx-auto mt-8 grid max-w-sm grid-cols-1 gap-6 md:max-w-full md:grid-cols-3 md:mt-16">
          {/* Instant Diagnostics */}
          <Card className="group border-0 shadow-none">
            <CardHeader className="pb-3 flex flex-col items-center">
              <CardDecorator>
                <Zap size={32} aria-hidden />
              </CardDecorator>
              <h3 className="mt-6 font-bold">Instant Diagnostics</h3>
            </CardHeader>
            <CardContent>
              <p className="mt-3 text-sm text-center">
                Get step-by-step troubleshooting with OEM torque specs, voltages, and part numbers.
              </p>
            </CardContent>
          </Card>

          {/* Context-Aware */}
          <Card className="group border-0 shadow-none">
            <CardHeader className="pb-3 flex flex-col items-center">
              <CardDecorator>
                <BookOpen size={32} aria-hidden />
              </CardDecorator>
              <h3 className="mt-6 font-bold">Context-Aware</h3>
            </CardHeader>
            <CardContent>
              <p className="mt-3 text-sm text-center">
                Leverages your vehicle’s own service manual content for pinpoint-accurate guidance.
              </p>
            </CardContent>
          </Card>

          {/* Figures & Diagrams */}
          <Card className="group border-0 shadow-none">
            <CardHeader className="pb-3 flex flex-col items-center">
              <CardDecorator>
                <ImageIcon size={32} aria-hidden />
              </CardDecorator>
              <h3 className="mt-6 font-bold">Figures & Diagrams</h3>
            </CardHeader>
            <CardContent>
              <p className="mt-3 text-sm text-center">
                Visual schematics and exploded-view diagrams help you locate parts and understand systems at a glance.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

const CardDecorator = ({ children }: { children: ReactNode }) => (
  <div className="relative mx-auto w-16 h-16 duration-200 [--color-border:color-mix(in_oklab,var(--color-zinc-950)10%,transparent)] group-hover:[--color-border:color-mix(in_oklab,var(--color-zinc-950)20%,transparent)] dark:[--color-border:color-mix(in_oklab,var(--color-white)15%,transparent)] dark:group-hover:bg-white/5 dark:group-hover:[--color-border:color-mix(in_oklab,var(--color-white)20%,transparent)]">
    <div
      aria-hidden
      className="absolute inset-0 bg-[linear-gradient(to_right,var(--color-border)_1px,transparent_1px),linear-gradient(to_bottom,var(--color-border)_1px,transparent_1px)] bg-[size:24px_24px]"
    />
    <div
      aria-hidden
      className="bg-radial to-background absolute inset-0 from-transparent to-75%"
    />
    <div className="absolute inset-0 m-auto flex w-12 h-12 items-center justify-center border-l border-t bg-white dark:bg-background">
      {children}
    </div>
  </div>
);
