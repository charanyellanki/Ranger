import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select } from "./ui/select";
import {
  useActivateProvider,
  useDeleteProvider,
  useTestProvider,
  useUpsertProvider,
} from "@/hooks/useProviders";
import type { ProviderCatalogEntry, ProviderStatus } from "@/lib/types";

interface Props {
  def: ProviderCatalogEntry;
  status: ProviderStatus | undefined;
}

export function ProviderConfigCard({ def, status }: Props) {
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState(status?.base_url ?? "");
  const [model, setModel] = useState(status?.active_model ?? def.models[0] ?? "");
  const [testMessage, setTestMessage] = useState<{
    ok: boolean;
    text: string;
  } | null>(null);

  const upsert = useUpsertProvider();
  const del = useDeleteProvider();
  const test = useTestProvider();
  const activate = useActivateProvider();

  const onSave = async () => {
    await upsert.mutateAsync({
      name: def.name,
      body: {
        api_key: apiKey || undefined,
        base_url: def.needs_base_url ? baseUrl || undefined : undefined,
        active_model: model || undefined,
      },
    });
    setApiKey("");
  };

  const onTest = async () => {
    setTestMessage(null);
    const res = await test.mutateAsync({
      name: def.name,
      model,
      api_key: apiKey || undefined,
      base_url: def.needs_base_url ? baseUrl || undefined : undefined,
    });
    setTestMessage({
      ok: res.success,
      text: res.success
        ? `OK — ${res.message} (${res.latency_ms}ms)`
        : res.message,
    });
  };

  const onActivate = async () => {
    await activate.mutateAsync({ name: def.name, model });
  };

  const onDelete = async () => {
    if (!confirm(`Remove saved credentials for ${def.label}?`)) return;
    await del.mutateAsync(def.name);
    setApiKey("");
    setBaseUrl("");
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{def.label}</CardTitle>
          <div className="flex items-center gap-2">
            {status?.is_active && <Badge variant="low">active</Badge>}
            {status?.configured && !status.is_active && (
              <Badge variant="secondary">configured</Badge>
            )}
            {!status?.configured && <Badge variant="outline">not configured</Badge>}
          </div>
        </div>
        <CardDescription>
          {def.needs_api_key ? "Requires API key. " : ""}
          {def.needs_base_url ? "Requires base URL (Ollama host). " : ""}
          {status?.api_key_last4 && (
            <>Stored key ends in <code className="font-mono">•••{status.api_key_last4}</code>.</>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {def.needs_api_key && (
          <div className="space-y-1">
            <Label htmlFor={`${def.name}-key`}>API key</Label>
            <Input
              id={`${def.name}-key`}
              type="password"
              placeholder={status?.configured ? "•••• enter a new key to rotate" : "sk-…"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
        )}

        {def.needs_base_url && (
          <div className="space-y-1">
            <Label htmlFor={`${def.name}-url`}>Base URL</Label>
            <Input
              id={`${def.name}-url`}
              placeholder="http://host.docker.internal:11434"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>
        )}

        <div className="space-y-1">
          <Label htmlFor={`${def.name}-model`}>Model</Label>
          <Select
            id={`${def.name}-model`}
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            {def.models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
        </div>

        {testMessage && (
          <div
            className={`rounded-md border p-2 text-xs ${
              testMessage.ok
                ? "border-severity-low/40 text-severity-low"
                : "border-destructive/40 text-destructive"
            }`}
          >
            {testMessage.text}
          </div>
        )}

        <div className="flex flex-wrap gap-2 pt-2">
          <Button onClick={onSave} disabled={upsert.isPending}>
            {upsert.isPending ? "Saving…" : "Save"}
          </Button>
          <Button variant="outline" onClick={onTest} disabled={test.isPending}>
            {test.isPending ? "Testing…" : "Test"}
          </Button>
          <Button
            variant="secondary"
            onClick={onActivate}
            disabled={activate.isPending || !status?.configured}
          >
            {status?.is_active ? "Active" : "Set active"}
          </Button>
          {status?.configured && (
            <Button variant="ghost" onClick={onDelete} disabled={del.isPending}>
              Remove
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
