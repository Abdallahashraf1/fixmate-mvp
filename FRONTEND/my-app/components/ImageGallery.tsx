"use client";

import React, { useState } from "react";
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";

interface ImageData {
  id: string;
  data: string;
  page: number;
  source?: string;
}

export default function ImageGallery({ images }: { images: ImageData[] }) {
  const [index, setIndex] = useState(0);
  const [open, setOpen] = useState(false);

  const slides = images.map(img => ({
    src: `data:image/png;base64,${img.data}`,
    key: img.id,
    title: `Page ${img.page} ${img.source ?? ""}`,
  }));

  return (
    <>
      <h5>Relevant Diagrams:</h5>
      <div className="grid grid-cols-3 gap-2">
        {slides.map((s, i) => (
          <img
            key={s.key}
            src={s.src}
            alt={s.title}
            className="cursor-pointer rounded"
            onClick={() => { setIndex(i); setOpen(true); }}
          />
        ))}
      </div>
      {open && (
        <Lightbox
          slides={slides}
          open={open}
          index={index}
          close={() => setOpen(false)}
        />
      )}
    </>
);
}
