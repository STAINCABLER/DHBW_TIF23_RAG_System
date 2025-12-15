import sys
sys.dont_write_bytecode = True
import flask
import rag

import dotenv

dotenv.load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

app = flask.app.Flask(__name__)
app.secret_key = "hallo welt"



@app.get("/")
def get_all_endpoints() -> str:
    with open("backend/index.html", "rb") as file:
        return file.read()

@app.post("/api")
def post_api() -> str:
    body = flask.request.get_json()
    if "user_input" not in body:
        return "", 400
    user_input: str = body["user_input"]

    return rag.rag_process(user_input)


@app.get("/health")
def get_health() -> tuple[str, int]:
    return "", 200


app.run("0.0.0.0", 8001, True)
