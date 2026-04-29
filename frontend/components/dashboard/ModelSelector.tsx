import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, Cpu, Check, RefreshCw } from "lucide-react";
import { fetchModels, activateModel, triggerInference } from "@/lib/api";
import type { ModelInfo } from "@/lib/types";
import clsx from "clsx";

export default function ModelSelector() {
  const [open, setOpen] = useState(false);
  const qc = useQueryClient();

  const { data: models = [] } = useQuery<ModelInfo[]>({
    queryKey: ["models"],
    queryFn: fetchModels,
    staleTime: 60_000,
  });

  const active = models.find((m) => m.is_active);

  const activate = useMutation({
    mutationFn: (version: string) => activateModel(version),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["models"] });
      setOpen(false);
    },
  });

  const runInference = useMutation({
    mutationFn: triggerInference,
  });

  return (
    <div className="relative flex items-center gap-2">
      {/* Inference trigger */}
      <button
        onClick={() => runInference.mutate()}
        disabled={runInference.isPending}
        title="Run inference now"
        className="p-1.5 rounded-lg border border-bg-border text-text-secondary hover:text-accent-blue hover:border-accent-blue/30 transition-colors"
      >
        <RefreshCw className={clsx("w-4 h-4", runInference.isPending && "animate-spin")} />
      </button>

      {/* Model dropdown */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-bg-border bg-bg-card text-sm text-text-secondary hover:border-accent-purple/40 transition-colors"
      >
        <Cpu className="w-3.5 h-3.5 text-accent-purple" />
        <span className="font-mono">{active?.version ?? "no model"}</span>
        <ChevronDown className={clsx("w-3.5 h-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-full right-0 mt-1 z-50 w-72 bg-bg-card border border-bg-border rounded-xl shadow-2xl overflow-hidden">
            <div className="px-3 py-2 border-b border-bg-border">
              <p className="text-xs text-text-muted uppercase tracking-widest">Select Model</p>
            </div>
            <ul className="py-1 max-h-64 overflow-y-auto">
              {models.length === 0 && (
                <li className="px-3 py-3 text-sm text-text-muted text-center">
                  No models found in /models
                </li>
              )}
              {models.map((m) => (
                <li key={m.version}>
                  <button
                    onClick={() => activate.mutate(m.version)}
                    disabled={m.is_active || !m.lgbm_ready || !m.lstm_ready}
                    className={clsx(
                      "w-full text-left px-3 py-2.5 flex items-start gap-3 hover:bg-bg-secondary transition-colors",
                      m.is_active && "opacity-70 cursor-default",
                      (!m.lgbm_ready || !m.lstm_ready) && "opacity-40 cursor-not-allowed"
                    )}
                  >
                    <div className="mt-0.5 shrink-0">
                      {m.is_active ? (
                        <Check className="w-4 h-4 text-accent-green" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-bg-border" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-text-primary">{m.version}</span>
                        {m.is_active && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20">
                            ACTIVE
                          </span>
                        )}
                        {(!m.lgbm_ready || !m.lstm_ready) && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-red/10 text-accent-red border border-accent-red/20">
                            INCOMPLETE
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-text-muted mt-0.5 truncate">
                        {m.description || `${m.num_features} features · ${m.coins.length} coins`}
                      </p>
                      {m.trained_at && (
                        <p className="text-[10px] text-text-muted/60 mt-0.5">{m.trained_at}</p>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
