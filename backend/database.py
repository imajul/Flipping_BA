import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "flipping_ba.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            titulo TEXT,
            precio_usd REAL,
            m2_cubiertos REAL,
            precio_m2 REAL,
            direccion TEXT,
            descripcion TEXT,
            antiguedad TEXT,
            expensas TEXT,
            piso TEXT,
            ambientes INTEGER,
            banios INTEGER,
            tiene_balcon INTEGER DEFAULT 0,
            tiene_cochera INTEGER DEFAULT 0,
            amenities TEXT,
            fuente TEXT,
            barrio TEXT,
            tipo_propiedad TEXT,
            analysis_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_cached_property(url: str, max_age_hours: int = 24) -> Optional[dict]:
    conn = get_connection()
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    row = conn.execute(
        "SELECT * FROM properties WHERE url = ? AND created_at > ? AND analysis_json IS NOT NULL",
        (url, cutoff),
    ).fetchone()
    conn.close()
    if row:
        data = dict(row)
        if data.get("analysis_json"):
            data["analysis"] = json.loads(data["analysis_json"])
        data["cached"] = True
        data["cached_at"] = data["created_at"]
        data["tiene_balcon"] = bool(data.get("tiene_balcon"))
        data["tiene_cochera"] = bool(data.get("tiene_cochera"))
        return data
    return None


def save_property(prop: dict, analysis: dict):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO properties (
                url, titulo, precio_usd, m2_cubiertos, precio_m2,
                direccion, descripcion, antiguedad, expensas, piso,
                ambientes, banios, tiene_balcon, tiene_cochera, amenities,
                fuente, barrio, tipo_propiedad, analysis_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                prop.get("url"),
                prop.get("titulo"),
                prop.get("precio_usd"),
                prop.get("m2_cubiertos"),
                prop.get("precio_m2"),
                prop.get("direccion"),
                prop.get("descripcion"),
                prop.get("antiguedad"),
                prop.get("expensas"),
                prop.get("piso"),
                prop.get("ambientes"),
                prop.get("banios"),
                1 if prop.get("tiene_balcon") else 0,
                1 if prop.get("tiene_cochera") else 0,
                prop.get("amenities"),
                prop.get("fuente"),
                prop.get("barrio"),
                prop.get("tipo_propiedad"),
                json.dumps(analysis),
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving property: {e}")
    finally:
        conn.close()


def get_all_properties(barrio: str = None, tipo: str = None) -> List[dict]:
    conn = get_connection()
    query = "SELECT * FROM properties WHERE analysis_json IS NOT NULL"
    params = []
    if barrio:
        query += " AND barrio = ?"
        params.append(barrio)
    if tipo:
        query += " AND tipo_propiedad = ?"
        params.append(tipo)
    query += " ORDER BY created_at DESC LIMIT 200"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for row in rows:
        data = dict(row)
        if data.get("analysis_json"):
            data["analysis"] = json.loads(data["analysis_json"])
        data["cached"] = True
        data["cached_at"] = data["created_at"]
        data["tiene_balcon"] = bool(data.get("tiene_balcon"))
        data["tiene_cochera"] = bool(data.get("tiene_cochera"))
        result.append(data)
    return result
