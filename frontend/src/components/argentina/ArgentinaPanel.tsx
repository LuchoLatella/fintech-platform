"use client";
import { useEffect, useState } from "react";
import { Flag, TrendingUp, TrendingDown, AlertTriangle, RefreshCw } from "lucide-react";
import { argentinaAPI } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

interface DolarRate { label: string; key: string; highlight?: boolean }
const RATES: DolarRate[] = [
  { label: "Oficial",  key: "oficial"  },
  { label: "MEP",      key: "mep",      highlight: true },
  { label: "CCL",      key: "ccl",      highlight: true },
  { label: "Blue",     key: "blue"     },
  { label: "Tarjeta",  key: "tarjeta"  },
];

export function ArgentinaPanel() {
  const { argSnapshot, setArgSnapshot } = useAppStore();
  const [loading, setLoading] = useState(!argSnapshot);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await argentinaAPI.snapshot();
      setArgSnapshot(res.data);
      setLastUpdate(new Date());
    } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { fetch(); const t = setInterval(fetch, 120_000); return () => clearInterval(t); }, []);

  const dolar = argSnapshot?.dolar;
  const rp    = argSnapshot?.riesgo_pais;
  const ops   = argSnapshot?.opportunities || [];

  return (
    <div className="card p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent-amber/10 border border-accent-amber/25 flex items-center justify-center">
            <Flag size={13} className="text-accent-amber" />
          </div>
          <span className="font-display text-sm font-medium text-text-primary">Módulo Argentina</span>
        </div>
        <button
          onClick={fetch}
          className="p-1.5 rounded-lg text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Tipos de cambio */}
      <div>
        <p className="text-xs text-text-muted mb-3 font-display uppercase tracking-wider">USD / ARS</p>
        <div className="grid grid-cols-5 gap-2">
          {RATES.map(({ label, key, highlight }) => {
            const val = dolar?.[key as keyof typeof dolar];
            return (
              <div
                key={key}
                className={clsx(
                  "rounded-lg p-2.5 text-center transition-colors",
                  highlight
                    ? "bg-accent-green/5 border border-accent-green/15"
                    : "bg-bg-base border border-bg-border"
                )}
              >
                <p className="text-xs text-text-muted mb-1">{label}</p>
                <p className={clsx("font-display text-sm font-medium", highlight ? "text-accent-green" : "text-text-primary")}>
                  {val ? `$${val.toLocaleString("es-AR", { maximumFractionDigits: 0 })}` : "—"}
                </p>
              </div>
            );
          })}
        </div>

        {/* Spread MEP/Oficial */}
        {dolar?.spread_mep_oficial !== undefined && dolar.spread_mep_oficial !== null && (
          <div className="mt-2 flex items-center gap-2 text-xs text-text-muted">
            <span>Spread MEP/Oficial:</span>
            <span className={dolar.spread_mep_oficial > 10 ? "text-accent-amber font-medium" : "text-text-secondary"}>
              +{dolar.spread_mep_oficial.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Indicadores macro */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-bg-base border border-bg-border rounded-lg p-3">
          <p className="text-xs text-text-muted mb-1">Riesgo País</p>
          <div className="flex items-end gap-2">
            <span className={clsx(
              "font-display text-xl font-medium",
              (rp || 0) > 1500 ? "text-accent-red" : (rp || 0) > 800 ? "text-accent-amber" : "text-accent-green"
            )}>
              {rp ? rp.toLocaleString() : "—"}
            </span>
            <span className="text-xs text-text-muted pb-0.5">bps</span>
          </div>
        </div>

        <div className="bg-bg-base border border-bg-border rounded-lg p-3">
          <p className="text-xs text-text-muted mb-1">Inflación Mensual</p>
          <div className="flex items-end gap-2">
            <span className="font-display text-xl font-medium text-accent-amber">
              {argSnapshot?.inflacion_mensual ? `${argSnapshot.inflacion_mensual.toFixed(1)}%` : "—"}
            </span>
          </div>
        </div>

        <div className="bg-bg-base border border-bg-border rounded-lg p-3">
          <p className="text-xs text-text-muted mb-1">Tasa BCRA</p>
          <span className="font-display text-xl font-medium text-accent-blue">
            {argSnapshot?.tasa_politica_monetaria ? `${argSnapshot.tasa_politica_monetaria.toFixed(0)}%` : "—"}
          </span>
        </div>

        <div className="bg-bg-base border border-bg-border rounded-lg p-3">
          <p className="text-xs text-text-muted mb-1">Spread CCL/MEP</p>
          <span className={clsx(
            "font-display text-xl font-medium",
            (dolar?.spread_ccl_mep || 0) > 3 ? "text-accent-amber" : "text-text-primary"
          )}>
            {dolar?.spread_ccl_mep != null ? `+${dolar.spread_ccl_mep.toFixed(1)}%` : "—"}
          </span>
        </div>
      </div>

      {/* Oportunidades detectadas */}
      {ops.length > 0 && (
        <div>
          <p className="text-xs text-text-muted mb-2 font-display uppercase tracking-wider">Oportunidades</p>
          <div className="space-y-2">
            {ops.map((op: any, i: number) => (
              <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-accent-amber/5 border border-accent-amber/15">
                <AlertTriangle size={13} className="text-accent-amber mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs text-text-primary leading-relaxed">{op.description}</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    Confianza: <span className="text-accent-amber">{op.confidence?.toFixed(0)}%</span>
                    {" · "}Riesgo: <span className="text-text-secondary capitalize">{op.risk}</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {lastUpdate && (
        <p className="text-xs text-text-muted">
          Actualizado: {lastUpdate.toLocaleTimeString("es-AR")}
        </p>
      )}
    </div>
  );
}
