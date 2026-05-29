"use client";
    qty: 0.12,
    value: 8200,
    pnl: 8.3,
  },
];

export default function PortafolioPage() {
  const total = positions.reduce((acc, p) => acc + p.value, 0);

  return (
    <div className="p-6 text-white space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Portafolio</h1>
          <p className="text-gray-400 mt-1">
            Gestión de cartera y riesgo
          </p>
        </div>

        <button className="bg-cyan-500 text-black px-5 py-2 rounded-xl font-semibold">
          Nueva operación
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">
          <Wallet className="text-cyan-400 mb-4" />
          <p className="text-gray-400">Capital total</p>
          <h2 className="text-4xl font-bold mt-2">
            ${total.toLocaleString()}
          </h2>
        </div>

        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">
          <TrendingUp className="text-green-400 mb-4" />
          <p className="text-gray-400">Rendimiento</p>
          <h2 className="text-4xl font-bold mt-2 text-green-400">
            +18.4%
          </h2>
        </div>

        <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl p-5">
          <PieChart className="text-violet-400 mb-4" />
          <p className="text-gray-400">Diversificación</p>
          <h2 className="text-4xl font-bold mt-2">
            Alta
          </h2>
        </div>
      </div>

      <div className="bg-[#081018] border border-[#1f2a37] rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#0d1622] text-gray-400 text-sm">
            <tr>
              <th className="text-left p-4">Activo</th>
              <th className="text-left p-4">Cantidad</th>
              <th className="text-left p-4">Valor</th>
              <th className="text-left p-4">P&L</th>
            </tr>
          </thead>

          <tbody>
            {positions.map((p) => (
              <tr
                key={p.symbol}
                className="border-t border-[#1f2a37]"
              >
                <td className="p-4 font-semibold">{p.symbol}</td>
                <td className="p-4">{p.qty}</td>
                <td className="p-4">
                  ${p.value.toLocaleString()}
                </td>
                <td className="p-4 text-green-400 font-bold">
                  +{p.pnl}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}