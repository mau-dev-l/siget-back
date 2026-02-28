from fastapi import APIRouter
from pydantic import BaseModel
from services.comment_service import add_comment, list_comments

router = APIRouter(prefix="/comentarios", tags=["comentarios"])


class CommentCreate(BaseModel):
    feature_id: str
    content: str


@router.post("/")
def create_comment_endpoint(data: CommentCreate):
    return add_comment(
        feature_id=data.feature_id,
        content=data.content
    )


@router.get("/{feature_id}")
def get_comments(feature_id: str):
    return list_comments(feature_id)