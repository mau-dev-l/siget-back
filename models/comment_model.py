from db.connection import execute_write_query, execute_read_query


def create_comment(feature_id: str, content: str):
    query = """
        INSERT INTO comments (feature_id, content)
        VALUES (%(feature_id)s, %(content)s)
        RETURNING id;
    """

    return execute_write_query(query, {
        "feature_id": feature_id,
        "content": content
    })


def get_comments_by_feature(feature_id: str):
    query = """
        SELECT id, content, created_at
        FROM comments
        WHERE feature_id = %(feature_id)s
        ORDER BY created_at DESC;
    """

    return execute_read_query(query, {
        "feature_id": feature_id
    })