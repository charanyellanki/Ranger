import { useNavigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { SeverityBadge } from "./SeverityBadge";
import { formatRelative } from "@/lib/utils";
import type { Alert } from "@/lib/types";

export function AlertsTable({ alerts }: { alerts: Alert[] }) {
  const navigate = useNavigate();

  if (alerts.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        No alerts yet. Submit a test alert to see the triage flow in action.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Device</TableHead>
          <TableHead>Alert type</TableHead>
          <TableHead>Severity hint</TableHead>
          <TableHead>Received</TableHead>
          <TableHead className="text-right">ID</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {alerts.map((a) => (
          <TableRow
            key={a.id}
            onClick={() => navigate(`/alerts/${a.id}`)}
            className="cursor-pointer"
          >
            <TableCell className="font-medium">{a.device_id}</TableCell>
            <TableCell>{a.alert_type}</TableCell>
            <TableCell>
              <SeverityBadge severity={a.severity_hint} />
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatRelative(a.created_at)}
            </TableCell>
            <TableCell className="text-right text-xs text-muted-foreground font-mono">
              {a.id.slice(0, 8)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
