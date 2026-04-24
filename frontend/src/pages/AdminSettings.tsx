import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ProviderConfigCard } from "@/components/ProviderConfigCard";
import { useProviderCatalog, useProviderStatuses } from "@/hooks/useProviders";
import { clearAdminToken, getAdminToken, setAdminToken } from "@/lib/auth";

export function AdminSettings() {
  const [token, setToken] = useState(getAdminToken() ?? "");
  const [authed, setAuthed] = useState(!!getAdminToken());
  const catalog = useProviderCatalog();
  const statuses = useProviderStatuses();

  const onSaveToken = () => {
    setAdminToken(token.trim());
    setAuthed(true);
    statuses.refetch();
  };

  const onSignOut = () => {
    clearAdminToken();
    setAuthed(false);
    setToken("");
  };

  if (!authed) {
    return (
      <div className="max-w-md mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Admin access</CardTitle>
            <CardDescription>
              Enter the shared admin token. Saved to <code>localStorage</code> — dev-only auth.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="token">Admin token</Label>
              <Input
                id="token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSaveToken()}
              />
            </div>
            <Button onClick={onSaveToken} disabled={!token.trim()}>
              Continue
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (catalog.isLoading || statuses.isLoading) {
    return <div className="text-sm text-muted-foreground">Loading…</div>;
  }

  if (statuses.error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Failed to load providers</AlertTitle>
        <AlertDescription>
          {String(statuses.error)} — the admin token may be invalid.
          <Button variant="ghost" className="ml-2" onClick={onSignOut}>
            Change token
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const statusByName = new Map((statuses.data ?? []).map((s) => [s.name, s]));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Admin — LLM providers</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure API keys, test them, and pick the active provider + model.
          </p>
        </div>
        <Button variant="ghost" onClick={onSignOut}>
          Sign out
        </Button>
      </div>

      <Alert>
        <AlertTitle>Keys are encrypted at rest</AlertTitle>
        <AlertDescription>
          Stored with Fernet symmetric encryption. Only the last 4 characters are ever shown back.
        </AlertDescription>
      </Alert>

      <div className="grid gap-6 md:grid-cols-2">
        {catalog.data?.providers.map((def) => (
          <ProviderConfigCard
            key={def.name}
            def={def}
            status={statusByName.get(def.name)}
          />
        ))}
      </div>
    </div>
  );
}
