import flask
import hashlib
import util.session_management
import util.user


accounts_blueprint: flask.Blueprint = flask.Blueprint("accounts", "accounts", url_prefix="/accounts")


@accounts_blueprint.get("/")
@util.session_management.requires_session(True)
def get_user(session_token: util.session_management.SessionToken):
    user: util.user.User = session_token.get_user()

    if not user:
        return "User not found!", 404

    return user.to_spare_dict(), 200


@accounts_blueprint.post("/login")
def post_login():
    email: str = flask.request.form.get("email", "").strip()
    password: str = flask.request.form.get("password", "")


    current_session_token: util.session_management.SessionToken | None = util.session_management.SessionToken.get_current_session_token()

    if current_session_token:
        current_session_token.revoke_session_token()

    if not email or not password:
        return "Invalid credentials!", 400

    password_hash: str = hashlib.sha256(password.encode()).hexdigest()

    user: util.user.User = util.user.User.find_user_by_email_and_password_hash(email, password_hash)

    if not user:
        return "Invalid credentials!", 400

    session_token: util.session_management.SessionToken = util.session_management.SessionToken.create_session_token(
        user.id
    )

    user.update_last_login_to_now()

    # Flask option
    flask.session["session_id"] = str(session_token.session_id)

    return "Successfully logged in!", 200

    # Cookie option

    # return flask.Response(
    #     "Successfully logged in!",
    #     200,
    #     {
    #         "Set-Cookie": "SESSION_ID={session_id}; HttpOnly;"
    #     }
    # )

@accounts_blueprint.post("/register")
def post_register():
    email: str = flask.request.form.get("email", "").strip()
    password: str = flask.request.form.get("password", "")


    if not email or not password:
        return "Email and password are required!", 400

    username: str = email.split("@")[0]
    user: util.user.User = util.user.User.create_user(username, email, password, "student")

    if not user:
        return "Email is already taken!", 400

    return "User successfully created!", 201



@accounts_blueprint.route("/logout", methods=["GET", "POST"])
@util.session_management.requires_session(True)
def get_logout(session_token: util.session_management.SessionToken):
    session_token.revoke_session_token()
    flask.session.clear()

    return flask.Response(
        "Successfully logged out",
        200,
        {
            "Set-Cookie": "SESSION_ID=deleted; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
        }
    )