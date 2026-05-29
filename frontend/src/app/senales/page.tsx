"use client";
            className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Brain className="text-violet-400" />
                <h2 className="text-xl font-bold">
                  {signal.asset}
                </h2>
              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-bold ${
                  signal.signal === "COMPRA"
                    ? "bg-green-500/20 text-green-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >
                {signal.signal}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-gray-400 text-sm">Confianza</p>
                <p className="text-4xl font-bold text-cyan-400">
                  {signal.confidence}%
                </p>
              </div>

              <div>
                <p className="text-gray-400 text-sm">Modelo</p>
                <p>{signal.strategy}</p>
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
          El motor de IA analiza momentum, volatilidad,
          volumen, RSI, MACD, sentimiento y correlaciones
          históricas para generar oportunidades de compra
          y venta.
        </p>
      </div>
    </div>
  );
}