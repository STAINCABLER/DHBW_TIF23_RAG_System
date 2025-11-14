from flask import session
from util import user




def is_user_logged_in() -> bool:
    if "user_id" not in session.keys():
        return False

    user_id: str = session["user_id"]

    current_user: user.User = user.get_user_from_user_id(user_id)

    if not current_user:
        return False

    return True


def get_user_from_session() -> user.User:
    if "user_id" not in session:
        return None
    user_id: str = session["user_id"]

    current_user: user.User = user.get_user_from_user_id(user_id)

    return current_user
