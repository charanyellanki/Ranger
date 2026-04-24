import { getAdminToken } from "./auth";
import type {
  ActiveProvider,
  Alert,
  AgentRun,
  ProviderCatalogEntry,
  ProviderName,
  ProviderStatus,
  Runbook,
  RunbookDetail,
  Severity,
} from "./types";

const API_BASE: string = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init.headers as Record<string, string>) ?? {}),
  };
  const token = getAdminToken();
  if (token && path.startsWith("/admin")) {
    headers["X-Admin-Token"] = token;
  }
  const resp = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText);
    throw new ApiError(resp.status, `${resp.status}: ${text}`);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

// ─── Alerts ───────────────────────────────────────────────────────

export interface SubmitAlertInput {
  device_id: string;
  alert_type: string;
  severity_hint?: Severity;
  payload?: Record<string, unknown>;
}

export interface AlertSubmitted {
  alert_id: string;
  run_id: string;
  status: string;
}

export const api = {
  listAlerts: (limit = 50) => request<Alert[]>(`/alerts?limit=${limit}`),
  getAlert: (id: string) => request<Alert>(`/alerts/${id}`),
  submitAlert: (body: SubmitAlertInput) =>
    request<AlertSubmitted>(`/alerts`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listRuns: (alertId?: string) =>
    request<AgentRun[]>(`/runs${alertId ? `?alert_id=${alertId}` : ""}`),
  getRun: (runId: string) => request<AgentRun>(`/runs/${runId}`),

  listRunbooks: () => request<Runbook[]>(`/runbooks`),
  getRunbook: (slug: string) => request<RunbookDetail>(`/runbooks/${slug}`),
  searchRunbooks: (q: string, topK = 5) =>
    request<{
      query: string;
      results: Array<{
        slug: string;
        title: string;
        score: number;
        excerpt: string;
        risk_level: string;
      }>;
    }>(`/runbooks/search?q=${encodeURIComponent(q)}&top_k=${topK}`),

  getActiveProvider: () => request<ActiveProvider>(`/admin/active`),
  getProviderCatalog: () =>
    request<{ providers: ProviderCatalogEntry[] }>(`/admin/providers/catalog`),
  listProviders: () => request<ProviderStatus[]>(`/admin/providers`),
  upsertProvider: (
    name: ProviderName,
    body: { api_key?: string; base_url?: string; active_model?: string },
  ) =>
    request<ProviderStatus>(`/admin/providers/${name}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  deleteProvider: (name: ProviderName) =>
    request<void>(`/admin/providers/${name}`, { method: "DELETE" }),
  activateProvider: (name: ProviderName, model: string) =>
    request<{ active_provider: ProviderName; active_model: string }>(
      `/admin/providers/activate`,
      {
        method: "POST",
        body: JSON.stringify({ name, model }),
      },
    ),
  testProvider: (body: {
    name: ProviderName;
    model: string;
    api_key?: string;
    base_url?: string;
  }) =>
    request<{
      success: boolean;
      message: string;
      latency_ms: number | null;
      tokens_used: number | null;
    }>(`/admin/providers/test`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export function wsUrlForRun(runId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws/runs/${runId}`;
}

export { ApiError };
