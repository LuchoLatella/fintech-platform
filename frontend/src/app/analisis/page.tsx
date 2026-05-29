"use client";

import { useState } from "react";

import {
  TrendingUp,
  Activity,
  Brain,
} from "lucide-react";

import { CandleChart } from "@/components/charts/CandleChart";

const SYMBOLS = [
  "AAPL",
  "NVDA",
  "TSLA",
  "MSFT",
  "BTC-USD",
  "ETH-USD",
];

export default function AnalisisPage() {

  const [symbol, setSymbol] =
    useState("AAPL");

  return (
    <div className="p-6 text-white space-y-6">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-3xl font-bold">
            Análisis Técnico
          </h1>

          <p className="text-gray-400 mt-1">
            Velas OHLCV + indicadores
          </p>
        </div>

        {/* SELECTOR */}
        <select
          value={symbol}
          onChange={(e) =>
            setSymbol(e.target.value)
          }
          className="bg-[#081018] border border-[#1f2a37] rounded-xl px-4 py-2 outline-none"
        >
          {SYMBOLS.map((s) => (
            <option
              key={s}
              value={s}
            >
              {s}
            </option>
          ))}
        </select>

      </div>

      {/* CHART */}
      <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-4">

        <CandleChart
          symbol={symbol}
          height={500}
        />

      </div>

      {/* GRID INDICADORES */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* RSI */}
        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

          <div className="flex items-center gap-2 mb-3">
            <Activity className="text-cyan-400 w-5 h-5" />

            <h2 className="font-semibold">
              RSI
            </h2>
          </div>

          <p className="text-4xl font-bold text-cyan-400">
            58
          </p>

          <p className="text-sm text-gray-400 mt-2">
            Neutral / Bullish
          </p>

        </div>

        {/* EMA */}
        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="text-green-400 w-5 h-5" />

            <h2 className="font-semibold">
              EMA Trend
            </h2>
          </div>

          <p className="text-4xl font-bold text-green-400">
            BUY
          </p>

          <p className="text-sm text-gray-400 mt-2">
            EMA20 sobre EMA50
          </p>

        </div>

        {/* IA */}
        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

          <div className="flex items-center gap-2 mb-3">
            <Brain className="text-violet-400 w-5 h-5" />

            <h2 className="font-semibold">
              IA Score
            </h2>
          </div>

          <p className="text-4xl font-bold text-violet-400">
            82%
          </p>

          <p className="text-sm text-gray-400 mt-2">
            Probabilidad alcista
          </p>

        </div>

      </div>

    </div>
  );
}