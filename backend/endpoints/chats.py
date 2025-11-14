from flask import Blueprint, request, session
from util import user, chat, session_management



chat_blueprint: Blueprint = Blueprint("chats", __name__, url_prefix="/chats")


@chat_blueprint.get("/")
def get_all_chats() -> list[dict[str, any]]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    return current_user.get_raw_chats_as_list(), 200


@chat_blueprint.get("/<chat_id>")
def get_chat(chat_id: str = "he") -> dict[str, any]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    current_chat: chat.Chat = current_user.get_chat_from_chat_id(chat_id)

    if not current_chat:
        return f"Chat with chat_id '{chat_id}' not found!", 404

    return current_chat.to_json(), 200
