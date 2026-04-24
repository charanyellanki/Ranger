import { Badge } from "./ui/badge";
import type { Severity } from "@/lib/types";

export function SeverityBadge({ severity }: { severity: Severity | null | undefined }) {
  if (!severity) return <Badge variant="outline">—</Badge>;
  return <Badge variant={severity}>{severity}</Badge>;
}
