import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProviderName } from "@/lib/types";

export function useActiveProvider() {
  return useQuery({
    queryKey: ["active-provider"],
    queryFn: () => api.getActiveProvider(),
    refetchInterval: 15_000,
  });
}

export function useProviderCatalog() {
  return useQuery({
    queryKey: ["provider-catalog"],
    queryFn: () => api.getProviderCatalog(),
    staleTime: Infinity,
  });
}

export function useProviderStatuses() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: () => api.listProviders(),
  });
}

export function useUpsertProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      name,
      body,
    }: {
      name: ProviderName;
      body: { api_key?: string; base_url?: string; active_model?: string };
    }) => api.upsertProvider(name, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["active-provider"] });
    },
  });
}

export function useDeleteProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: ProviderName) => api.deleteProvider(name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["active-provider"] });
    },
  });
}

export function useActivateProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, model }: { name: ProviderName; model: string }) =>
      api.activateProvider(name, model),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      qc.invalidateQueries({ queryKey: ["active-provider"] });
    },
  });
}

export function useTestProvider() {
  return useMutation({
    mutationFn: (body: {
      name: ProviderName;
      model: string;
      api_key?: string;
      base_url?: string;
    }) => api.testProvider(body),
  });
}
