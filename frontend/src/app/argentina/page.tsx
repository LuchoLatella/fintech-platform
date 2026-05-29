"use client";

import {
  Landmark,
  Flag,
  ArrowUpRight,
} from "lucide-react";

const dollars = [
  { type: "Oficial", value: 1230 },
  { type: "MEP", value: 1288 },
  { type: "CCL", value: 1312 },
  { type: "Blue", value: 1340 },
];

export default function ArgentinaPage() {
  return (
    <div className="p-6 text-white space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Módulo Argentina
        </h1>

        <p className="text-gray-400 mt-1">
          Economía, dólar y oportunidades locales
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {dollars.map((d) => (
          <div
            key={d.type}
            className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5"
          >
            <Flag className="text-cyan-400 mb-3" />

            <p className="text-gray-400">
              Dólar {d.type}
            </p>

            <h2 className="text-4xl font-bold mt-2">
              ${d.value}
            </h2>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-6 h-[400px]">
          <div className="flex items-center gap-2 mb-4">
            <Landmark className="text-yellow-400" />

            <h2 className="text-xl font-semibold">
              Riesgo País
            </h2>
          </div>

          <div className="h-full flex items-center justify-center text-gray-500">
            Integrar gráfico histórico
          </div>
        </div>

        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <ArrowUpRight className="text-green-400" />

            <h2 className="text-xl font-semibold">
              Oportunidades detectadas
            </h2>
          </div>

          <div className="space-y-4">
            <div className="border border-[#1f2a37] rounded-xl p-4">
              <h3 className="font-bold">
                AL30
              </h3>

              <p className="text-sm text-gray-400 mt-1">
                Posible compresión de spread.
              </p>
            </div>

            <div className="border border-[#1f2a37] rounded-xl p-4">
              <h3 className="font-bold">
                CEDEAR NVDA
              </h3>

              <p className="text-sm text-gray-400 mt-1">
                Desacople respecto al subyacente.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}