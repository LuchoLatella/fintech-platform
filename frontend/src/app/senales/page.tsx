"use client";

import { useEffect, useState } from "react";

import {
  Brain,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";

interface Signal {
  symbol: string;

  prediction: string;

  confidence: number;

  features: {
    rsi: number;
    macd_hist: number;
    trend_strength: number;
  };
}

export default function SenalesPage() {

  const [signals, setSignals] = useState<Signal[]>([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {

    async function loadSignals() {

      try {

        const symbols = [
          "AAPL",
          "NVDA",
          "TSLA",
          "MSFT",
          "AMZN",
          "META",

          "BTC-USD",
          "ETH-USD",

          "GGAL.BA",
          "YPFD.BA",
          "PAMP.BA",
        ];

        const responses = await Promise.all(

          symbols.map((symbol) =>

            fetch(
              `http://localhost:8000/api/v1/ml/predict/${symbol}`
            ).then((r) => r.json())
          )
        );

        const formatted = responses
          .filter((r) => r.ok)
          .map((r) => ({
            symbol: r.data.symbol,

            prediction: r.data.prediction,

            confidence: r.data.confidence,

            features: r.data.features,
          }))
          .sort(
            (a, b) =>
              b.confidence - a.confidence
          );

        setSignals(formatted);

      } catch (error) {

        console.error(
          "Error cargando señales IA",
          error
        );

      } finally {

        setLoading(false);
      }
    }

    loadSignals();

  }, []);

  return (
    <div className="p-6 text-white space-y-6">

      <div>
        <h1 className="text-3xl font-bold">
          Señales IA
        </h1>

        <p className="text-gray-400 mt-1">
          Ranking inteligente de oportunidades
        </p>
      </div>

      {loading && (
        <div className="text-gray-400">
          Analizando mercados globales...
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

        {signals.map((signal) => (

          <div
            key={signal.symbol}
            className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5"
          >

            <div className="flex items-center justify-between mb-4">

              <div className="flex items-center gap-2">

                <Brain className="text-violet-400" />

                <h2 className="text-xl font-bold">
                  {signal.symbol}
                </h2>

              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  signal.prediction === "bullish"
                    ? "bg-green-500/20 text-green-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >

                {signal.prediction === "bullish"
                  ? "COMPRA"
                  : "VENTA"}

              </span>

            </div>

            <div className="space-y-3">

              <div>

                <p className="text-gray-400 text-sm">
                  Confianza IA
                </p>

                <p className="text-4xl font-bold text-cyan-400">
                  {signal.confidence}%
                </p>

              </div>

              <div>

                <p className="text-gray-400 text-sm">
                  RSI
                </p>

                <p>
                  {signal.features.rsi?.toFixed(2)}
                </p>

              </div>

              <div>

                <p className="text-gray-400 text-sm">
                  MACD
                </p>

                <p>
                  {signal.features.macd_hist?.toFixed(2)}
                </p>

              </div>

              <div>

                <p className="text-gray-400 text-sm">
                  Fuerza tendencia
                </p>

                <p>
                  {signal.features.trend_strength}
                </p>

              </div>

              <div className="pt-4 flex gap-3">

                <button className="flex-1 bg-cyan-500 hover:bg-cyan-400 transition rounded-xl py-2 font-semibold text-black">
                  Operar
                </button>

                <button className="border border-[#1f2a37] rounded-xl px-4">
                  <ArrowUpRight size={18} />
                </button>

              </div>

            </div>

          </div>
        ))}

      </div>

      <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-6">

        <div className="flex items-center gap-2 mb-4">

          <ShieldCheck className="text-green-400" />

          <h2 className="text-xl font-semibold">
            Explicación de la IA
          </h2>

        </div>

        <p className="text-gray-300 leading-relaxed">

          El motor de IA analiza momentum,
          volatilidad, RSI, MACD,
          tendencia, ATR, Bollinger Bands
          y volumen para detectar
          oportunidades globales.

        </p>

      </div>

    </div>
  );
}