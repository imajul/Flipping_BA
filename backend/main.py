import asyncio
import csv
import io
import json
import uuid
from typing import Dict, List

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import SearchRequest, SearchStatus, PropertyResult
from database import init_db, get_cached_property, save_property, get_all_properties
from scraper import scrape_zonaprop, scrape_mercadolibre, get_precio_ref_m2
from analyzer import analyze_property, get_fallback_analysis

app = FastAPI(title="Flipping BA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store
tasks: Dict[str, dict] = {}


@app.on_event("startup")
def startup():
    init_db()


# ── Search ────────────────────────────────────────────────────────────────────

@app.post("/api/search", response_model=dict)
async def start_search(req: SearchRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Iniciando búsqueda...",
        "results": None,
        "error": None,
    }
    background_tasks.add_task(run_search, task_id, req)
    return {"task_id": task_id}


@app.get("/api/search/{task_id}", response_model=SearchStatus)
def get_search_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return SearchStatus(task_id=task_id, **task)


async def run_search(task_id: str, req: SearchRequest):
    def update(status: str, progress: int, message: str):
        tasks[task_id].update({"status": status, "progress": progress, "message": message})

    try:
        update("running", 5, "Obteniendo precio de referencia del mercado...")

        # Get market reference price
        precio_ref = await get_precio_ref_m2(req.barrio)

        update("running", 15, f"Precio de referencia {req.barrio}: USD {precio_ref:,.0f}/m²")

        raw_properties = []

        # Scrape ZonaProp
        if req.fuente in ("zonaprop", "ambas"):
            update("running", 20, f"Scrapeando ZonaProp — {req.barrio}...")
            try:
                zp_props, zp_ref = await scrape_zonaprop(
                    req.barrio, req.tipo_propiedad, req.presupuesto_max_usd
                )
                if zp_ref:
                    precio_ref = zp_ref
                raw_properties.extend(zp_props)
                update("running", 40, f"ZonaProp: {len(zp_props)} propiedades encontradas")
            except Exception as e:
                update("running", 40, f"ZonaProp error: {str(e)[:100]} — continuando con MercadoLibre")

        # Scrape MercadoLibre
        if req.fuente in ("mercadolibre", "ambas"):
            update("running", 45, f"Scrapeando MercadoLibre — {req.barrio}...")
            try:
                ml_props = await scrape_mercadolibre(
                    req.barrio, req.tipo_propiedad, req.presupuesto_max_usd
                )
                raw_properties.extend(ml_props)
                update("running", 60, f"MercadoLibre: {len(ml_props)} propiedades encontradas")
            except Exception as e:
                update("running", 60, f"MercadoLibre error: {str(e)[:100]}")

        if not raw_properties:
            tasks[task_id].update({
                "status": "done",
                "progress": 100,
                "message": "No se encontraron propiedades con los filtros aplicados.",
                "results": [],
            })
            return

        # Deduplicate by URL
        seen_urls = set()
        unique_props = []
        for p in raw_properties:
            if p["url"] not in seen_urls:
                seen_urls.add(p["url"])
                unique_props.append(p)

        total = len(unique_props)
        update("running", 62, f"Analizando {total} propiedades con IA...")

        results: List[dict] = []
        for i, prop in enumerate(unique_props):
            pct = 62 + int((i / total) * 35)
            update("running", pct, f"Analizando propiedad {i + 1}/{total}: {prop.get('titulo', '')[:50]}")

            # Check cache first
            cached = get_cached_property(prop["url"])
            if cached:
                cached["cached"] = True
                results.append(cached)
                continue

            # Analyze with Claude
            try:
                analysis = analyze_property(prop, precio_ref)
            except Exception as e:
                print(f"Analysis error for {prop['url']}: {e}")
                analysis = get_fallback_analysis(prop, precio_ref)

            save_property(prop, analysis)
            prop["analysis"] = analysis
            prop["cached"] = False
            results.append(prop)

            # Respect rate limits
            await asyncio.sleep(0.3)

        # Sort by score
        results.sort(key=lambda x: (x.get("analysis") or {}).get("score_oportunidad", 0), reverse=True)

        tasks[task_id].update({
            "status": "done",
            "progress": 100,
            "message": f"Análisis completo: {len(results)} propiedades encontradas",
            "results": results,
        })

    except Exception as e:
        tasks[task_id].update({
            "status": "error",
            "progress": 0,
            "message": "Error inesperado",
            "error": str(e),
        })
        raise


# ── Cached properties ─────────────────────────────────────────────────────────

@app.get("/api/properties")
def list_properties(barrio: str = None, tipo: str = None):
    return get_all_properties(barrio, tipo)


# ── Export CSV ────────────────────────────────────────────────────────────────

@app.get("/api/export/csv")
def export_csv(barrio: str = None, tipo: str = None):
    props = get_all_properties(barrio, tipo)
    if not props:
        raise HTTPException(status_code=404, detail="No hay propiedades para exportar")

    output = io.StringIO()
    fieldnames = [
        "titulo", "barrio", "tipo_propiedad", "fuente", "precio_usd", "m2_cubiertos",
        "precio_m2", "direccion", "ambientes", "banios", "tiene_balcon", "tiene_cochera",
        "score_oportunidad", "label", "recomendacion", "descuento_vs_mercado_pct",
        "potencial_revalorizacion_pct", "roi_estimado_pct", "costo_reforma_estimado_usd",
        "plazo_estimado_meses", "resumen", "alertas", "url", "cached_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for p in props:
        analysis = p.get("analysis") or {}
        row = {
            "titulo": p.get("titulo"),
            "barrio": p.get("barrio"),
            "tipo_propiedad": p.get("tipo_propiedad"),
            "fuente": p.get("fuente"),
            "precio_usd": p.get("precio_usd"),
            "m2_cubiertos": p.get("m2_cubiertos"),
            "precio_m2": p.get("precio_m2"),
            "direccion": p.get("direccion"),
            "ambientes": p.get("ambientes"),
            "banios": p.get("banios"),
            "tiene_balcon": p.get("tiene_balcon"),
            "tiene_cochera": p.get("tiene_cochera"),
            "score_oportunidad": analysis.get("score_oportunidad"),
            "label": analysis.get("label"),
            "recomendacion": analysis.get("recomendacion"),
            "descuento_vs_mercado_pct": analysis.get("descuento_vs_mercado_pct"),
            "potencial_revalorizacion_pct": analysis.get("potencial_revalorizacion_pct"),
            "roi_estimado_pct": analysis.get("roi_estimado_pct"),
            "costo_reforma_estimado_usd": analysis.get("costo_reforma_estimado_usd"),
            "plazo_estimado_meses": analysis.get("plazo_estimado_meses"),
            "resumen": analysis.get("resumen"),
            "alertas": "; ".join(analysis.get("alertas") or []),
            "url": p.get("url"),
            "cached_at": p.get("cached_at"),
        }
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=flipping_ba_resultados.csv"},
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}
