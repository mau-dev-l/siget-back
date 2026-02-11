import json

def rows_to_geojson(rows, geom_col="geom"):
    features = []
    for row in rows:
        # row ya es un dict gracias al RealDictCursor
        if geom_col in row:
            geom_raw = row.pop(geom_col)
            try:
                # Si viene de ST_AsGeoJSON en el SQL, es un string
                geometry = json.loads(geom_raw) if isinstance(geom_raw, str) else geom_raw
            except:
                geometry = None
        else:
            geometry = None

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": row,
            "id": row.get("id") or row.get("gid")
        })
    return {"type": "FeatureCollection", "features": features}

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
