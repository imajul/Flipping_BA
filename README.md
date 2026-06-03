# Flipping BA

Aplicación web para analizar oportunidades de flipping inmobiliario en CABA (Buenos Aires).

**Stack:** FastAPI + Playwright + Claude AI + React + Tailwind CSS + SQLite

## Setup

### 1. Variables de entorno

```bash
cp .env.example .env
# Editá .env y pegá tu ANTHROPIC_API_KEY
```

### 2. Backend

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar Chromium para Playwright
playwright install chromium

# Iniciar el servidor
uvicorn backend.main:app --reload
```

El backend queda en `http://localhost:8000`. Docs en `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

La app queda en `http://localhost:5173`.

## Funcionalidades

- **Scraping real** de ZonaProp y MercadoLibre con Playwright
- **Análisis IA** con Claude por cada propiedad: score 0-100, ROI, costo de reforma, recomendación
- **Caché SQLite** de 24hs — no re-scrapea ni re-analiza URLs ya procesadas
- **Comparador** lado a lado de 2-3 propiedades
- **Exportar CSV** con todos los campos

## Notas

- El scraping puede tardar 2-5 minutos dependiendo de cuántas propiedades se encuentren.
- Si ZonaProp o MercadoLibre bloquean el scraper, el sistema continúa con la otra fuente.
- Los precios de referencia del mercado se calculan como la mediana de las primeras 20 propiedades usadas en buen estado del barrio.
