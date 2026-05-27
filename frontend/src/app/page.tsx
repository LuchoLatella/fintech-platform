"use client";
import { useEffect, useState } from "react";
import { CandleChart } from "@/components/charts/CandleChart";
import { ArgentinaPanel } from "@/components/argentina/ArgentinaPanel";
import { SignalsPanel } from "@/components/signals/SignalsPanel";
import { marketAPI, signalsAPI } from "@/lib/api";
import { TrendingUp, TrendingDown, Activity, Zap } from "lucide-react";
import clsx from "clsx";

// Activos del watchlist rápido en el dashboard
const QUICK_WATCH = [
  { symbol: "AAPL",    label: "Apple"   },
  { symbol: "NVDA",    label: "NVIDIA"  },
  { symbol: "SPY",     label: "S&P 500" },
  { symbol: "BTC-USD", label: "Bitcoin" },
  { symbol: "GLD",     label: "Oro"     },
];

export default function DashboardPage() {
  const [activeSymbol, setActiveSymbol] = useState("AAPL");
  const [quotes, setQuotes] = useState<Record<string, any>>({});
  const [topSignals, setTopSignals] = useState<any[]>([]);
  const [loadingSignals, setLoadingSignals] = useState(true);

  // Cotizaciones del watchlist rápido
  useEffect(() => {
    const symbols = QUICK_WATCH.map((w) => w.symbol);
    marketAPI.batchQuotes(symbols)
      .then((res) => {
        const map: Record<string, any> = {};
        res.data.quotes.forEach((q: any) => { if (q.ok) map[q.symbol] = q; });
        setQuotes(map);
      })
      .catch(() => {});
  }, []);

  // Top 3 señales IA para el resumen
  useEffect(() => {
    signalsAPI.ranking(3)
      .then((res) => setTopSignals(res.data.ranking || []))
      .catch(() => {})
      .finally(() => setLoadingSignals(false));
  }, []);

  return (
    <div className="space-y-6 animate-slide-up">

      {/* ── Fila 1: Stats resumidos ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Señales activas"
          value="—"
          sub="Hoy"
          icon={<Zap size={15} className="text-accent-purple" />}
          color="purple"
        />
        <StatCard
          label="Oportunidades ARG"
          value="—"
          sub="Detectadas"
          icon={<Activity size={15} className="text-accent-amber" />}
          color="amber"
        />
        <StatCard
          label="S&P 500"
          value={quotes["SPY"]?.price ? `$${quotes["SPY"].price.toFixed(2)}` : "—"}
          sub={quotes["SPY"]?.change_pct != null
            ? `${quotes["SPY"].change_pct > 0 ? "+" : ""}${quotes["SPY"].change_pct.toFixed(2)}% hoy`
            : ""}
          icon={<TrendingUp size={15} className="text-accent-blue" />}
          color="blue"
          changePositive={quotes["SPY"]?.change_pct >= 0}
        />
        <StatCard
          label="Bitcoin"
          value={quotes["BTC-USD"]?.price
            ? `$${quotes["BTC-USD"].price.toLocaleString("es-AR", { maximumFractionDigits: 0 })}`
            : "—"}
          sub={quotes["BTC-USD"]?.change_pct != null
            ? `${quotes["BTC-USD"].change_pct > 0 ? "+" : ""}${quotes["BTC-USD"].change_pct.toFixed(2)}% hoy`
            : ""}
          icon={<TrendingUp size={15} className="text-accent-amber" />}
          color="amber"
          changePositive={quotes["BTC-USD"]?.change_pct >= 0}
        />
      </div>

      {/* ── Fila 2: Watchlist rápida ── */}
      <div className="grid grid-cols-5 gap-3">
        {QUICK_WATCH.map(({ symbol, label }) => {
          const q = quotes[symbol];
          const up = (q?.change_pct || 0) >= 0;
          return (
            <button
              key={symbol}
              onClick={() => setActiveSymbol(symbol)}
              className={clsx(
                "card p-3 text-left transition-all hover:border-bg-hover",
                activeSymbol === symbol && "border-accent-green/30 bg-accent-green/5"
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-display text-xs font-medium text-text-primary">{symbol}</span>
                {q && (
                  <span className={clsx("text-xs font-display", up ? "positive" : "negative")}>
                    {up ? "▲" : "▼"} {Math.abs(q.change_pct || 0).toFixed(2)}%
                  </span>
                )}
              </div>
              <p className="text-xs text-text-muted">{label}</p>
              {q && (
                <p className="font-display text-sm font-medium text-text-primary mt-1">
                  ${q.price?.toLocaleString("es-AR", { maximumFractionDigits: 2 })}
                </p>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Fila 3: Chart + Argentina ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {/* Gráfico principal */}
        <div className="xl:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-display text-base font-medium text-text-primary">{activeSymbol}</h2>
              {quotes[activeSymbol] && (
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="font-display text-2xl font-medium text-text-primary">
                    ${quotes[activeSymbol]?.price?.toLocaleString("es-AR", { maximumFractionDigits: 2 })}
                  </span>
                  <span className={clsx(
                    "text-sm font-display",
                    (quotes[activeSymbol]?.change_pct || 0) >= 0 ? "positive" : "negative"
                  )}>
                    {(quotes[activeSymbol]?.change_pct || 0) >= 0 ? "+" : ""}
                    {quotes[activeSymbol]?.change_pct?.toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
          <CandleChart symbol={activeSymbol} height={340} />
        </div>

        {/* Panel Argentina */}
        <div className="xl:col-span-1">
          <ArgentinaPanel />
        </div>
      </div>

      {/* ── Fila 4: Señales IA + Top oportunidades ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {/* Señales */}
        <div className="xl:col-span-2">
          <SignalsPanel />
        </div>

        {/* Top 3 oportunidades */}
        <div className="card p-5 space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent-green/10 border border-accent-green/25 flex items-center justify-center">
              <TrendingUp size={13} className="text-accent-green" />
            </div>
            <span className="font-display text-sm font-medium text-text-primary">Top Oportunidades</span>
          </div>

          {loadingSignals ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-20 rounded-xl bg-bg-hover animate-pulse" />
            ))
          ) : topSignals.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">Calculando señales...</p>
          ) : (
            topSignals.map((sig, i) => (
              <div key={sig.symbol} className="bg-bg-base border border-bg-border rounded-xl p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-display text-sm font-medium text-text-primary">
                    #{i + 1} {sig.symbol}
                  </span>
                  <span className="badge-buy text-xs px-1.5 py-0.5 rounded font-display">COMPRA</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <p className="text-xs text-text-muted">Confianza</p>
                    <p className="font-display text-sm text-accent-green font-medium">{sig.confidence?.toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Retorno est.</p>
                    <p className="font-display text-sm text-text-primary">
                      {sig.expected_return != null ? `+${sig.expected_return.toFixed(1)}%` : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">R/B</p>
                    <p className="font-display text-sm text-accent-blue">
                      {sig.risk_reward != null ? `${sig.risk_reward.toFixed(1)}x` : "—"}
                    </p>
                  </div>
                </div>
                {sig.rationale && (
                  <p className="text-xs text-text-muted leading-relaxed line-clamp-2">{sig.rationale}</p>
                )}
              </div>
            ))
          )}

          <p className="text-xs text-text-muted">
            ⚠️ Análisis informativo. No constituye asesoramiento financiero.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Componente StatCard ────────────────────────────────────────────────────────
function StatCard({
  label, value, sub, icon, color, changePositive,
}: {
  label: string; value: string; sub?: string;
  icon: React.ReactNode; color: string; changePositive?: boolean;
}) {
  const colorMap: Record<string, string> = {
    purple: "bg-accent-purple/10 border-accent-purple/25",
    amber:  "bg-accent-amber/10  border-accent-amber/25",
    blue:   "bg-accent-blue/10   border-accent-blue/25",
    green:  "bg-accent-green/10  border-accent-green/25",
  };
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-text-muted">{label}</p>
        <div className={clsx("w-7 h-7 rounded-lg border flex items-center justify-center", colorMap[color])}>
          {icon}
        </div>
      </div>
      <p className="font-display text-xl font-medium text-text-primary">{value}</p>
      {sub && (
        <p className={clsx(
          "text-xs mt-0.5",
          changePositive === true ? "positive" :
          changePositive === false ? "negative" : "text-text-muted"
        )}>{sub}</p>
      )}
    </div>
  );
}
