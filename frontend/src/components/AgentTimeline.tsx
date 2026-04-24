import { useMemo, useState } from "react";
import { Badge } from "./ui/badge";
import { cn, formatDuration } from "@/lib/utils";
import type { AgentStep, StreamEvent } from "@/lib/types";
import { ChevronDown, ChevronRight, Check, AlertCircle, Loader2 } from "lucide-react";

const NODE_LABELS: Record<string, string> = {
  diagnostic_agent: "Diagnostic Agent",
  knowledge_agent: "Knowledge Agent",
  remediation_agent: "Remediation Agent",
  escalate_node: "Escalation",
  finalize_success: "Finalize (remediated)",
  finalize_escalated: "Finalize (escalated)",
};

interface TimelineStep {
  step_index: number;
  node_name: string;
  status: string;
  reasoning: string | null;
  tokens_used: number;
  duration_ms: number;
  error: string | null;
}

function mergeEvents(persisted: AgentStep[], streamed: StreamEvent[]): TimelineStep[] {
  const bySidx = new Map<number, TimelineStep>();
  for (const s of persisted) {
    bySidx.set(s.step_index, {
      step_index: s.step_index,
      node_name: s.node_name,
      status: s.status,
      reasoning: s.reasoning,
      tokens_used: s.tokens_used,
      duration_ms: s.duration_ms,
      error: s.error,
    });
  }
  for (const e of streamed) {
    if (e.type !== "step" || e.step_index === undefined) continue;
    bySidx.set(e.step_index, {
      step_index: e.step_index,
      node_name: e.node_name ?? "unknown",
      status: e.status ?? "done",
      reasoning: e.reasoning ?? null,
      tokens_used: e.tokens_used ?? 0,
      duration_ms: e.duration_ms ?? 0,
      error: e.error ?? null,
    });
  }
  return Array.from(bySidx.values()).sort((a, b) => a.step_index - b.step_index);
}

export function AgentTimeline({
  persistedSteps,
  streamedEvents,
  isRunning,
}: {
  persistedSteps: AgentStep[];
  streamedEvents: StreamEvent[];
  isRunning: boolean;
}) {
  const steps = useMemo(
    () => mergeEvents(persistedSteps, streamedEvents),
    [persistedSteps, streamedEvents],
  );

  if (steps.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        {isRunning ? "Waiting for first agent step…" : "No steps recorded."}
      </div>
    );
  }

  return (
    <ol className="space-y-3">
      {steps.map((step) => (
        <TimelineItem key={step.step_index} step={step} />
      ))}
      {isRunning && (
        <li className="flex items-center gap-3 pl-10 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Waiting for next step…
        </li>
      )}
    </ol>
  );
}

function TimelineItem({ step }: { step: TimelineStep }) {
  const [open, setOpen] = useState(false);
  const label = NODE_LABELS[step.node_name] ?? step.node_name;
  const failed = step.status === "failed" || !!step.error;

  return (
    <li className="rounded-lg border border-border bg-card">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-accent/40 transition-colors rounded-lg"
      >
        <StatusIcon status={step.status} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium">{label}</span>
            <Badge variant={failed ? "destructive" : "secondary"}>{step.status}</Badge>
            {step.tokens_used > 0 && (
              <Badge variant="outline">{step.tokens_used} tokens</Badge>
            )}
            <span className="text-xs text-muted-foreground">
              {formatDuration(step.duration_ms)}
            </span>
          </div>
          {step.error && (
            <div className="text-xs text-destructive mt-1 truncate">{step.error}</div>
          )}
        </div>
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="border-t border-border p-4 space-y-3 text-sm">
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1">Reasoning</div>
            <pre
              className={cn(
                "whitespace-pre-wrap break-words rounded-md bg-muted p-3 text-xs font-mono",
                !step.reasoning && "italic text-muted-foreground",
              )}
            >
              {step.reasoning || "(no reasoning captured)"}
            </pre>
          </div>
        </div>
      )}
    </li>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "running") {
    return <Loader2 className="h-5 w-5 text-muted-foreground animate-spin" />;
  }
  if (status === "failed") {
    return <AlertCircle className="h-5 w-5 text-destructive" />;
  }
  return <Check className="h-5 w-5 text-severity-low" />;
}
