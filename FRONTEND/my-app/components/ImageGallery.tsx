"use client";

import { ChevronLeft, ChevronRight, X } from "lucide-react";
import React, { useState } from "react";

interface ImageData {
  id: string;
  data: string;
  page: number;
  source?: string;
}

export default function ImageGallery({ images }: { images: ImageData[] }) {
  const [index, setIndex] = useState(0);
  const [open, setOpen] = useState(false);

  const slides = images.map((img) => ({
    src: `data:image/png;base64,${img.data}`,
    key: img.id,
    title: `Page ${img.page}${img.source ? ` - ${img.source}` : ""}`,
  }));

  const active = slides[index];
  const hasMultiple = slides.length > 1;

  const previous = () =>
    setIndex((current) => (current - 1 + slides.length) % slides.length);
  const next = () => setIndex((current) => (current + 1) % slides.length);

  return (
    <section className="mt-5 border-t border-border pt-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Relevant diagrams
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Retrieved from the manual pages used for this answer.
          </p>
        </div>
        <span className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">
          {images.length} {images.length === 1 ? "image" : "images"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {slides.map((slide, i) => (
          <button
            key={slide.key}
            type="button"
            className="overflow-hidden rounded-md border border-border bg-background text-left transition-opacity hover:opacity-80"
            onClick={() => {
              setIndex(i);
              setOpen(true);
            }}
          >
            <img
              src={slide.src}
              alt={slide.title}
              className="aspect-video w-full object-cover"
            />
          </button>
        ))}
      </div>

      {open && active && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-6">
          <div className="w-full max-w-4xl rounded-xl border border-border bg-background shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="min-w-0">
                <h4 className="truncate text-sm font-semibold text-foreground">
                  {active.title}
                </h4>
                <p className="text-xs text-muted-foreground">
                  {index + 1} of {slides.length}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Close image viewer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="relative flex min-h-[20rem] items-center justify-center bg-muted/20 p-4">
              {hasMultiple && (
                <button
                  type="button"
                  onClick={previous}
                  className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-background/90 p-2 text-foreground shadow hover:bg-background"
                  aria-label="Previous image"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
              )}

              <img
                src={active.src}
                alt={active.title}
                className="max-h-[60vh] max-w-full rounded-md object-contain"
              />

              {hasMultiple && (
                <button
                  type="button"
                  onClick={next}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-background/90 p-2 text-foreground shadow hover:bg-background"
                  aria-label="Next image"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              )}
            </div>

            {hasMultiple && (
              <div className="flex justify-center overflow-x-auto border-t border-border p-3">
                <div className="flex gap-2">
                {slides.map((slide, i) => (
                  <button
                    key={slide.key}
                    type="button"
                    onClick={() => setIndex(i)}
                    className={`h-16 w-24 shrink-0 overflow-hidden rounded-md border transition-colors ${
                      i === index
                        ? "border-sky-500 ring-2 ring-sky-500/25"
                        : "border-border hover:border-foreground/30"
                    }`}
                    aria-label={`Open image ${i + 1}`}
                  >
                    <img
                      src={slide.src}
                      alt={slide.title}
                      className="h-full w-full object-cover"
                    />
                  </button>
                ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
