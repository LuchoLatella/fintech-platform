"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Search,
  Activity,
} from "lucide-react";

interface Asset {
  symbol: string;
  name: string;
  price: number;
  change: number;
  volume: string;
}

export default function MercadoPage() {
  const [search, setSearch] = useState("");
  const [assets, setAssets] = useState<Asset[]>([]);

  useEffect(() => {
    setAssets([
      {
        symbol: "AAPL",
        name: "Apple",
        price: 213.22,
        change: 1.42,
        volume: "82M",
      },
      {
        symbol: "NVDA",
        name: "NVIDIA",
        price: 1023.15,
        change: 4.31,
        volume: "65M",
      },
      {
        symbol: "TSLA",
        name: "Tesla",
        price: 187.11,
        change: -2.12,
        volume: "43M",
      },
      {
        symbol: "BTC-USD",
        name: "Bitcoin",
        price: 67421,
        change: 3.12,
        volume: "18B",
      },
    ]);
  }, []);

  const filtered = assets.filter(
    (a) =>
      a.symbol.toLowerCase().includes(search.toLowerCase()) ||
      a.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6 text-white">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Mercado</h1>

          <p className="text-gray-400 mt-1">
            Cotizaciones en tiempo real
          </p>
        </div>

        <div className="relative w-[320px]">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-500" />

          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar activo..."
            className="w-full bg-[#081018] border border-[#1f2a37] rounded-xl py-2 pl-10 pr-4 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {filtered.map((asset) => (
          <div
            key={asset.symbol}
            className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-bold text-lg">
                  {asset.symbol}
                </h2>

                <p className="text-sm text-gray-400">
                  {asset.name}
                </p>
              </div>

              {asset.change > 0 ? (
                <TrendingUp className="text-green-400" />
              ) : (
                <TrendingDown className="text-red-400" />
              )}
            </div>

            <div className="space-y-2">
              <p className="text-3xl font-bold">
                ${asset.price.toLocaleString()}
              </p>

              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-semibold ${
                    asset.change > 0
                      ? "text-green-400"
                      : "text-red-400"
                  }`}
                >
                  {asset.change}%
                </span>

                <span className="text-gray-400 text-sm">
                  Vol: {asset.volume}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-6 h-[500px]">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-cyan-400" />

          <h2 className="text-xl font-semibold">
            Heatmap del mercado
          </h2>
        </div>

        <div className="h-full flex items-center justify-center text-gray-500">
          Integrar TradingView Heatmap / WebSocket
        </div>
      </div>
    </div>
  );
}