"use client";

import { useEffect, useState } from "react";

import {
  TrendingUp,
  TrendingDown,
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

interface AnalysisResult {
  symbol: string;

  trend: string;
  strength: number;

  rsi_14: number;

  ema_9: number;
  ema_21: number;
  ema_50: number;
  ema_200: number;

  macd_line: number;
  macd_signal: number;
  macd_hist: number;

  signals: string[];

  stop_loss: number;
  take_profit: number;
}

export default function AnalisisPage() {

  const [symbol, setSymbol] =
    useState("AAPL");

  const [analysis, setAnalysis] =
    useState<AnalysisResult | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    async function loadAnalysis() {

      try {

        setLoading(true);

        const response = await fetch(
          `http://localhost:8000/api/v1/analysis/technical/${symbol}`
        );

        const data =
          await response.json();

        setAnalysis(data);

      } catch (error) {

        console.error(
          "Error loading analysis:",
          error
        );

      } finally {

        setLoading(false);

      }
    }

    loadAnalysis();

  }, [symbol]);

  return (
    <div className="p-6 text-white space-y-6">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-3xl font-bold">
            Análisis Técnico
          </h1>

          <p className="text-gray-400 mt-1">
            Motor analítico en tiempo real
          </p>
        </div>

        {/* SELECT */}
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

      {/* LOADING */}
      {loading && (
        <div className="text-gray-400">
          Analizando mercado...
        </div>
      )}

      {/* ANALYSIS */}
      {!loading && analysis && (

        <>
          {/* GRID */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* RSI */}
            <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

              <div className="flex items-center gap-2 mb-3">
                <Activity className="text-cyan-400 w-5 h-5" />

                <h2 className="font-semibold">
                  RSI 14
                </h2>
              </div>

              <p className="text-4xl font-bold text-cyan-400">
                {analysis.rsi_14?.toFixed(2)}
              </p>

              <p className="text-sm text-gray-400 mt-2">
                {analysis.rsi_14 > 70
                  ? "Sobrecomprado"
                  : analysis.rsi_14 < 30
                  ? "Sobrevendido"
                  : "Neutral"}
              </p>

            </div>

            {/* TREND */}
            <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

              <div className="flex items-center gap-2 mb-3">

                {analysis.trend === "bullish"
                  ? (
                    <TrendingUp className="text-green-400 w-5 h-5" />
                  )
                  : (
                    <TrendingDown className="text-red-400 w-5 h-5" />
                  )
                }

                <h2 className="font-semibold">
                  Tendencia
                </h2>

              </div>

              <p
                className={`text-4xl font-bold ${
                  analysis.trend === "bullish"
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {analysis.trend.toUpperCase()}
              </p>

              <p className="text-sm text-gray-400 mt-2">
                Fuerza: {analysis.strength}%
              </p>

            </div>

            {/* IA SCORE */}
            <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

              <div className="flex items-center gap-2 mb-3">
                <Brain className="text-violet-400 w-5 h-5" />

                <h2 className="font-semibold">
                  Score IA
                </h2>
              </div>

              <p className="text-4xl font-bold text-violet-400">
                {analysis.strength}%
              </p>

              <p className="text-sm text-gray-400 mt-2">
                Score probabilístico
              </p>

            </div>

          </div>

          {/* SIGNALS */}
          <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-6">

            <h2 className="text-xl font-bold mb-4">
              Señales Detectadas
            </h2>

            <div className="flex flex-wrap gap-2">

              {analysis.signals.map((signal) => (

                <div
                  key={signal}
                  className="px-3 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm"
                >
                  {signal}
                </div>

              ))}

            </div>

          </div>

          {/* RISK */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* STOP LOSS */}
            <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

              <h2 className="text-lg font-semibold mb-3">
                Stop Loss
              </h2>

              <p className="text-3xl font-bold text-red-400">
                ${analysis.stop_loss?.toFixed(2)}
              </p>

            </div>

            {/* TAKE PROFIT */}
            <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">

              <h2 className="text-lg font-semibold mb-3">
                Take Profit
              </h2>

              <p className="text-3xl font-bold text-green-400">
                ${analysis.take_profit?.toFixed(2)}
              </p>

            </div>

          </div>

        </>

      )}

    </div>
  );
}