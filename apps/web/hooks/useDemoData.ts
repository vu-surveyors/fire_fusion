"use client";

import { useCallback, useEffect, useState } from "react";
import type { DemoData, DemoEnvelope, DemoProvenance } from "@/types/demo";

export type DemoDataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; response: DemoEnvelope };

let demoDataRequest: Promise<DemoEnvelope> | undefined;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function loadDemoData(): Promise<DemoEnvelope> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
  let payload: unknown = null;

  // Attempt live API fetch first
  try {
    const apiRes = await fetch(`${apiUrl}/bundle`, { cache: "no-store" });
    if (apiRes.ok) {
      payload = await apiRes.json();
    }
  } catch {
    // API server not reachable, fallback to static harmonized data
  }

  // Fallback to static harmonized bundle
  if (!payload) {
    const response = await fetch("/resources/data/demo.json");
    if (!response.ok) {
      throw new Error(`Demo data request failed (${response.status}).`);
    }
    payload = await response.json();
  }
  if (
    !isRecord(payload) ||
    payload.status !== "ok" ||
    payload.error !== null ||
    !isRecord(payload.data) ||
    !isRecord(payload.data.cells) ||
    !Array.isArray(payload.data.cells.raw) ||
    !Array.isArray(payload.data.cells.harmonised) ||
    !isRecord(payload.data.calendar) ||
    !Array.isArray(payload.data.calendar.raw) ||
    !Array.isArray(payload.data.calendar.harmonised) ||
    !isRecord(payload.data.clusters) ||
    !isRecord(payload.provenance) ||
    !Array.isArray(payload.provenance.datasets) ||
    !isRecord(payload.provenance.parameters) ||
    typeof payload.provenance.run_id !== "string" ||
    typeof payload.provenance.git_sha !== "string"
  ) {
    throw new Error("Demo data response has an invalid envelope.");
  }

  return {
    status: "ok",
    data: payload.data as DemoData,
    error: null,
    provenance: payload.provenance as DemoProvenance,
  };
}

function getDemoData() {
  if (!demoDataRequest) {
    const request = loadDemoData().catch((error: unknown) => {
      if (demoDataRequest === request) demoDataRequest = undefined;
      throw error;
    });
    demoDataRequest = request;
  }

  return demoDataRequest;
}

export function useDemoData() {
  const [state, setState] = useState<DemoDataState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => {
    demoDataRequest = undefined;
    setAttempt((current) => current + 1);
  }, []);

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });

    void getDemoData()
      .then((response) => {
        if (active) setState({ status: "success", response });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Could not load demo data.",
        });
      });

    return () => {
      active = false;
    };
  }, [attempt]);

  return { ...state, retry };
}
