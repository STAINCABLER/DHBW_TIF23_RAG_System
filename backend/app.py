import sys
sys.dont_write_bytecode = True
import flask
import rag
import test_rag

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
def get_index() -> str:
    with open("backend/index.html", "r", encoding="utf-8") as file:
        return file.read()

@app.get("/debug")
def get_index_debug() -> str:
    with open("backend/index.html", "r", encoding="utf-8") as file:
        r = file.read()
        return r.replace('const API_URL = "./api"', 'const API_URL = "./api-debug"').replace('<title>Der DHBW Datenbank Design Deputy</title>', '<title>Der DHBW Datenbank Design Deputy - Debug</title>').replace('<h1>Der DHBW Datenbank Design Deputy</h1>', '<h1>Der DHBW Datenbank Design Deputy - DEBUG</h1>').replace('--color-surface: #05181B;', '--color-surface: #180505;')

@app.post("/api")
def post_api() -> str:
    body = flask.request.get_json()
    if "user_input" not in body:
        return "", 400
    user_input: str = body["user_input"]

    return rag.rag_process(user_input)

@app.post("/api-debug")
def post_api_debug() -> str:
    body = flask.request.get_json()
    if "user_input" not in body:
        return "", 400
    user_input: str = body["user_input"]

    results: list[float] = [0.0, 0.0, 0.0]
    NUM_OF_TRIES: int = 1000

    for _ in range(NUM_OF_TRIES):
        r = test_rag.rag_process(user_input)

        for i, e in enumerate(r):
            results[i] += e
    
    avg: list[float] = [
        i / NUM_OF_TRIES * 1000
        for i in results
    ]

    return f"""
    <h3>{NUM_OF_TRIES} Run test</h3>
    <p>
    <h5>Total Times</h5>
        <table>
            <tr>
                <th style="min-width: 200px;">Category</th>
                <th>Time [s]</th>
            </tr>
            <tr>
                <td>Total Scenario Search</td>
                <td>{results[0]:.4f}</td>
            </tr>
            <tr>
                <td>Total Chunks Search</td>
                <td>{results[1]:.4f}</td>
            </tr>
            <tr>
                <td>Total Search</td>
                <td>{results[2]:.4f}</td>
            </tr>
        </table>
        <br>
    </p>
    <p>
    <h5>Average Times</h5>
        <table>
            <tr>
                <th style="min-width: 200px;">Category</th>
                <th>Time [ms]</th>
            </tr>
            <tr>
                <td>Average Scenario Search</td>
                <td>{avg[0]:.0f}</td>
            </tr>
            <tr>
                <td>Average Chunks Search</td>
                <td>{avg[1]:.0f}</td>
            </tr>
            <tr>
                <td>Total Average Search</td>
                <td>{avg[2]:.0f}</td>
            </tr>
        </table>
        <br>
    </p>
    """

    return f"{results}\n{avg}"

@app.get("/health")
def get_health() -> tuple[str, int]:
    return "", 200


app.run("0.0.0.0", 8001, True)
