import json

def rows_to_geojson(rows, geom_col="geom"):
    """
    Transforma filas de SQLAlchemy (Mappings) a un estándar GeoJSON.
    """
    if not rows:
        return {"type": "FeatureCollection", "features": []}

    features = []
    for row in rows:
        # CORRECCIÓN: 'row' ya es un mapeo por el uso de result.mappings()
        # Creamos una copia para poder extraer la geometría sin afectar el original
        row_dict = dict(row) 
        
        if geom_col in row_dict:
            raw_geom = row_dict.pop(geom_col)
            if isinstance(raw_geom, str):
                try:
                    # Parseamos el string JSON que devuelve ST_AsGeoJSON
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

def generar_consulta_geojson(tabla: str, limite: int = None):
    # Esta función se mantiene igual ya que solo genera el SQL string
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