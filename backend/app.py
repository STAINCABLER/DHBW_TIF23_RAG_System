from flask import Flask, Blueprint
from endpoints import accounts, chats

app = Flask(__name__)
app.secret_key = "hallo welt"

api_blueprint: Blueprint = Blueprint("api", __name__, url_prefix="/api")

api_blueprint.register_blueprint(accounts.account)
api_blueprint.register_blueprint(chats.chat_blueprint)



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


app.register_blueprint(api_blueprint)

@app.get("/health")
def get_health() -> tuple[str, int]:
    return "", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="4000")
