import re
import json
import anthropic
from typing import Optional

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Eres un experto en flipping inmobiliario en Buenos Aires, Argentina, con 15 años de experiencia.
Analizás propiedades para determinar su potencial de compra-reforma-venta.
Respondés SIEMPRE en JSON válido sin markdown."""


def analyze_property(prop: dict, precio_ref_m2: float) -> dict:
    barrio = prop.get("barrio", "CABA")
    precio = prop.get("precio_usd") or 0
    m2 = prop.get("m2_cubiertos") or 0
    precio_m2 = prop.get("precio_m2") or (precio / m2 if m2 > 0 else 0)

    user_prompt = f"""Analizá esta propiedad para flipping en {barrio}, CABA:

Datos de la propiedad:
- Dirección: {prop.get("direccion") or "No especificada"}
- Precio publicado: USD {precio:,.0f}
- Superficie: {m2} m²
- Precio/m²: USD {precio_m2:,.0f}
- Descripción: {prop.get("descripcion") or "Sin descripción"}
- Fuente: {prop.get("fuente", "")}
- URL: {prop.get("url", "")}

Precio de referencia del mercado para departamentos usados en buen estado en {barrio}: USD {precio_ref_m2:,.0f}/m² (dato de ZonaProp al momento de la búsqueda).

Devolvé este JSON exacto:
{{
  "score_oportunidad": <0-100>,
  "label": <"Alta oportunidad" | "Oportunidad media" | "Riesgo alto">,
  "descuento_vs_mercado_pct": <número, puede ser negativo>,
  "potencial_revalorizacion_pct": <estimación post-reforma>,
  "costo_reforma_estimado_usd": <rango bajo-alto como string, ej "15000-25000">,
  "roi_estimado_pct": <ROI neto estimado luego de reforma y gastos>,
  "plazo_estimado_meses": <meses estimados para completar la operación>,
  "ventajas": [<lista de strings, aspectos positivos concretos>],
  "desventajas": [<lista de strings, aspectos negativos concretos>],
  "alertas": [<lista de strings, red flags si los hay>],
  "resumen": <2-3 oraciones de análisis narrativo>,
  "recomendacion": <"Comprar", "Investigar más" o "Descartar">
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text.strip()
    # Strip markdown fences if present
    response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
    response_text = re.sub(r"\s*```$", "", response_text)

    return json.loads(response_text)


def get_fallback_analysis(prop: dict, precio_ref_m2: float) -> dict:
    precio = prop.get("precio_usd") or 0
    m2 = prop.get("m2_cubiertos") or 1
    precio_m2 = prop.get("precio_m2") or (precio / m2)
    descuento = ((precio_ref_m2 - precio_m2) / precio_ref_m2 * 100) if precio_ref_m2 > 0 else 0

    return {
        "score_oportunidad": 50,
        "label": "Oportunidad media",
        "descuento_vs_mercado_pct": round(descuento, 1),
        "potencial_revalorizacion_pct": 15.0,
        "costo_reforma_estimado_usd": "10000-20000",
        "roi_estimado_pct": 10.0,
        "plazo_estimado_meses": 6,
        "ventajas": ["Precio por debajo del mercado" if descuento > 0 else "Precio de mercado"],
        "desventajas": ["Análisis automático — verificar presencialmente"],
        "alertas": ["No se pudo analizar con IA — resultado estimado"],
        "resumen": "Análisis estimado automáticamente. Se recomienda verificar la propiedad presencialmente antes de tomar decisiones.",
        "recomendacion": "Investigar más",
    }
