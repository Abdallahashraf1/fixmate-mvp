// components/HeaderBar.tsx
"use client";

import React, { useState, useEffect, Fragment } from "react";
import { useChat } from "../context/ChatContext";
import { UserButton } from "@clerk/nextjs";
import { Menu } from "lucide-react";
import { Listbox, Transition } from "@headlessui/react";
import { ChevronDown } from "lucide-react";

const dropdownStyles = `relative inline-block text-left`;
const buttonStyles = `
  flex items-center gap-2 bg-white dark:bg-gray-800
  border border-gray-300 dark:border-gray-600 rounded-md
  px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200
  hover:border-gray-400 dark:hover:border-gray-500
  focus:outline-none focus:ring-2 focus:ring-blue-500
`;
const optionsStyles = `
  absolute mt-1 w-40 bg-white dark:bg-gray-800
  border border-gray-200 dark:border-gray-700
  rounded-md shadow-lg z-10
  divide-y divide-gray-100 dark:divide-gray-700
  focus:outline-none
`;

export default function HeaderBar() {
  const {
    showSidebar,
    toggleSidebar,
    make,
    setMake,
    model,
    setModel,
    role,
    setRole,
  } = useChat();

  const [makes, setMakes] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const roles = ["Car Specialist", "Car Owner"];

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/meta/makes`)
      .then((r) => r.json())
      .then(setMakes);
  }, []);

  useEffect(() => {
    if (!make) return setModels([]);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/meta/models?make=${make}`)
      .then((r) => r.json())
      .then(setModels);
  }, [make]);

  return (
    <header
      className={`
        sticky top-0 z-20 flex h-16 items-center bg-background border-b px-4
        transition-margin duration-300 ease-in-out
        ${showSidebar ? "ml-64" : "ml-0"}
      `}
    >
      {/* Left: hamburger only when closed, then dropdowns */}
      <div className="flex items-center gap-4 flex-1">
        {!showSidebar && (
          <button
            onClick={toggleSidebar}
            className="p-1 rounded hover:bg-muted/20"
            aria-label="Open sidebar"
          >
            <Menu size={20} />
          </button>
        )}

        {/* Make dropdown */}
        <Listbox value={make} onChange={setMake}>
          <div className={dropdownStyles}>
            <Listbox.Button className={buttonStyles}>
              <span className="capitalize">{make || "Make"}</span>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </Listbox.Button>
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className={optionsStyles}>
                {makes.map((mk) => (
                  <Listbox.Option
                    key={mk}
                    value={mk}
                    className={({ active }) =>
                      `cursor-pointer select-none p-2 ${
                        active
                          ? "bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100"
                          : "text-gray-700 dark:text-gray-200"
                      }`
                    }
                  >
                    {mk}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>

        {/* Model dropdown */}
        <Listbox value={model} onChange={setModel}>
          <div className={dropdownStyles}>
            <Listbox.Button className={buttonStyles}>
              <span className="capitalize">{model || "Model"}</span>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </Listbox.Button>
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className={optionsStyles}>
                {models.map((md) => (
                  <Listbox.Option
                    key={md}
                    value={md}
                    className={({ active }) =>
                      `cursor-pointer select-none p-2 ${
                        active
                          ? "bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100"
                          : "text-gray-700 dark:text-gray-200"
                      }`
                    }
                  >
                    {md}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>
      </div>

      {/* Right: role dropdown + user button */}
      <div className="flex items-center gap-4">
        <Listbox value={role} onChange={setRole}>
          <div className={dropdownStyles}>
            <Listbox.Button className={buttonStyles}>
              <span>{role}</span>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </Listbox.Button>
            <Transition
              as={Fragment}
              leave="transition ease-in duration-100"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Listbox.Options className={optionsStyles}>
                {roles.map((r) => (
                  <Listbox.Option
                    key={r}
                    value={r}
                    className={({ active }) =>
                      `cursor-pointer select-none p-2 ${
                        active
                          ? "bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100"
                          : "text-gray-700 dark:text-gray-200"
                      }`
                    }
                  >
                    {r}
                  </Listbox.Option>
                ))}
              </Listbox.Options>
            </Transition>
          </div>
        </Listbox>

        <UserButton />
      </div>
    </header>
  );
}
