from flask import Flask, request, jsonify
import datetime
import requests

app = Flask(__name__)

LICENSE_PRICES_USD = {
    "basic": 9.99,
    "premium": 29.99,
    "exclusive": 99.99,
}

DJANGO_URL = "http://django_web:8000"

# ─── Adapter pattern ──────────────────────────────────────────────
class CurrencyAdapter:
    BASE_URL = "https://api.frankfurter.app"

    @staticmethod
    def convert(amount_usd: float, to_currency: str) -> dict:
        try:
            r = requests.get(
                f"{CurrencyAdapter.BASE_URL}/latest",
                params={"from": "USD", "to": to_currency},
                timeout=5
            )
            r.raise_for_status()
            rate = r.json()["rates"][to_currency]
            return {"amount": round(amount_usd * rate, 2), "currency": to_currency, "rate": rate}
        except Exception:
            return {"amount": amount_usd, "currency": "USD", "rate": 1.0}
# ──────────────────────────────────────────────────────────────────


@app.route("/api/v2/licensing/", methods=["POST"])
def crear_licencia():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    license_type = data.get("license_type")
    track_id     = data.get("track_id")
    user_id      = data.get("user_id")
    currency     = data.get("currency", "USD").upper()

    if not all([license_type, track_id, user_id]):
        return jsonify({"error": "Faltan campos: license_type, track_id, user_id"}), 400

    if license_type not in LICENSE_PRICES_USD:
        return jsonify({"error": f"Tipo inválido: {license_type}"}), 400

    # 1. Convertir precio con Adapter
    precio_usd = LICENSE_PRICES_USD[license_type]
    precio_convertido = CurrencyAdapter.convert(precio_usd, currency)

    # 2. Crear licencia real en Django
    try:
        resp = requests.post(
            f"{DJANGO_URL}/payment/licensing/",
            json={"license_type": license_type, "track": track_id, "user": user_id},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        django_ok = resp.status_code == 201
        django_msg = resp.json() if django_ok else resp.text
    except Exception as e:
        django_ok = False
        django_msg = str(e)

    # 3. Log de auditoría
    with open("licensing_log.txt", "a") as f:
        f.write(f"[{datetime.datetime.now()}] {license_type} | Track:{track_id} User:{user_id} | {precio_convertido['amount']} {precio_convertido['currency']} | django_ok:{django_ok}\n")

    if not django_ok:
        return jsonify({"error": "No se pudo registrar la licencia", "detalle": django_msg}), 502

    return jsonify({
        "status": "approved",
        "license_type": license_type,
        "track_id": track_id,
        "user_id": user_id,
        "precio_usd": precio_usd,
        f"precio_{currency.lower()}": precio_convertido["amount"],
        "currency": precio_convertido["currency"],
        "tasa": precio_convertido["rate"],
        "recibo_id": f"REC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}",
    }), 201


@app.route("/api/v2/licensing/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servicio": "flask-licensing"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)