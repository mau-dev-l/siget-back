import json


def rows_to_geojson(rows, geom_col="geom"):
    features = []
    for row in rows:
        row_dict = dict(row) 
        if geom_col in row_dict and isinstance(row_dict[geom_col], str):
            geometry = json.loads(row_dict.pop(geom_col))
        elif geom_col in row_dict:
            geometry = row_dict.pop(geom_col)
        else:
            geometry = None

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": row_dict,
            "id": row_dict.get("id") or row_dict.get("gid")
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
