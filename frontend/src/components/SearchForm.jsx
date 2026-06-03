import React, { useState } from "react";

const BARRIOS = [
  "Belgrano", "Palermo", "Recoleta", "Caballito", "Núñez",
  "Villa Crespo", "Almagro", "San Telmo", "Barracas", "Devoto",
];

const TIPOS = [
  "Departamento 2 amb",
  "Departamento 3 amb",
  "PH",
];

export default function SearchForm({ onSearch, loading }) {
  const [form, setForm] = useState({
    barrio: "Belgrano",
    tipo_propiedad: "Departamento 2 amb",
    presupuesto_max_usd: 120000,
    fuente: "ambas",
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch({ ...form, presupuesto_max_usd: Number(form.presupuesto_max_usd) });
  };

  return (
    <form onSubmit={handleSubmit} className="card p-6 space-y-5">
      <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
        <span className="text-xl">🔍</span> Configurar búsqueda
      </h2>

      <div>
        <label className="label">Barrio</label>
        <select
          className="input"
          value={form.barrio}
          onChange={(e) => set("barrio", e.target.value)}
        >
          {BARRIOS.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Tipo de propiedad</label>
        <select
          className="input"
          value={form.tipo_propiedad}
          onChange={(e) => set("tipo_propiedad", e.target.value)}
        >
          {TIPOS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">Presupuesto máximo (USD)</label>
        <div className="relative">
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 font-semibold text-sm">
            USD
          </span>
          <input
            type="number"
            min={10000}
            max={2000000}
            step={5000}
            className="input pl-12"
            value={form.presupuesto_max_usd}
            onChange={(e) => set("presupuesto_max_usd", e.target.value)}
            required
          />
        </div>
      </div>

      <div>
        <label className="label">Fuente</label>
        <div className="flex gap-2">
          {[
            { v: "zonaprop", label: "ZonaProp" },
            { v: "mercadolibre", label: "MercadoLibre" },
            { v: "ambas", label: "Ambas" },
          ].map(({ v, label }) => (
            <button
              key={v}
              type="button"
              onClick={() => set("fuente", v)}
              className={`flex-1 py-2 text-xs font-semibold rounded-xl border transition-colors duration-150 ${
                form.fuente === v
                  ? "bg-sky-600 text-white border-sky-600"
                  : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
        {loading ? (
          <>
            <div className="spinner" />
            Buscando...
          </>
        ) : (
          <>🏠 Buscar oportunidades</>
        )}
      </button>
    </form>
  );
}
