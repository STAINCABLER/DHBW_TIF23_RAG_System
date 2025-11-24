from flask import Blueprint, request
from util import user, chat, session_management



chat_blueprint: Blueprint = Blueprint("chats", __name__, url_prefix="/chats")


@chat_blueprint.get("/")
def get_all_chats() -> list[dict[str, any]]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    chats = current_user.get_chats()

    result_data: list[dict[str, any]] = [
        chat.to_chat_overview()
        for chat in chats
    ]

    return result_data, 200

@chat_blueprint.post("/")
def create_chat() -> dict[str, any]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    new_chat: chat.Chat = current_user.create_chat()



    # TODO: bissl magic


    return new_chat.to_dict(), 200

@chat_blueprint.get("/<chat_id>")
def get_chat(chat_id: str) -> dict[str, any]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    current_chat: chat.Chat = current_user.get_chat_with_id(chat_id)

    if not current_chat:
        return f"Chat with chat_id '{chat_id}' not found!", 404

    return current_chat.to_dict(), 200


@chat_blueprint.post("/<chat_id>")
def post_to_chat(chat_id: str) -> dict[str, any]:
    if not session_management.is_user_logged_in():
        return "", 401

    current_user: user.User = session_management.get_user_from_session()

    current_chat: chat.Chat = current_user.get_chat_with_id(chat_id)

    if not current_chat:
        return f"Chat with chat_id '{chat_id}' not found!", 404

    user_input: str = request.form.get("user_input", None)

    if not user_input:
        return "Field user_input is required!", 400
    
    user_chat_entry: chat.ChatMessage = chat.ChatMessage(chat.EntryRole.USER.role_name, user_input, [])

    current_chat.messages.append(user_chat_entry)
    
    #TODO Do magic here

    question: str = "PLACEHOLDER"
    assitent_chat_entry: chat.ChatMessage = chat.ChatMessage(chat.EntryRole.ASSISTENT.role_name, question, [])


    current_chat.messages.append(assitent_chat_entry)

    current_chat.update_messages()

    return assitent_chat_entry.to_dict(), 200
