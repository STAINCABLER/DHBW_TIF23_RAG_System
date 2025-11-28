import flask

import endpoints.documents
import rag
import util.conversation
import util.session_management
import util.user


chats_blueprint: flask.Blueprint = flask.Blueprint("chats", "chats", url_prefix="/chats")
chats_blueprint.register_blueprint(endpoints.documents.documents_blueprint)

@chats_blueprint.get("/")
@util.session_management.requires_session(True)
def get_all_chats(session_token: util.session_management.SessionToken):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversations: list[util.conversation.Conversation] = util.conversation.Conversation.get_all_conversations_from_user_id(user.id)

    transformed_conversations: list[dict[str, any]] = [
        conversation.to_reduced_dict()
        for conversation in conversations
    ]

    return transformed_conversations, 200

@chats_blueprint.get("/<chat_id>")
@util.session_management.requires_session(True)
def get_chat(session_token: util.session_management.SessionToken, chat_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    conversation.load_all_messages()

    return conversation.to_full_dict(), 200


@chats_blueprint.post("/<chat_id>")
@util.session_management.requires_session(True)
def post_to_chat(session_token: util.session_management.SessionToken, chat_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    user_input: str = flask.request.form.get("user_input", None)

    if not user_input:
        return "Request requires user_input!", 400
    
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    conversation.load_all_messages()

    user_message: util.conversation.ConversationMessage = conversation.create_conversation_message(user_input, "user", {})

    if not user_message:
        "Could not save user-message", 500

    ######################
    # TODO DO MAGIC HERE #
    ######################

    # Currently only serves as a placeholder
    output: str = rag.process_input(user, user_input)

    message: util.conversation.ConversationMessage = conversation.create_conversation_message(output, "assistant", {})

    if not message:
        "Could not generate assistant-message", 500

    return message.to_dict(), 201


@chats_blueprint.post("/")
@util.session_management.requires_session(True)
def post_create_chat(session_token: util.session_management.SessionToken):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    user_id: int = user.id
    title: str = flask.request.form.get("title", "New Chat")

    conversation: util.conversation.Conversation = util.conversation.Conversation.create_conversation_from_user(
        user_id,
        title
    )

    if not conversation:
        return "Could not create conversation", 500
    
    return conversation.to_reduced_dict(), 201
