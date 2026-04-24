import { useEffect, useRef, useState } from "react";
import { wsUrlForRun } from "@/lib/api";
import type { StreamEvent } from "@/lib/types";

interface UseRunStreamResult {
  events: StreamEvent[];
  status: "connecting" | "open" | "closed" | "error";
}

export function useRunStream(runId: string | undefined): UseRunStreamResult {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<UseRunStreamResult["status"]>("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!runId) return;
    setEvents([]);
    setStatus("connecting");

    const ws = new WebSocket(wsUrlForRun(runId));
    wsRef.current = ws;

    ws.onopen = () => setStatus("open");
    ws.onerror = () => setStatus("error");
    ws.onclose = () => setStatus("closed");

    ws.onmessage = (msg) => {
      try {
        const event: StreamEvent = JSON.parse(msg.data);
        if (event.type === "ping") return;
        setEvents((prev) => [...prev, event]);
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [runId]);

  return { events, status };
}
