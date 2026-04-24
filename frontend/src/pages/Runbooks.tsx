import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export function Runbooks() {
  const list = useQuery({ queryKey: ["runbooks"], queryFn: () => api.listRunbooks() });
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const search = useQuery({
    queryKey: ["runbooks-search", q],
    queryFn: () => api.searchRunbooks(q),
    enabled: q.trim().length > 2,
  });

  const detail = useQuery({
    queryKey: ["runbook", selected],
    queryFn: () => api.getRunbook(selected as string),
    enabled: !!selected,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Runbooks</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Indexed knowledge base — the Knowledge Agent retrieves from this collection.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Semantic search</CardTitle>
          <CardDescription>
            Query exactly as the Knowledge Agent does (vector similarity over chunks).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Input
            placeholder="e.g. device stuck rebooting after firmware update"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {q.trim().length > 2 && (
            <div className="mt-4 space-y-2">
              {search.data?.results.map((r) => (
                <button
                  key={r.slug}
                  onClick={() => setSelected(r.slug)}
                  className="w-full text-left rounded-md border border-border p-3 hover:bg-accent/40 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{r.title}</span>
                    <Badge variant="outline">{r.score}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {r.excerpt}
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>All runbooks</CardTitle>
            <CardDescription>{list.data?.length ?? 0} indexed</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            {list.data?.map((rb) => (
              <button
                key={rb.slug}
                onClick={() => setSelected(rb.slug)}
                className={`w-full text-left rounded-md p-2 text-sm transition-colors ${
                  selected === rb.slug ? "bg-accent" : "hover:bg-accent/40"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span>{rb.title}</span>
                  <Badge variant={riskVariant(rb.risk_level)}>{rb.risk_level}</Badge>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{detail.data?.title ?? "Select a runbook"}</CardTitle>
            {detail.data && (
              <CardDescription>
                risk: {detail.data.risk_level} · slug: <code>{detail.data.slug}</code>
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {detail.data ? (
              <pre className="text-xs whitespace-pre-wrap font-mono bg-muted rounded-md p-3 overflow-auto max-h-[60vh]">
                {detail.data.content}
              </pre>
            ) : (
              <div className="text-sm text-muted-foreground">
                Pick a runbook from the list to see its full content.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function riskVariant(risk: string): "low" | "medium" | "high" {
  if (risk === "high") return "high";
  if (risk === "medium") return "medium";
  return "low";
}
