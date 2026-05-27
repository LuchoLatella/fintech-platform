"use client";
import { useEffect, useState } from "react";
import { Search, Bell, User, Wifi, WifiOff } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { marketAPI } from "@/lib/api";
import clsx from "clsx";

const TICKER_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "BTC-USD", "ETH-USD", "SPY", "QQQ"];

export function Topbar() {
  const { quotes, updateQuote } = useAppStore();
  const [wsConnected, setWsConnected] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // WebSocket de precios para el ticker
  useEffect(() => {
    let ws: WebSocket;
    const connect = () => {
      ws = new WebSocket(
        `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/v1/quotes?symbols=${TICKER_SYMBOLS.join(",")}`
      );
      ws.onopen  = () => setWsConnected(true);
      ws.onclose = () => { setWsConnected(false); setTimeout(connect, 5000); };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "quote") updateQuote(data);
      };
    };
    connect();
    return () => ws?.close();
  }, []);

  // Búsqueda de activos
  useEffect(() => {
    if (searchQuery.length < 2) { setSearchResults([]); return; }
    const t = setTimeout(async () => {
      try {
        const res = await marketAPI.search(searchQuery);
        setSearchResults(res.data.results.slice(0, 6));
      } catch {}
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  return (
    <header className="h-14 flex items-center gap-4 px-6 bg-bg-surface border-b border-bg-border shrink-0">

      {/* Búsqueda */}
      <div className="relative flex-1 max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Buscar activo..."
          className="w-full bg-bg-card border border-bg-border rounded-lg pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-green/40 transition-colors"
        />
        {searchResults.length > 0 && (
          <div className="absolute top-full mt-1 w-full bg-bg-card border border-bg-border rounded-xl shadow-2xl z-50 overflow-hidden">
            {searchResults.map((r) => (
              <button
                key={r.id}
                onClick={() => { setSearchQuery(""); setSearchResults([]); }}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-bg-hover transition-colors text-left"
              >
                <span className="font-display text-sm font-medium text-text-primary">{r.symbol}</span>
                <span className="text-xs text-text-secondary truncate">{r.name}</span>
                <span className="ml-auto text-xs text-text-muted">{r.exchange}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Ticker de precios */}
      <div className="flex-1 overflow-hidden hidden lg:block">
        <div className="flex gap-6 animate-none">
          {TICKER_SYMBOLS.map((sym) => {
            const q = quotes[sym];
            if (!q) return null;
            const up = (q.change_pct || 0) >= 0;
            return (
              <div key={sym} className="flex items-center gap-2 shrink-0">
                <span className="font-display text-xs text-text-secondary">{sym}</span>
                <span className="font-display text-xs font-medium text-text-primary">
                  {q.price?.toLocaleString("es-AR", { maximumFractionDigits: 2 })}
                </span>
                <span className={clsx("font-display text-xs", up ? "positive" : "negative")}>
                  {up ? "▲" : "▼"} {Math.abs(q.change_pct || 0).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Estado WS + acciones */}
      <div className="flex items-center gap-3 ml-auto">
        <div className="flex items-center gap-1.5">
          {wsConnected
            ? <Wifi size={13} className="text-accent-green" />
            : <WifiOff size={13} className="text-accent-red" />
          }
          <span className="text-xs text-text-muted hidden sm:block">
            {wsConnected ? "En vivo" : "Reconectando..."}
          </span>
        </div>
        <button className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors">
          <Bell size={16} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />
        </button>
        <button className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors">
          <User size={16} />
        </button>
      </div>
    </header>
  );
}
