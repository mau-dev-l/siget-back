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