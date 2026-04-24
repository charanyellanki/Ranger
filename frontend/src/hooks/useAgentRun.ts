import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useRunsForAlert(alertId: string | undefined) {
  return useQuery({
    queryKey: ["runs", alertId],
    queryFn: () => api.listRuns(alertId),
    enabled: !!alertId,
    refetchInterval: (q) => {
      const data = q.state.data;
      const active = data?.some((r) => r.status === "running");
      return active ? 2_000 : false;
    },
  });
}

export function useRun(runId: string | undefined) {
  return useQuery({
    queryKey: ["run", runId],
    queryFn: () => api.getRun(runId as string),
    enabled: !!runId,
    refetchInterval: (q) => (q.state.data?.status === "running" ? 2_000 : false),
  });
}
