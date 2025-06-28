"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { Message } from "../lib/types";
import ImageGallery from "./ImageGallery";

export default function AssistantMessage({ msg }: { msg: Message }) {
  return (
    <div className="mb-4">
      <div className="prose">
        <ReactMarkdown>{msg.content}</ReactMarkdown>
      </div>
      {msg.images?.length > 0 && <ImageGallery images={msg.images} />}
    </div>
);
}
