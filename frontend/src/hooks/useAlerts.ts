import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type SubmitAlertInput } from "@/lib/api";

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: () => api.listAlerts(50),
    refetchInterval: 10_000,
  });
}

export function useSubmitAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SubmitAlertInput) => api.submitAlert(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["runs"] });
    },
  });
}

export function useAlert(id: string | undefined) {
  return useQuery({
    queryKey: ["alert", id],
    queryFn: () => api.getAlert(id as string),
    enabled: !!id,
  });
}
