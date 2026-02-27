from db.connection import execute_read_one

def get_user_by_username(username: str):
    query = """
        SELECT id, username, password, role
        FROM users
        WHERE username = %(username)s
        LIMIT 1
    """
    return execute_read_one(query, {"username": username}, use_pool2=True)