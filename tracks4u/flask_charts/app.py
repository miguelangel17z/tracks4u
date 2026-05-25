
from flask import Flask, jsonify, request, render_template


import requests

app = Flask(__name__)


DJANGO_URL = "http://django-web:8000"
INTERNAL_BASE = f"{DJANGO_URL}/internal/charts"




def fetch_from_django(path: str, params: dict = None):
    """Helper para consumir los endpoints internos de Django."""
    try:
        resp = requests.get(f"{INTERNAL_BASE}{path}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json(), resp.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "No se pudo conectar con Django"}, 502
    except requests.exceptions.Timeout:
        return {"error": "Timeout conectando con Django"}, 504
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/v2/charts/dashboard/", methods=["GET"])
def dashboard_data():

    period = request.args.get("period", "30d")

    data, status = fetch_from_django(
        "/dashboard/",
        {"period": period}
    )

    return jsonify(data), status

# ── Página principal del dashboard ───────────────────────────────

@app.route("/charts/", methods=["GET"])
def dashboard():
    """Sirve el template HTML del dashboard."""
    return render_template("charts/dashboard.html")


# ── API endpoints expuestos al frontend ──────────────────────────

@app.route("/api/v2/charts/summary/", methods=["GET"])
def summary():
    period = request.args.get("period", "30d")
    data, status = fetch_from_django("/summary/", {"period": period})
    return jsonify(data), status


@app.route("/api/v2/charts/sales/", methods=["GET"])
def sales():
    period = request.args.get("period", "30d")
    data, status = fetch_from_django("/sales/", {"period": period})
    return jsonify(data), status


@app.route("/api/v2/charts/revenue/", methods=["GET"])
def revenue():
    period = request.args.get("period", "30d")
    data, status = fetch_from_django("/revenue/", {"period": period})
    return jsonify(data), status


@app.route("/api/v2/charts/top-tracks/", methods=["GET"])
def top_tracks():
    limit = request.args.get("limit", 10)
    data, status = fetch_from_django("/top-tracks/", {"limit": limit})
    return jsonify(data), status


@app.route("/api/v2/charts/top-genres/", methods=["GET"])
def top_genres():
    period = request.args.get("period", "30d")
    data, status = fetch_from_django("/top-genres/", {"period": period})
    return jsonify(data), status


@app.route("/api/v2/charts/health/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servicio": "flask-charts"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
