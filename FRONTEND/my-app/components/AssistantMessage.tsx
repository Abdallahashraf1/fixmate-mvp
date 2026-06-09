"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { Message, SourceChunk } from "../lib/types";
import ImageGallery from "./ImageGallery";

function formatScore(value?: number | null) {
  return typeof value === "number" ? value.toFixed(4) : "n/a";
}

function rankLabel(source: SourceChunk) {
  const ranks = [];
  if (typeof source.dense_rank === "number") ranks.push(`Dense #${source.dense_rank}`);
  if (typeof source.bm25_rank === "number") ranks.push(`BM25 #${source.bm25_rank}`);
  return ranks.length ? ranks.join(" / ") : "Rank unavailable";
}

function SourcePopover({ sources }: { sources: SourceChunk[] }) {
  if (!sources.length) return null;

  return (
    <div
      className="w-[min(30rem,calc(100vw-2rem))] overflow-hidden rounded-lg border border-border bg-popover text-popover-foreground shadow-xl"
      role="tooltip"
    >
      <div className="border-b border-border bg-muted/30 px-3 py-2">
        <div className="text-[11px] font-semibold uppercase tracking-normal text-muted-foreground">
          Reference context
        </div>
      </div>
      <div className="max-h-72 overflow-y-auto p-2.5">
        <div className="space-y-2">
          {sources.map((source, index) => (
            <section
              key={`${source.chunk_id}-${index}`}
              className="rounded-md border border-border bg-background p-2.5"
            >
              <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground">
                <span className="max-w-48 truncate font-medium text-foreground">
                  {source.source || "Unknown PDF"}
                </span>
                <span>Page {source.page || "n/a"}</span>
                <span>RRF {formatScore(source.rrf_score)}</span>
                <span>{rankLabel(source)}</span>
              </div>
              <p className="max-h-36 overflow-y-auto whitespace-pre-wrap break-words rounded-sm bg-muted/20 p-2 text-xs leading-5 text-foreground/90">
                {source.text}
              </p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

function ReferenceTrigger({ sources }: { sources: SourceChunk[] }) {
  if (!sources.length) return null;

  return (
    <div className="group/reference relative mt-3 inline-block pb-2" tabIndex={0}>
      <button
        type="button"
        className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring/40"
      >
        Reference
      </button>
      <div className="absolute left-0 top-full z-30 hidden pt-1 group-hover/reference:block group-focus-within/reference:block">
        <SourcePopover sources={sources} />
      </div>
    </div>
  );
}

export default function AssistantMessage({ msg }: { msg: Message }) {
  const sources = msg.sources ?? [];

  return (
    <div className="mb-4">
      <div className="max-w-full">
        <div className="assistant-markdown prose max-w-none rounded-md px-1 py-1 focus:outline-none group-focus-within:ring-2 group-focus-within:ring-ring/40">
          {msg.isLoading && !msg.content ? (
            <div className="flex items-center gap-2 py-2 text-muted-foreground">
              <span className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:-0.2s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-current [animation-delay:-0.1s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-current" />
            </div>
          ) : (
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          )}
        </div>
        <ReferenceTrigger sources={sources} />
      </div>
      {(msg.images?.length ?? 0) > 0 && <ImageGallery images={msg.images ?? []} />}
    </div>
  );
}
