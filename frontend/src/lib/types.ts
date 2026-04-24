export type Severity = "low" | "medium" | "high" | "critical";

export interface Alert {
  id: string;
  device_id: string;
  alert_type: string;
  severity_hint: Severity | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AgentStep {
  id: string;
  step_index: number;
  node_name: string;
  status: "pending" | "running" | "done" | "failed";
  input_state: Record<string, unknown> | null;
  output_state: Record<string, unknown> | null;
  reasoning: string | null;
  llm_calls: number;
  tokens_used: number;
  duration_ms: number;
  error: string | null;
  started_at: string;
}

export interface AgentRun {
  id: string;
  alert_id: string;
  status: "running" | "completed" | "failed";
  outcome: "remediated" | "escalated" | "failed" | null;
  summary: string | null;
  severity: Severity | null;
  failure_modes: string[] | null;
  retrieved_runbooks:
    | Array<{ slug: string; title: string; risk_level: string; score: number }>
    | null;
  total_tokens: number;
  total_llm_calls: number;
  started_at: string;
  completed_at: string | null;
  steps: AgentStep[];
}

export interface Runbook {
  id: string;
  slug: string;
  title: string;
  risk_level: string;
  indexed_at: string;
}

export interface RunbookDetail extends Runbook {
  content: string;
}

export type ProviderName = "openai" | "anthropic" | "gemini" | "grok" | "ollama";

export interface ProviderCatalogEntry {
  name: ProviderName;
  label: string;
  models: string[];
  needs_api_key: boolean;
  needs_base_url: boolean;
}

export interface ProviderStatus {
  name: ProviderName;
  configured: boolean;
  is_active: boolean;
  api_key_last4: string | null;
  active_model: string | null;
  base_url: string | null;
}

export interface ActiveProvider {
  configured: boolean;
  provider?: ProviderName;
  model?: string;
}

export interface StreamEvent {
  type: "step" | "run_complete" | "run_failed" | "ping";
  step_index?: number;
  node_name?: string;
  status?: string;
  reasoning?: string | null;
  tokens_used?: number;
  duration_ms?: number;
  error?: string | null;
  outcome?: string;
  summary?: string;
  severity?: Severity;
  timestamp?: string;
  replayed?: boolean;
}
