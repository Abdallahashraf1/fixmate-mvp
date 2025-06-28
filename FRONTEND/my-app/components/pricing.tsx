import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Check } from "lucide-react";

export default function Pricing() {
  return (
    <section id="pricing" className="py-16 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-2xl space-y-6 text-center">
          <h1 className="text-4xl font-semibold lg:text-5xl">
            Simple, Transparent Pricing
          </h1>
          <p>All plans include unlimited diagnostic queries.</p>
        </div>

        <div className="mt-8 grid gap-6 md:mt-20 md:grid-cols-3">
          {/* Free */}
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle className="font-medium">Free</CardTitle>
              <span className="my-3 block text-2xl font-semibold">$0 / mo</span>
              <CardDescription className="text-sm">Up to 10 queries / day</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <hr className="border-dashed" />
              <ul className="space-y-3 text-sm">
                {["Basic diagnostics", "Service-manual context", "Community support"].map(
                  (item, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <Check className="size-3" />
                      {item}
                    </li>
                  )
                )}
              </ul>
            </CardContent>
            <CardFooter className="mt-auto">
              <Button asChild variant="outline" className="w-full">
                <Link href="#hero">Get Started</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Pro */}
          <Card className="relative flex flex-col">
            <span className="absolute inset-x-0 -top-3 mx-auto inline-flex h-6 w-fit items-center rounded-full bg-purple-400 px-3 py-1 text-xs font-medium text-purple-900">
              Popular
            </span>
            <CardHeader>
              <CardTitle className="font-medium">Pro</CardTitle>
              <span className="my-3 block text-2xl font-semibold">$19 / mo</span>
              <CardDescription className="text-sm">Unlimited queries + images</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <hr className="border-dashed" />
              <ul className="space-y-3 text-sm">
                {[
                  "Unlimited diagnostics",
                  "Image-based fault detection",
                  "Priority support",
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <Check className="size-3" />
                    {item}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button asChild className="w-full">
                <Link href="#hero">Get Started</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Enterprise */}
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle className="font-medium">Enterprise</CardTitle>
              <span className="my-3 block text-2xl font-semibold">$49 / mo</span>
              <CardDescription className="text-sm">For teams</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <hr className="border-dashed" />
              <ul className="space-y-3 text-sm">
                {[
                  "Everything in Pro",
                  "Custom SLA & onboarding",
                  "Team collaboration",
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <Check className="size-3" />
                    {item}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter className="mt-auto">
              <Button asChild variant="outline" className="w-full">
                <Link href="#hero">Contact Sales</Link>
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </section>
);
}
