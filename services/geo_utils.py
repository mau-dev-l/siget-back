import json

def rows_to_geojson(rows, geom_col="geom"):
    """
    Convierte resultados de la BD a GeoJSON estándar.
    Maneja casos donde no hay resultados para evitar errores en el Frontend.
    """
    if not rows:
        return {"type": "FeatureCollection", "features": []}

    features = []
    for row in rows:
        # Ya que usamos RealDictCursor, 'row' ya es un diccionario
        row_dict = dict(row) 
        
        try:
            # 1. Extraer y parsear la geometría
            geom_data = row_dict.pop(geom_col, None)
            
            if geom_data:
                # Si viene de ST_AsGeoJSON es un string, si no, podría ser ya un dict
                geometry = json.loads(geom_data) if isinstance(geom_data, str) else geom_data
            else:
                geometry = None
                
            # 2. Construir el Feature
            features.append({
                "type": "Feature",
                "geometry": geometry,
                "properties": row_dict,
                "id": row_dict.get("id") or row_dict.get("gid") or row_dict.get("cvegeo")
            })
        except Exception as e:
            print(f"Error parseando fila a GeoJSON: {e}")
            continue

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
