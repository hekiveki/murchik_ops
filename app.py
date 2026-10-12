from flask import Flask, jsonify
from datetime import datetime, timezone

app = Flask(__name__)
started_at = datetime.now(timezone.utc).isoformat()

@app.get("/")
def index():
    return jsonify(service="MurchikOps Demo API", message="Мяу! Я Мурчик, работа кипит - прямо под лапами.", started_at=started_at, status="ok")

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200
