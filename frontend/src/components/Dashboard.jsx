import React from "react";
import PropertyCard from "./PropertyCard";

export default function Dashboard({ properties, loading, progress, message, selected, onToggleSelect }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-sky-100"></div>
          <div className="w-20 h-20 rounded-full border-4 border-sky-500 border-t-transparent animate-spin absolute inset-0"></div>
        </div>
        <div className="text-center space-y-2 max-w-sm">
          <p className="font-semibold text-gray-800">{message || "Buscando propiedades..."}</p>
          {progress > 0 && (
            <div className="w-64 bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 bg-sky-500 rounded-full progress-bar"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
          {progress > 0 && (
            <p className="text-xs text-gray-400">{progress}% completado</p>
          )}
        </div>
        <div className="flex gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span> Scrapeando ZonaProp
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse delay-300"></span> MercadoLibre
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse delay-700"></span> Analizando con IA
          </span>
        </div>
      </div>
    );
  }

  if (!properties) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <div className="text-6xl">🏢</div>
        <div>
          <p className="text-xl font-bold text-gray-800">Encontrá oportunidades de flipping</p>
          <p className="text-gray-500 mt-1 text-sm max-w-sm">
            Configurá tu búsqueda y dejá que la IA analice cada propiedad: descuento vs. mercado, ROI estimado, costo de reforma y más.
          </p>
        </div>
        <div className="flex gap-4 mt-2 text-sm text-gray-400">
          <span>🤖 Análisis con Claude AI</span>
          <span>📊 Score de oportunidad</span>
          <span>💾 Caché 24hs</span>
        </div>
      </div>
    );
  }

  if (properties.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
        <div className="text-5xl">🔍</div>
        <div>
          <p className="text-lg font-bold text-gray-800">No se encontraron propiedades</p>
          <p className="text-gray-500 text-sm mt-1">
            Probá aumentando el presupuesto máximo o cambiando el barrio.
          </p>
        </div>
      </div>
    );
  }

  const alta = properties.filter((p) => (p.analysis?.score_oportunidad ?? 0) >= 75);
  const media = properties.filter((p) => {
    const s = p.analysis?.score_oportunidad ?? 0;
    return s >= 50 && s < 75;
  });
  const baja = properties.filter((p) => (p.analysis?.score_oportunidad ?? 0) < 50);

  return (
    <div className="space-y-6">
      {/* Summary bar */}
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-sm font-semibold text-gray-700">
          {properties.length} propiedades analizadas
        </span>
        <div className="flex gap-2">
          {alta.length > 0 && (
            <span className="badge bg-green-100 text-green-800">{alta.length} alta oportunidad</span>
          )}
          {media.length > 0 && (
            <span className="badge bg-yellow-100 text-yellow-800">{media.length} oportunidad media</span>
          )}
          {baja.length > 0 && (
            <span className="badge bg-red-100 text-red-800">{baja.length} riesgo alto</span>
          )}
        </div>
        {selected.length > 0 && (
          <span className="badge bg-sky-100 text-sky-700 ml-auto">
            {selected.length} seleccionada{selected.length > 1 ? "s" : ""} para comparar
          </span>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-5">
        {properties.map((p, i) => (
          <PropertyCard
            key={p.url || i}
            property={p}
            selected={selected.some((s) => s.url === p.url)}
            onToggleSelect={onToggleSelect}
          />
        ))}
      </div>
    </div>
  );
}
