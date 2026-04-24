import { useActiveProvider } from "@/hooks/useProviders";
import { Badge } from "./ui/badge";

const LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Gemini",
  grok: "Grok",
  ollama: "Ollama",
};

export function ProviderBadge() {
  const { data, isLoading } = useActiveProvider();
  if (isLoading) return null;
  if (!data?.configured) {
    return (
      <Badge variant="destructive" className="gap-1.5">
        No LLM configured
      </Badge>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline">{LABELS[data.provider ?? ""] ?? data.provider}</Badge>
      <span className="text-xs text-muted-foreground">{data.model}</span>
    </div>
  );
}
