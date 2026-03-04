import json

def rows_to_geojson(rows, geom_col="geom"):
    """
    Transforma filas de SQLAlchemy (Result) a un estándar GeoJSON.
    """
    if not rows:
        return {"type": "FeatureCollection", "features": []}

    features = []
    for row in rows:
        # En SQLAlchemy Async, row suele ser un objeto Row. 
        # Lo convertimos a dict para mantener tu lógica actual.
        row_dict = dict(row._mapping) 
        
        if geom_col in row_dict:
            raw_geom = row_dict.pop(geom_col)
            if isinstance(raw_geom, str):
                try:
                    geometry = json.loads(raw_geom)
                except:
                    geometry = None
            else:
                geometry = raw_geom
        else:
            geometry = None

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": row_dict,
            "id": row_dict.get("id") or row_dict.get("gid") or row_dict.get("cvegeo")
        })

    return {"type": "FeatureCollection", "features": features}

# Esta función solo genera el string de la consulta, se mantiene igual.
def generar_consulta_geojson(tabla: str, limite: int = None):
    limit_clause = f"LIMIT {limite}" if limite else ""
    return f"""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(
            json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_Transform(t.geom, 4326))::json,
                'properties', to_jsonb(t) - 'geom' 
            )
        ), '[]'::json)
    )
    FROM (SELECT * FROM "{tabla}" {limit_clause}) as t;
    """