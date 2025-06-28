// components/team.tsx
"use client";

import React from "react";
import Image from "next/image";

const members = [
  {
    name: "Méschac Irung",
    role: "Creator",
    // local file in public/images/team/meschac.png
    avatar: "/images/team/meschac.png",
  },
  {
    name: "Théo Balick",
    role: "Frontend Dev",
    avatar: "/images/team/theo.png",
  },
  {
    name: "Glodie Lukose",
    role: "Frontend Dev",
    avatar: "/images/team/glodie.png",
  },
  {
    name: "Bernard Ngandu",
    role: "Backend Dev",
    avatar: "/images/team/bernard.png",
  },
];

export default function TeamSection() {
  return (
    <section id="team" className="py-12 md:py-32">
      <div className="mx-auto max-w-3xl px-8 lg:px-0">
        <h2 className="mb-8 text-4xl font-bold md:mb-16 lg:text-5xl">
          Our team
        </h2>

        {/* Leadership */}
        <div>
          <h3 className="mb-6 text-lg font-medium">Leadership</h3>
          <div className="grid grid-cols-2 gap-4 border-t py-6 md:grid-cols-4">
            {members.map((member, idx) => (
              <div key={idx} className="text-center">
                <div className="mx-auto w-20 h-20 rounded-full border p-0.5 shadow shadow-zinc-950/5 overflow-hidden">
                  <Image
                    src={member.avatar}
                    alt={member.name}
                    width={80}
                    height={80}
                    className="object-cover"
                  />
                </div>
                <span className="mt-2 block text-sm">{member.name}</span>
                <span className="text-muted-foreground block text-xs">
                  {member.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Engineering */}
        <div className="mt-6">
          <h3 className="mb-6 text-lg font-medium">Engineering</h3>
          <div className="grid grid-cols-2 gap-4 border-t py-6 md:grid-cols-4">
            {members.map((member, idx) => (
              <div key={idx} className="text-center">
                <div className="mx-auto w-20 h-20 rounded-full border p-0.5 shadow shadow-zinc-950/5 overflow-hidden">
                  <Image
                    src={member.avatar}
                    alt={member.name}
                    width={80}
                    height={80}
                    className="object-cover"
                  />
                </div>
                <span className="mt-2 block text-sm">{member.name}</span>
                <span className="text-muted-foreground block text-xs">
                  {member.role}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
