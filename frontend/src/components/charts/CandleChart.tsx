"use client";
import { useEffect, useRef, useState } from "react";
import { marketAPI } from "@/lib/api";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"];

interface Props {
  symbol: string;
  defaultTimeframe?: string;
  height?: number;
}

export function CandleChart({ symbol, defaultTimeframe = "1d", height = 380 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const [timeframe, setTimeframe] = useState(defaultTimeframe);
  const [loading, setLoading] = useState(true);

  // Inicializar chart
  useEffect(() => {
    if (!containerRef.current) return;
    let chart: any;

    const init = async () => {
      const { createChart, ColorType, CrosshairMode } = await import("lightweight-charts");

      chart = createChart(containerRef.current!, {
        width:  containerRef.current!.offsetWidth,
        height,
        layout: {
          background:  { type: ColorType.Solid, color: "#111926" },
          textColor:   "#7A8FA8",
        },
        grid: {
          vertLines:   { color: "#1C2A3A" },
          horzLines:   { color: "#1C2A3A" },
        },
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: { borderColor: "#1C2A3A" },
        timeScale:       { borderColor: "#1C2A3A", timeVisible: true },
      });

      seriesRef.current = chart.addCandlestickSeries({
        upColor:       "#00E5A0",
        downColor:     "#FF4D6A",
        borderVisible: false,
        wickUpColor:   "#00E5A0",
        wickDownColor: "#FF4D6A",
      });

      chartRef.current = chart;

      // Responsive resize
      const ro = new ResizeObserver(() => {
        if (containerRef.current)
          chart.resize(containerRef.current.offsetWidth, height);
      });
      ro.observe(containerRef.current!);
    };

    init();
    return () => { chart?.remove(); };
  }, [height]);

  // Cargar datos cuando cambie símbolo o timeframe
  useEffect(() => {
    if (!seriesRef.current) return;
    setLoading(true);
    marketAPI.history(symbol, timeframe)
      .then((res) => {
        const candles = res.data.data.map((d: any) => ({
          time:  d.time.split("T")[0] || d.time,
          open:  d.open,
          high:  d.high,
          low:   d.low,
          close: d.close,
        }));
        seriesRef.current.setData(candles);
        chartRef.current?.timeScale().fitContent();
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbol, timeframe]);

  return (
    <div className="flex flex-col gap-3">
      {/* Selector de timeframe */}
      <div className="flex items-center gap-1">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-2.5 py-1 rounded text-xs font-display transition-colors ${
              timeframe === tf
                ? "bg-accent-green/10 text-accent-green border border-accent-green/25"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            {tf.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Chart container */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-bg-card/60 rounded-xl z-10">
            <div className="w-5 h-5 border-2 border-accent-green/30 border-t-accent-green rounded-full animate-spin" />
          </div>
        )}
        <div ref={containerRef} className="rounded-xl overflow-hidden" style={{ height }} />
      </div>
    </div>
  );
}
