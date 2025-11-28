import sys
sys.dont_write_bytecode = True
import flask
import endpoints.accounts
import endpoints.chats
import endpoints.debug


app = flask.app.Flask(__name__)
app.secret_key = "hallo welt"

api_blueprint: flask.Blueprint = flask.Blueprint("api", "api", url_prefix="/api")


api_blueprint.register_blueprint(endpoints.accounts.accounts_blueprint)
api_blueprint.register_blueprint(endpoints.chats.chats_blueprint)



@api_blueprint.get("/")
def get_all_endpoints() -> list[dict[str, any]]:
    endpoints: list[dict[str, any]]= []
    for i in app.url_map._rules:
        #endpoints.append(f"{", ".join(i.methods):<25} {i.rule:<30} {i.endpoint}")
        methods: list[str] = list(i.methods)
        if "HEAD" in methods:
            methods.remove("HEAD")
        if "OPTIONS" in methods:
            methods.remove("OPTIONS")

        for method in methods:
            endpoints.append({
                "path": i.rule,
                "method": method,
                "parameter": list(i.arguments)
            })
    return endpoints

@app.get("/health")
def get_health() -> tuple[str, int]:
    return "", 200


app.register_blueprint(api_blueprint)
app.register_blueprint(endpoints.debug.debug_blueprint)

app.run("0.0.0.0", 8001, True)