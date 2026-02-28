from models.comment_model import create_comment, get_comments_by_feature
from fastapi import HTTPException


def add_comment(feature_id: str, content: str):

    if not content.strip():
        raise HTTPException(status_code=400, detail="Comentario vacío")

    comment_id = create_comment(feature_id, content)

    return {
        "message": "Comentario guardado",
        "comment_id": comment_id
    }


def list_comments(feature_id: str):
    return get_comments_by_feature(feature_id)