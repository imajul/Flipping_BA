import React from "react";

function Val({ v }) {
  if (v == null || v === "") return <span className="text-gray-400">—</span>;
  if (typeof v === "boolean") return <span>{v ? "✅ Sí" : "❌ No"}</span>;
  if (typeof v === "number") return <span>{v.toLocaleString("es-AR")}</span>;
  return <span>{String(v)}</span>;
}

function PctCell({ v }) {
  if (v == null) return <span className="text-gray-400">—</span>;
  const cls = v > 0 ? "text-green-600 font-semibold" : v < 0 ? "text-red-500 font-semibold" : "text-gray-600";
  return <span className={cls}>{v > 0 ? "+" : ""}{Number(v).toFixed(1)}%</span>;
}

const ROWS = [
  { label: "Fuente", key: "fuente" },
  { label: "Precio", render: (p) => p.precio_usd ? `USD ${p.precio_usd.toLocaleString("es-AR")}` : "—" },
  { label: "m²", key: "m2_cubiertos", suffix: " m²" },
  { label: "Precio/m²", render: (p) => p.precio_m2 ? `USD ${Math.round(p.precio_m2).toLocaleString()}` : "—" },
  { label: "Dirección", key: "direccion" },
  { label: "Ambientes", key: "ambientes" },
  { label: "Baños", key: "banios" },
  { label: "Balcón", key: "tiene_balcon" },
  { label: "Cochera", key: "tiene_cochera" },
  { divider: true, label: "Análisis IA" },
  { label: "Score", render: (p) => {
    const s = p.analysis?.score_oportunidad;
    if (s == null) return "—";
    const cls = s >= 75 ? "text-green-600" : s >= 50 ? "text-yellow-600" : "text-red-500";
    return <span className={`font-bold text-lg ${cls}`}>{s}/100</span>;
  }},
  { label: "Label", render: (p) => p.analysis?.label || "—" },
  { label: "Recomendación", render: (p) => {
    const r = p.analysis?.recomendacion;
    const cls = { "Comprar": "text-green-600", "Investigar más": "text-yellow-600", "Descartar": "text-red-500" };
    return <span className={`font-semibold ${cls[r] || "text-gray-700"}`}>{r || "—"}</span>;
  }},
  { label: "Descuento vs. mercado", render: (p) => <PctCell v={p.analysis?.descuento_vs_mercado_pct} /> },
  { label: "Potencial revalorización", render: (p) => <PctCell v={p.analysis?.potencial_revalorizacion_pct} /> },
  { label: "ROI estimado", render: (p) => <PctCell v={p.analysis?.roi_estimado_pct} /> },
  { label: "Reforma estimada", render: (p) => p.analysis?.costo_reforma_estimado_usd ? `USD ${p.analysis.costo_reforma_estimado_usd}` : "—" },
  { label: "Plazo estimado", render: (p) => p.analysis?.plazo_estimado_meses ? `${p.analysis.plazo_estimado_meses} meses` : "—" },
  { label: "Resumen", render: (p) => <span className="text-xs text-gray-600 italic">{p.analysis?.resumen || "—"}</span> },
];

export default function Comparator({ properties, onRemove, onClose }) {
  if (!properties.length) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-8 px-4 pb-8 overflow-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-lg text-gray-900">⚖️ Comparador de propiedades</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left p-4 w-40 font-semibold text-gray-500 text-xs uppercase tracking-wide">
                  Campo
                </th>
                {properties.map((p, i) => (
                  <th key={i} className="p-4 text-left min-w-[200px]">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-gray-800 text-sm line-clamp-2 leading-snug">{p.titulo}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{p.barrio} · {p.fuente === "zonaprop" ? "ZonaProp" : "MercadoLibre"}</p>
                      </div>
                      <button
                        onClick={() => onRemove(p)}
                        className="text-gray-300 hover:text-red-400 flex-shrink-0"
                        title="Quitar"
                      >×</button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, ri) =>
                row.divider ? (
                  <tr key={ri} className="bg-gray-50">
                    <td colSpan={properties.length + 1} className="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-widest">
                      {row.label}
                    </td>
                  </tr>
                ) : (
                  <tr key={ri} className="border-b border-gray-50 hover:bg-gray-50/50">
                    <td className="px-4 py-3 text-xs font-medium text-gray-500">{row.label}</td>
                    {properties.map((p, pi) => (
                      <td key={pi} className="px-4 py-3 text-sm text-gray-800">
                        {row.render
                          ? row.render(p)
                          : <Val v={row.suffix ? (p[row.key] != null ? `${p[row.key]}${row.suffix}` : null) : p[row.key]} />
                        }
                      </td>
                    ))}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 flex justify-end gap-3 border-t border-gray-100">
          <button onClick={onClose} className="btn-secondary">Cerrar</button>
        </div>
      </div>
    </div>
  );
}
