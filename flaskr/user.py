from flaskr.db import get_db

def user_by_username(username):
    db = get_db()

    user = db.execute(
        'SELECT id, username, password FROM user WHERE username = ?', (username,)
        ).fetchone()
    return user