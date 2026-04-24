import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertsTable } from "@/components/AlertsTable";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useAlerts, useSubmitAlert } from "@/hooks/useAlerts";

const SAMPLE_ALERTS = [
  {
    label: "Wi-Fi connectivity loss (low)",
    body: {
      device_id: "dev-wifi-sensor-014",
      alert_type: "connectivity_loss",
      severity_hint: "low" as const,
      payload: { last_seen: new Date().toISOString(), signal_strength: -85, ssid: "wh-iot" },
    },
  },
  {
    label: "Storage gateway offline (high)",
    body: {
      device_id: "dev-storage-gw-042",
      alert_type: "gateway_offline",
      severity_hint: "high" as const,
      payload: { site: "warehouse-3", downstream_sensors: 14, last_telemetry: new Date().toISOString() },
    },
  },
  {
    label: "Tamper alert (critical)",
    body: {
      device_id: "dev-asset-tracker-210",
      alert_type: "tamper_event",
      severity_hint: "critical" as const,
      payload: { flags: ["enclosure_opened"], location: "bay-7" },
    },
  },
  {
    label: "Battery drain (medium)",
    body: {
      device_id: "dev-temp-sensor-077",
      alert_type: "battery_drain",
      severity_hint: "medium" as const,
      payload: { battery_percent: 18, drain_rate_pct_per_hour: 2.1 },
    },
  },
];

export function Dashboard() {
  const alerts = useAlerts();
  const submit = useSubmitAlert();
  const [lastSubmitted, setLastSubmitted] = useState<string | null>(null);

  const onSubmit = async (sample: (typeof SAMPLE_ALERTS)[number]) => {
    const result = await submit.mutateAsync(sample.body);
    setLastSubmitted(result.alert_id);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Incoming alerts, routed through the multi-agent triage graph.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Submit a test alert</CardTitle>
          <CardDescription>
            Triggers the full pipeline: diagnostic → knowledge (RAG) → remediation or escalation.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {SAMPLE_ALERTS.map((s) => (
            <Button
              key={s.label}
              variant="outline"
              onClick={() => onSubmit(s)}
              disabled={submit.isPending}
            >
              {s.label}
            </Button>
          ))}
        </CardContent>
      </Card>

      {lastSubmitted && (
        <Alert variant="success">
          <AlertTitle>Alert submitted</AlertTitle>
          <AlertDescription>
            <a
              href={`/alerts/${lastSubmitted}`}
              className="underline"
            >
              Open the triage timeline →
            </a>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent alerts</CardTitle>
          <CardDescription>
            {alerts.data?.length ?? 0} alert{alerts.data?.length === 1 ? "" : "s"} — click a row to
            open its triage run.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.isLoading ? (
            <div className="text-sm text-muted-foreground">Loading…</div>
          ) : alerts.error ? (
            <Alert variant="destructive">
              <AlertTitle>Failed to load alerts</AlertTitle>
              <AlertDescription>{String(alerts.error)}</AlertDescription>
            </Alert>
          ) : (
            <AlertsTable alerts={alerts.data ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
