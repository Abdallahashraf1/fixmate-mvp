// components/header.tsx
"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SignInButton, SignUpButton } from "@clerk/nextjs";

const menuItems = [
  { name: "Features", href: "#features" },
  { name: "Solution", href: "#solution" },
  { name: "Pricing", href: "#pricing" },
  { name: "About", href: "#team" },
];

export const HeroHeader = () => {
  const [menuState, setMenuState] = React.useState(false);

  return (
    <header>
      <nav
        data-state={menuState && "active"}
        className="bg-background/50 fixed z-20 w-full border-b backdrop-blur-3xl"
      >
        <div className="mx-auto max-w-6xl px-6 transition-all duration-300">
          <div className="relative flex flex-wrap items-center justify-between gap-6 py-3 lg:gap-0 lg:py-4">
            {/* Left side: logo + mobile menu button */}
            <div className="flex w-full items-center justify-between gap-12 lg:w-auto">
              <Link href="#hero" aria-label="FixMate home">
                <Image
                  src="/images/logo.png"
                  alt="FixMate logo"
                  width={64}
                  height={64}
                  // Remove fixed height class so it uses the 64px you set above
                  className="w-auto"
                />
              </Link>

              <button
                onClick={() => setMenuState(!menuState)}
                aria-label={menuState ? "Close Menu" : "Open Menu"}
                className="relative z-20 -m-2.5 -mr-4 block cursor-pointer p-2.5 lg:hidden"
              >
                <Menu className="in-data-[state=active]:rotate-180 in-data-[state=active]:scale-0 in-data-[state=active]:opacity-0 m-auto size-6 duration-200" />
                <X className="in-data-[state=active]:rotate-0 in-data-[state=active]:scale-100 in-data-[state=active]:opacity-100 absolute inset-0 m-auto size-6 -rotate-180 scale-0 opacity-0 duration-200" />
              </button>

              <div className="hidden lg:block">
                <ul className="flex gap-8 text-sm">
                  {menuItems.map((item, idx) => (
                    <li key={idx}>
                      <Link
                        href={item.href}
                        className="text-muted-foreground hover:text-accent-foreground block duration-150"
                      >
                        {item.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Right side: auth buttons */}
            <div
              className={`bg-background ${
                menuState ? "block" : "hidden"
              } lg:block lg:bg-transparent w-full lg:w-auto lg:flex lg:items-center lg:justify-end space-y-4 lg:space-y-0 lg:space-x-4 p-6 lg:p-0 rounded-3xl lg:rounded-none shadow-lg lg:shadow-none`}
            >
              <SignInButton>
                <Button size="lg">Sign In</Button>
              </SignInButton>
              <SignUpButton>
                <Button size="lg" variant="ghost">
                  Sign Up
                </Button>
              </SignUpButton>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};
