import flask

import database.postgres
import database.redis
import util.file
import util.user

debug_blueprint: flask.Blueprint = flask.Blueprint("debug", "debug", url_prefix="/debug")


@debug_blueprint.get("/")
def get_debug_page():
    return (
        "<style>"
            "a {"
                "font-size: 40px;"
                "color: white;"
            "}"
            "body {"
                "background-color: #111;"
                "color: white;"
                "padding: 100px;"
            "}"
        "</style>"
        "<a href='/debug/users'>Users</a>"
        "<br>"
        "<a href='/debug/sessions'>Sessions</a>"
        "<br>"
        "<a href='/debug/files'>Files</a>"
    ), 200


@debug_blueprint.get("/users")
def get_all_users():
    users: list[util.user.User] = util.user.User.get_all_users()
    return [
        user.to_dict()
        for user in users
    ], 200

@debug_blueprint.get("/sessions")
def get_all_sessions():
    with database.redis.open_session() as redis_session:
        keys = redis_session.keys()
        raw_values: list[dict[bytes, bytes]] = [
            redis_session.hgetall(key.decode())
            for key in keys
        ]
    values = [
        {
            key.decode(): value.decode()
            for key, value in raw_val.items()
        }
        for raw_val in raw_values
    ]
    return values, 200

@debug_blueprint.get("/files")
def get_all_uploaded_files():
    raw_result: list[dict[str, any]] = database.postgres.fetch_all(
        "SELECT * FROM uploaded_files"
    )
    uploaded_files: list[util.file.UploadedFile] = [
        util.file.UploadedFile.from_dict(file)
        for file in raw_result
    ]

    dict_files: list[dict[str, any]] = [
        file.to_dict()
        for file in uploaded_files
    ]
    return dict_files, 200
