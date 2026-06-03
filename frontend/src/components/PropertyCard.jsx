import React, { useState } from "react";

function ScoreCircle({ score }) {
  const cls = score >= 75 ? "score-green" : score >= 50 ? "score-yellow" : "score-red";
  return (
    <div className={`score-circle ${cls}`}>
      {score}
    </div>
  );
}

function RecomendacionBadge({ rec }) {
  const styles = {
    "Comprar": "bg-green-100 text-green-800",
    "Investigar más": "bg-yellow-100 text-yellow-800",
    "Descartar": "bg-red-100 text-red-800",
  };
  return (
    <span className={`badge ${styles[rec] || "bg-gray-100 text-gray-700"}`}>
      {rec}
    </span>
  );
}

function FmtUSD({ value }) {
  if (!value && value !== 0) return <span className="text-gray-400">—</span>;
  return <span>USD {Number(value).toLocaleString("es-AR")}</span>;
}

function Pct({ value, invert = false }) {
  if (value == null) return <span className="text-gray-400">—</span>;
  const positive = invert ? value < 0 : value > 0;
  return (
    <span className={positive ? "text-green-600 font-semibold" : value === 0 ? "text-gray-500" : "text-red-500 font-semibold"}>
      {value > 0 ? "+" : ""}{Number(value).toFixed(1)}%
    </span>
  );
}

export default function PropertyCard({ property, selected, onToggleSelect }) {
  const [expanded, setExpanded] = useState(false);
  const a = property.analysis || {};

  return (
    <div className={`card p-5 flex flex-col gap-4 ${selected ? "ring-2 ring-sky-500" : ""}`}>
      {/* Header */}
      <div className="flex gap-4 items-start">
        <ScoreCircle score={a.score_oportunidad ?? 0} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {a.label && (
              <span className="badge bg-sky-50 text-sky-700">{a.label}</span>
            )}
            {a.recomendacion && <RecomendacionBadge rec={a.recomendacion} />}
            {property.cached && (
              <span className="badge bg-gray-100 text-gray-500 text-[10px]">
                📦 caché {property.cached_at ? new Date(property.cached_at).toLocaleDateString("es-AR") : ""}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-sm text-gray-800 leading-snug line-clamp-2">
            {property.titulo}
          </h3>
          {property.direccion && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">📍 {property.direccion}</p>
          )}
        </div>
      </div>

      {/* Price metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-xl p-3 text-center">
          <p className="text-xs text-gray-500 mb-0.5">Precio</p>
          <p className="font-bold text-sm text-gray-900">
            <FmtUSD value={property.precio_usd} />
          </p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3 text-center">
          <p className="text-xs text-gray-500 mb-0.5">m²</p>
          <p className="font-bold text-sm text-gray-900">
            {property.m2_cubiertos ? `${property.m2_cubiertos} m²` : "—"}
          </p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3 text-center">
          <p className="text-xs text-gray-500 mb-0.5">USD/m²</p>
          <p className="font-bold text-sm text-gray-900">
            {property.precio_m2 ? `$${Math.round(property.precio_m2).toLocaleString()}` : "—"}
          </p>
        </div>
      </div>

      {/* AI metrics */}
      {a.score_oportunidad != null && (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <span className="text-gray-500">Descuento vs. mercado</span>
            <Pct value={a.descuento_vs_mercado_pct} />
          </div>
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <span className="text-gray-500">Potencial revalor.</span>
            <Pct value={a.potencial_revalorizacion_pct} />
          </div>
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <span className="text-gray-500">ROI estimado</span>
            <Pct value={a.roi_estimado_pct} />
          </div>
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <span className="text-gray-500">Plazo</span>
            <span className="font-medium">{a.plazo_estimado_meses ? `${a.plazo_estimado_meses} meses` : "—"}</span>
          </div>
          <div className="flex justify-between items-center col-span-2">
            <span className="text-gray-500">Reforma estimada</span>
            <span className="font-medium text-gray-800">USD {a.costo_reforma_estimado_usd || "—"}</span>
          </div>
        </div>
      )}

      {/* Alertas */}
      {a.alertas && a.alertas.length > 0 && (
        <div className="space-y-1">
          {a.alertas.map((alert, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-1.5">
              <span className="mt-0.5 flex-shrink-0">⚠️</span>
              <span>{alert}</span>
            </div>
          ))}
        </div>
      )}

      {/* Resumen */}
      {a.resumen && (
        <p className="text-xs text-gray-600 leading-relaxed italic border-l-2 border-sky-200 pl-3">
          {a.resumen}
        </p>
      )}

      {/* Expandable: ventajas / desventajas */}
      {(a.ventajas?.length > 0 || a.desventajas?.length > 0) && (
        <div>
          <button
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? "▲ Ocultar detalles" : "▼ Ver ventajas y desventajas"}
          </button>
          {expanded && (
            <div className="mt-3 grid grid-cols-2 gap-3">
              {a.ventajas?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-green-700 mb-1.5">✅ Ventajas</p>
                  <ul className="space-y-1">
                    {a.ventajas.map((v, i) => (
                      <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                        <span className="text-green-500 flex-shrink-0">•</span>{v}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {a.desventajas?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-red-700 mb-1.5">❌ Desventajas</p>
                  <ul className="space-y-1">
                    {a.desventajas.map((v, i) => (
                      <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                        <span className="text-red-400 flex-shrink-0">•</span>{v}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1 border-t border-gray-100">
        <a
          href={property.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary text-xs flex-1 justify-center"
        >
          🔗 Ver publicación
        </a>
        <button
          className={`btn-secondary text-xs px-3 ${selected ? "bg-sky-50 border-sky-300 text-sky-700" : ""}`}
          onClick={() => onToggleSelect(property)}
          title={selected ? "Quitar del comparador" : "Agregar al comparador"}
        >
          {selected ? "✓ Comparando" : "⚖️ Comparar"}
        </button>
        <span className={`badge self-center text-[10px] ${
          property.fuente === "zonaprop"
            ? "bg-blue-50 text-blue-700"
            : "bg-orange-50 text-orange-700"
        }`}>
          {property.fuente === "zonaprop" ? "ZP" : "ML"}
        </span>
      </div>
    </div>
  );
}
