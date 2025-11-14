from flask import Blueprint, request, session
from util import user, session_management



account: Blueprint = Blueprint("accounts", __name__, url_prefix="/accounts")


@account.post("/login")
def login() -> tuple[str, int]:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        matched_user: user.User = user.match_user(username, password)

        session.clear()

        if not matched_user:
            return "Invalid credentials", 400

        session["user_id"] = str(matched_user.user_id)

        return "Valid credentials", 200

@account.post("/register")
def register() -> tuple[dict[str, str], int]:
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        new_user: user.User = user.create_user(username, password)

        if not new_user:
            return "Username is already in use! Sorry :(", 400

        new_user_dict: dict[str, any] = new_user.to_dict()

        del new_user_dict["password"]

        return new_user_dict, 200


@account.route("/logout")
def logout() -> tuple[dict[str, str], int]:
    if not session_management.is_user_logged_in():
        return "", 401
    session.clear()
    return "Successfully logged out!", 200

@account.route("/")
def get_user_data() -> tuple[dict[str, str], int]:
    if not session_management.is_user_logged_in():
        return "", 401
    current_user: user.User = session_management.get_user_from_session()

    user_as_dict: dict[str, any] = current_user.to_dict()

    del user_as_dict["password"]
    return user_as_dict, 200
