import Image from "next/image";

export default function ContentSection() {
  return (
    <section id="solution" className="py-16 md:py-32">
      <div className="mx-auto max-w-5xl space-y-8 px-6 md:space-y-16">
        <h2 className="relative z-10 max-w-xl text-4xl font-medium lg:text-5xl">
          Engineered for Every Car
        </h2>

        <div className="grid gap-6 sm:grid-cols-2 md:gap-12 lg:gap-24">
          {/* Illustration */}
          <div className="relative mb-6 sm:mb-0">
            <div className="bg-linear-to-b aspect-76/59 relative rounded-2xl from-zinc-300 to-transparent p-px dark:from-zinc-700">
              <Image
                src="/images/car-dashboard-light.png"
                className="rounded-[15px] shadow dark:hidden"
                alt="Car dashboard"
                width={1200}
                height={800}
              />
              <Image
                src="/images/car-dashboard-dark.png"
                className="hidden rounded-[15px] dark:block"
                alt="Car dashboard (dark)"
                width={1200}
                height={800}
              />
            </div>
          </div>

          {/* Text & testimonial */}
          <div className="relative space-y-4">
            <p className="text-muted-foreground">
              From brake checks to engine tune-ups, FixMate covers all major diagnostic workflows in one place.{" "}
              <span className="text-accent-foreground font-bold">
                No more guesswork.
              </span>
            </p>
            <p className="text-muted-foreground">
              Accurate guidance, safety alerts, and part-number lookups—24/7, at your fingertips.
            </p>

            <div className="pt-6">
              <blockquote className="border-l-4 pl-4">
                <p>
                  “FixMate saved me hours at the shop—instant diagnostics right on my phone!”
                </p>
                <div className="mt-6 space-y-3">
                  <cite className="block font-medium">Jane Smith, DIY Enthusiast</cite>
                </div>
              </blockquote>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
