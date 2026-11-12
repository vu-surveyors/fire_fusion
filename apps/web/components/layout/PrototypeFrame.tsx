"use client";

import { useEffect, useRef } from "react";

type PrototypeScreen = "overview" | "map" | "calendar" | "cluster" | "validation" | "methods";

type PrototypeFrameProps = {
  screen: PrototypeScreen;
  clusterId?: string;
};

export function PrototypeFrame({ screen, clusterId }: PrototypeFrameProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const view = screen === "cluster" ? "records" : screen;
  const route = new URLSearchParams({ view });
  if (clusterId) route.set("cluster", clusterId);
  const hash = `#${route.toString()}`;

  useEffect(() => {
    if (iframeRef.current?.contentWindow) {
      try {
        if (iframeRef.current.contentWindow.location.hash !== hash) {
          iframeRef.current.contentWindow.location.hash = hash;
        }
      } catch {
        // cross-origin fallback
      }
    }
  }, [hash]);

  return (
    <iframe
      ref={iframeRef}
      className="prototype-frame"
      src={`/resources/FireFusion_Desktop_Prototype.html${hash}`}
      title="FireFusion sensor-harmonized wildfire intelligence"
      allow="clipboard-write"
    />
  );
}
