import flask
import mimetypes
import os

import util.conversation
import util.file
import util.user
import util.session_management





SUPPORTED_FILE_TYPES: list[str] = [
    "csv"
    "json",
    "md",
    "pdf",
    "txt",
]


def get_file_type(filename: str) -> str | None:
    if "." not in filename:
        return None
    
    extension: str = filename.rsplit(".", 1)[1].lower()

    return extension
    

def is_file_type_allowed(filename: str) -> bool:
    extension: str | None = get_file_type(filename)

    return extension in SUPPORTED_FILE_TYPES


documents_blueprint: flask.Blueprint = flask.Blueprint("docs", "docs", url_prefix="/<chat_id>/docs")


@documents_blueprint.get("/")
@util.session_management.requires_session(True)
def get_all_documents(session_token: util.session_management.SessionToken, chat_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    uploaded_files: list[util.file.UploadedFile] = conversation.get_all_uploaded_files()

    parsed_files: list[dict[str, any]] = [
        file.to_dict()
        for file in uploaded_files
    ]

    return parsed_files, 200

@documents_blueprint.get("/<document_id>")
@util.session_management.requires_session(True)
def get_document(session_token: util.session_management.SessionToken, chat_id: int, document_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    uploaded_file: util.file.UploadedFile = util.file.UploadedFile.find_by_file_id(document_id)

    if not uploaded_file:
        return "File not found!", 404

    if uploaded_file.conversation_id != conversation.conversation_id:
        return "File not found!", 404

    if not os.path.exists(os.path.join(util.file.UPLOAD_FOLDER, str(uploaded_file.file_uuid))):
        return "File not found!", 404
    
    file_path: str = os.path.join(util.file.UPLOAD_FOLDER, str(uploaded_file.file_uuid))
    mimetype: str = mimetypes.types_map.get(f".{uploaded_file.file_type}", "text/plain")
    with open(file_path, "rb") as file:
        content = file.read()
        return flask.Response(content, mimetype=mimetype)

@documents_blueprint.delete("/<document_id>")
@util.session_management.requires_session(True)
def delete_document(session_token: util.session_management.SessionToken, chat_id: int, document_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    uploaded_file: util.file.UploadedFile = util.file.UploadedFile.find_by_file_id(document_id)

    if not uploaded_file:
        return "File not found!", 404

    if uploaded_file.conversation_id != conversation.conversation_id:
        return "File not found!", 404

    if not os.path.exists(os.path.join(util.file.UPLOAD_FOLDER, str(uploaded_file.file_uuid))):
        return "File not found!", 404
    
    uploaded_file.delete_file()

    return "", 200

@documents_blueprint.post("/")
@util.session_management.requires_session(True)
def post_upload_file(session_token: util.session_management.SessionToken, chat_id: int):
    user: util.user.User = session_token.get_user()

    if not user:
        return "", 401
    
    conversation: util.conversation.Conversation = util.conversation.Conversation.get_conversation_from_conversation_id(chat_id)

    if not conversation:
        return "Conversation not found!", 404
    
    if conversation.user_id != user.id:
        return "Conversation not found!", 404
    
    if "file" not in flask.request.files:
        return "File required", 400
    
    file = flask.request.files["file"]

    if not file:
        return "Invalid file!", 400

    if file.filename == "" or not file.filename:
        return "Invalid filename", 400
    
    file_name: str = file.filename
    file_type: str | None = get_file_type(file_name)

    if not file_type:
        return "File must use . extension!", 400
    
    if not is_file_type_allowed(file_name):
        return f"File-Type '{file_type}' not supported!"

    uploaded_file: util.file.UploadedFile = conversation.create_uploaded_file(
        file_name,
        file_type
    )

    if not uploaded_file:
        return "Could not upload file!", 500
    
    file.save(os.path.join(util.file.UPLOAD_FOLDER, str(uploaded_file.file_uuid)))

    return uploaded_file.to_dict(), 201


    

    
