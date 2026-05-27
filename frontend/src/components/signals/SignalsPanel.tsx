"use client";
import { useEffect, useState } from "react";
import { Brain, ArrowUpRight, ShieldAlert, Target, TrendingUp } from "lucide-react";
import { signalsAPI } from "@/lib/api";
import clsx from "clsx";

interface Signal {
  id: string; symbol: string; asset_name: string; exchange: string;
  asset_class: string; signal_type: string; strategy: string;
  confidence: number; risk_score: number; expected_return?: number;
  entry_price?: number; stop_loss?: number; take_profit_1?: number;
  risk_reward?: number; rationale: string; generated_at: string;
}

const SIGNAL_FILTERS = [
  { label: "Todas",    value: ""      },
  { label: "Compra",   value: "buy"   },
  { label: "Venta",    value: "sell"  },
  { label: "Monitoreo",value: "watch" },
];

export function SignalsPanel() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<Signal | null>(null);

  useEffect(() => {
    setLoading(true);
    signalsAPI.list({ signal_type: filter || undefined, min_confidence: 60 })
      .then((res) => setSignals(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent-purple/10 border border-accent-purple/25 flex items-center justify-center">
            <Brain size={13} className="text-accent-purple" />
          </div>
          <span className="font-display text-sm font-medium text-text-primary">Señales IA</span>
          <span className="text-xs text-text-muted bg-bg-base border border-bg-border px-2 py-0.5 rounded-full">
            {signals.length} activas
          </span>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-1.5">
        {SIGNAL_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={clsx(
              "px-3 py-1 rounded-lg text-xs font-medium transition-colors",
              filter === f.value
                ? "bg-accent-purple/10 text-accent-purple border border-accent-purple/25"
                : "text-text-muted hover:text-text-secondary border border-transparent hover:border-bg-border"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Lista */}
      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-bg-hover animate-pulse" />
          ))
        ) : signals.length === 0 ? (
          <p className="text-sm text-text-muted text-center py-8">Sin señales para los filtros seleccionados</p>
        ) : (
          signals.map((sig) => (
            <SignalRow
              key={sig.id}
              signal={sig}
              onClick={() => setSelected(selected?.id === sig.id ? null : sig)}
              expanded={selected?.id === sig.id}
            />
          ))
        )}
      </div>
    </div>
  );
}

function SignalRow({ signal: s, onClick, expanded }: { signal: Signal; onClick: () => void; expanded: boolean }) {
  const typeColors: Record<string, string> = {
    buy:   "badge-buy",
    sell:  "badge-sell",
    watch: "badge-watch",
    hold:  "badge-hold",
    avoid: "badge-avoid",
  };
  const typeLabels: Record<string, string> = {
    buy: "COMPRA", sell: "VENTA", watch: "MONITOREO", hold: "MANTENER", avoid: "EVITAR",
  };
  const confColor = s.confidence >= 75 ? "text-accent-green" : s.confidence >= 60 ? "text-accent-amber" : "text-text-secondary";

  return (
    <div
      className="rounded-xl border border-bg-border hover:border-bg-hover bg-bg-base cursor-pointer transition-all"
      onClick={onClick}
    >
      <div className="flex items-center gap-3 p-3">
        {/* Símbolo */}
        <div className="w-9 h-9 rounded-lg bg-bg-card border border-bg-border flex items-center justify-center shrink-0">
          <span className="font-display text-xs font-medium text-text-primary">
            {s.symbol.slice(0, 3)}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-display text-sm font-medium text-text-primary">{s.symbol}</span>
            <span className={clsx("text-xs px-1.5 py-0.5 rounded font-display", typeColors[s.signal_type])}>
              {typeLabels[s.signal_type] || s.signal_type.toUpperCase()}
            </span>
            <span className="text-xs text-text-muted">{s.exchange}</span>
          </div>
          <p className="text-xs text-text-secondary truncate mt-0.5">{s.asset_name}</p>
        </div>

        <div className="text-right shrink-0">
          <div className="flex items-center gap-1 justify-end">
            <Target size={11} className={confColor} />
            <span className={clsx("font-display text-sm font-medium", confColor)}>
              {s.confidence.toFixed(0)}%
            </span>
          </div>
          {s.expected_return != null && (
            <p className={clsx("text-xs font-display", s.expected_return > 0 ? "positive" : "negative")}>
              {s.expected_return > 0 ? "+" : ""}{s.expected_return.toFixed(1)}%
            </p>
          )}
        </div>

        <ArrowUpRight
          size={14}
          className={clsx("text-text-muted transition-transform shrink-0", expanded && "rotate-45")}
        />
      </div>

      {/* Detalle expandido */}
      {expanded && (
        <div className="px-3 pb-3 pt-0 border-t border-bg-border animate-fade-in">
          <p className="text-xs text-text-secondary leading-relaxed mt-2 mb-3">{s.rationale}</p>
          <div className="grid grid-cols-3 gap-2">
            {s.entry_price && (
              <div className="bg-bg-card rounded-lg p-2">
                <p className="text-xs text-text-muted">Entrada</p>
                <p className="font-display text-xs font-medium text-text-primary">${s.entry_price.toFixed(2)}</p>
              </div>
            )}
            {s.stop_loss && (
              <div className="bg-bg-card rounded-lg p-2">
                <p className="text-xs text-text-muted">Stop Loss</p>
                <p className="font-display text-xs font-medium text-accent-red">${s.stop_loss.toFixed(2)}</p>
              </div>
            )}
            {s.take_profit_1 && (
              <div className="bg-bg-card rounded-lg p-2">
                <p className="text-xs text-text-muted">Take Profit</p>
                <p className="font-display text-xs font-medium text-accent-green">${s.take_profit_1.toFixed(2)}</p>
              </div>
            )}
          </div>
          {s.risk_reward && (
            <p className="text-xs text-text-muted mt-2">
              Riesgo/Beneficio: <span className="text-accent-blue font-medium">{s.risk_reward.toFixed(1)}x</span>
              {" · "}Riesgo: <span className={s.risk_score > 60 ? "text-accent-red" : "text-accent-green"}>
                {s.risk_score.toFixed(0)}%
              </span>
            </p>
          )}
          <p className="text-xs text-text-muted mt-1">
            ⚠️ Análisis informativo. No constituye asesoramiento financiero.
          </p>
        </div>
      )}
    </div>
  );
}
