from flaskr.db import get_db

def user_by_username(username):
    """Helper function that returns a user based in their username. If user not exists will return none"""

    db = get_db()

    user = db.execute(
        'SELECT id, username, password FROM user WHERE username = ?', (username,)
        ).fetchone()
    return user