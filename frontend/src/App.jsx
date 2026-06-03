import React, { useState, useRef } from "react";
import axios from "axios";
import SearchForm from "./components/SearchForm";
import Dashboard from "./components/Dashboard";
import Comparator from "./components/Comparator";

const API = "/api";
const POLL_MS = 2500;

export default function App() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [properties, setProperties] = useState(null);
  const [selected, setSelected] = useState([]);
  const [showComparator, setShowComparator] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const handleSearch = async (form) => {
    setLoading(true);
    setProperties(null);
    setError(null);
    setProgress(0);
    setMessage("Iniciando búsqueda...");
    setSelected([]);

    try {
      const { data } = await axios.post(`${API}/search`, form);
      const taskId = data.task_id;
      pollRef.current = setInterval(async () => {
        try {
          const { data: status } = await axios.get(`${API}/search/${taskId}`);
          setProgress(status.progress || 0);
          setMessage(status.message || "");

          if (status.status === "done") {
            clearInterval(pollRef.current);
            setProperties(status.results || []);
            setLoading(false);
          } else if (status.status === "error") {
            clearInterval(pollRef.current);
            setError(status.error || "Error inesperado");
            setLoading(false);
          }
        } catch (err) {
          clearInterval(pollRef.current);
          setError("Error al obtener resultados");
          setLoading(false);
        }
      }, POLL_MS);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al iniciar la búsqueda");
      setLoading(false);
    }
  };

  const handleToggleSelect = (prop) => {
    setSelected((prev) => {
      const exists = prev.some((p) => p.url === prop.url);
      if (exists) return prev.filter((p) => p.url !== prop.url);
      if (prev.length >= 3) return prev; // max 3
      return [...prev, prop];
    });
  };

  const handleExport = async () => {
    window.open(`${API}/export/csv`, "_blank");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-40 shadow-sm">
        <div className="max-w-screen-2xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏠</span>
            <div>
              <h1 className="font-bold text-gray-900 text-lg leading-tight">Flipping BA</h1>
              <p className="text-xs text-gray-400">Oportunidades inmobiliarias CABA · Powered by Claude AI</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {selected.length >= 2 && (
              <button
                className="btn-primary"
                onClick={() => setShowComparator(true)}
              >
                ⚖️ Comparar {selected.length}
              </button>
            )}
            {properties && properties.length > 0 && (
              <button className="btn-secondary" onClick={handleExport}>
                📥 Exportar CSV
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 flex gap-6">
        {/* Sidebar */}
        <aside className="w-72 flex-shrink-0 space-y-4">
          <SearchForm onSearch={handleSearch} loading={loading} />

          {/* Info card */}
          <div className="card p-4 space-y-3 text-xs text-gray-500">
            <p className="font-semibold text-gray-700 text-sm">¿Cómo funciona?</p>
            <div className="space-y-2">
              <div className="flex gap-2">
                <span>1️⃣</span>
                <span>Scrapea ZonaProp y MercadoLibre en tiempo real</span>
              </div>
              <div className="flex gap-2">
                <span>2️⃣</span>
                <span>Claude AI analiza cada propiedad y calcula ROI, reforma y oportunidad</span>
              </div>
              <div className="flex gap-2">
                <span>3️⃣</span>
                <span>Resultados guardados 24hs en caché local</span>
              </div>
            </div>
          </div>

          {selected.length > 0 && (
            <div className="card p-4">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                Seleccionadas para comparar ({selected.length}/3)
              </p>
              <div className="space-y-2">
                {selected.map((p) => (
                  <div key={p.url} className="flex items-center gap-2 text-xs">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      (p.analysis?.score_oportunidad ?? 0) >= 75 ? "bg-green-500" :
                      (p.analysis?.score_oportunidad ?? 0) >= 50 ? "bg-yellow-500" : "bg-red-500"
                    }`}></span>
                    <span className="text-gray-600 truncate flex-1">{p.titulo?.slice(0, 40) || "Propiedad"}</span>
                    <button
                      className="text-gray-400 hover:text-red-400"
                      onClick={() => handleToggleSelect(p)}
                    >×</button>
                  </div>
                ))}
              </div>
              {selected.length >= 2 && (
                <button
                  className="btn-primary w-full justify-center mt-3 text-xs py-2"
                  onClick={() => setShowComparator(true)}
                >
                  ⚖️ Comparar
                </button>
              )}
            </div>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4 flex gap-3 items-start">
              <span className="text-red-500 text-lg flex-shrink-0">⚠️</span>
              <div>
                <p className="font-semibold text-red-800 text-sm">Error en la búsqueda</p>
                <p className="text-red-600 text-xs mt-0.5">{error}</p>
              </div>
              <button
                className="ml-auto text-red-400 hover:text-red-600"
                onClick={() => setError(null)}
              >×</button>
            </div>
          )}

          <Dashboard
            properties={properties}
            loading={loading}
            progress={progress}
            message={message}
            selected={selected}
            onToggleSelect={handleToggleSelect}
          />
        </main>
      </div>

      {/* Comparator modal */}
      {showComparator && selected.length >= 2 && (
        <Comparator
          properties={selected}
          onRemove={handleToggleSelect}
          onClose={() => setShowComparator(false)}
        />
      )}
    </div>
  );
}
