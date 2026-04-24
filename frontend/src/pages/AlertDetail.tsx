import { Link, useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { SeverityBadge } from "@/components/SeverityBadge";
import { AgentTimeline } from "@/components/AgentTimeline";
import { useAlert } from "@/hooks/useAlerts";
import { useRunsForAlert } from "@/hooks/useAgentRun";
import { useRunStream } from "@/hooks/useWebSocket";
import { formatDateTime } from "@/lib/utils";

export function AlertDetail() {
  const { alertId } = useParams<{ alertId: string }>();
  const alertQ = useAlert(alertId);
  const runsQ = useRunsForAlert(alertId);
  const run = runsQ.data?.[0];
  const stream = useRunStream(run?.id);

  if (alertQ.isLoading) return <div className="text-sm text-muted-foreground">Loading…</div>;
  if (alertQ.error || !alertQ.data) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Alert not found</AlertTitle>
        <AlertDescription>
          <Link to="/" className="underline">Back to dashboard</Link>
        </AlertDescription>
      </Alert>
    );
  }

  const alert = alertQ.data;
  const isRunning = run?.status === "running";

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="text-xs text-muted-foreground hover:text-foreground">
          ← Back to dashboard
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight mt-2">
          {alert.alert_type}
        </h1>
        <p className="text-sm text-muted-foreground">
          Device <code className="font-mono">{alert.device_id}</code> · received{" "}
          {formatDateTime(alert.created_at)}
        </p>
      </div>

      {run && (
        <OutcomeBanner
          status={run.status}
          outcome={run.outcome}
          summary={run.summary}
          streamStatus={stream.status}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Agent timeline</CardTitle>
            <CardDescription>
              Every node execution is audited.{" "}
              {isRunning ? "Streaming live via WebSocket." : "Replayed from audit log."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {run ? (
              <AgentTimeline
                persistedSteps={run.steps}
                streamedEvents={stream.events}
                isRunning={isRunning}
              />
            ) : (
              <div className="text-sm text-muted-foreground">No agent run yet.</div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Classification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <MetaRow label="Severity">
                <SeverityBadge severity={run?.severity ?? alert.severity_hint} />
              </MetaRow>
              <MetaRow label="Status">
                <Badge variant={run?.status === "completed" ? "secondary" : "outline"}>
                  {run?.status ?? "—"}
                </Badge>
              </MetaRow>
              <MetaRow label="Outcome">
                <Badge variant={run?.outcome === "remediated" ? "low" : "high"}>
                  {run?.outcome ?? "—"}
                </Badge>
              </MetaRow>
              <MetaRow label="Tokens">{run?.total_tokens ?? 0}</MetaRow>
              <MetaRow label="LLM calls">{run?.total_llm_calls ?? 0}</MetaRow>
            </CardContent>
          </Card>

          {run?.retrieved_runbooks && run.retrieved_runbooks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Retrieved runbooks</CardTitle>
                <CardDescription>Top RAG matches for this diagnosis.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {run.retrieved_runbooks.map((rb) => (
                  <Link
                    key={rb.slug}
                    to={`/runbooks`}
                    className="block rounded-md border border-border p-2 hover:bg-accent/40 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium">{rb.title}</span>
                      <Badge variant="outline">{rb.score}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      risk: {rb.risk_level}
                    </div>
                  </Link>
                ))}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Raw payload</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs font-mono bg-muted rounded-md p-3 overflow-auto">
                {JSON.stringify(alert.payload, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function MetaRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span>{children}</span>
    </div>
  );
}

function OutcomeBanner({
  status,
  outcome,
  summary,
  streamStatus,
}: {
  status: string;
  outcome: string | null;
  summary: string | null;
  streamStatus: string;
}) {
  if (status === "running") {
    return (
      <Alert>
        <AlertTitle>Triage in progress</AlertTitle>
        <AlertDescription>
          Live stream: <code className="font-mono">{streamStatus}</code>. New steps appear below as
          the graph executes.
        </AlertDescription>
      </Alert>
    );
  }
  if (outcome === "remediated") {
    return (
      <Alert variant="success">
        <AlertTitle>Auto-remediated</AlertTitle>
        <AlertDescription>{summary}</AlertDescription>
      </Alert>
    );
  }
  if (outcome === "escalated") {
    return (
      <Alert variant="warning">
        <AlertTitle>Escalated for human review</AlertTitle>
        <AlertDescription>{summary}</AlertDescription>
      </Alert>
    );
  }
  if (status === "failed") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Run failed</AlertTitle>
        <AlertDescription>{summary}</AlertDescription>
      </Alert>
    );
  }
  return null;
}
