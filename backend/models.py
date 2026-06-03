from pydantic import BaseModel
from typing import Optional, List


class PropertyAnalysis(BaseModel):
    score_oportunidad: int
    label: str
    descuento_vs_mercado_pct: float
    potencial_revalorizacion_pct: float
    costo_reforma_estimado_usd: str
    roi_estimado_pct: float
    plazo_estimado_meses: int
    ventajas: List[str]
    desventajas: List[str]
    alertas: List[str]
    resumen: str
    recomendacion: str


class PropertyData(BaseModel):
    url: str
    titulo: str
    precio_usd: Optional[float] = None
    m2_cubiertos: Optional[float] = None
    precio_m2: Optional[float] = None
    direccion: Optional[str] = None
    descripcion: Optional[str] = None
    antiguedad: Optional[str] = None
    expensas: Optional[str] = None
    piso: Optional[str] = None
    ambientes: Optional[int] = None
    banios: Optional[int] = None
    tiene_balcon: Optional[bool] = None
    tiene_cochera: Optional[bool] = None
    amenities: Optional[str] = None
    fuente: str
    barrio: str
    tipo_propiedad: str


class PropertyResult(PropertyData):
    id: Optional[int] = None
    analysis: Optional[PropertyAnalysis] = None
    cached: bool = False
    cached_at: Optional[str] = None
    created_at: Optional[str] = None


class SearchRequest(BaseModel):
    barrio: str
    tipo_propiedad: str
    presupuesto_max_usd: float
    fuente: str  # "zonaprop" | "mercadolibre" | "ambas"


class SearchStatus(BaseModel):
    task_id: str
    status: str  # "pending" | "running" | "done" | "error"
    progress: int  # 0-100
    message: str
    results: Optional[List[PropertyResult]] = None
    error: Optional[str] = None
