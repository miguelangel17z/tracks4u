from flask import Flask, request, jsonify
import datetime
import requests
import json
import base64

app = Flask(__name__)

LICENSE_PRICES_USD = {
    "basic": 9.99,
    "premium": 29.99,
    "exclusive": 99.99,
}

DJANGO_URL = "http://django-web:8000"

# ─── Adapter pattern ──────────────────────────────────────────────
import requests


class CurrencyAdapter:
    BASE_URL = "https://open.er-api.com/v6/latest/USD"

    @staticmethod
    def convert(amount_usd: float, to_currency: str) -> dict:
        try:
            to_currency = to_currency.upper()

            r = requests.get(
                CurrencyAdapter.BASE_URL,
                timeout=5
            )

            r.raise_for_status()

            data = r.json()

            rate = data["rates"][to_currency]

            return {
                "amount": round(amount_usd * rate, 2),
                "currency": to_currency,
                "rate": rate
            }

        except Exception as e:
            print(e)

            return {
                "amount": amount_usd,
                "currency": "USD",
                "rate": 1.0
            }
# ──────────────────────────────────────────────────────────────────

def get_user_id_from_token(auth_header):
    try:
        token = auth_header.replace("Bearer ", "")
        payload = token.split(".")[1]
        # agregar padding si falta
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        return decoded.get("user_id")
    except Exception as e:
        print(f"Error decodificando token: {e}")
        return None

@app.route("/api/v2/licensing/", methods=["POST"])
def crear_licencia():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    license_type = data.get("license_type")
    track_id     = data.get("track_id")
    currency     = data.get("currency", "USD").upper()

    if not all([license_type, track_id]):
        return jsonify({"error": "Faltan campos: license_type, track_id"}), 400

    if license_type not in LICENSE_PRICES_USD:
        return jsonify({"error": f"Tipo inválido: {license_type}"}), 400

    # 1. Convertir precio con Adapter
    precio_usd = LICENSE_PRICES_USD[license_type]
    precio_convertido = CurrencyAdapter.convert(precio_usd, currency)
    print(f"Enviando a Django: license_type={license_type}, track={track_id}, tipo track={type(track_id)}", flush=True)
    # 2. Crear licencia real en Django
    try:
        auth_header = request.headers.get("Authorization", "")
        user_id = get_user_id_from_token(auth_header)

        if not user_id:
            return jsonify({"error": "Token inválido o ausente"}), 401

        resp = requests.post(
            f"{DJANGO_URL}/payment/licensing/",
            json={"license_type": license_type, "track": int(track_id), "user": user_id},
            headers={"Content-Type": "application/json"},
            timeout=5
        ) 
        django_status = resp.status_code

        django_ok = resp.status_code == 201

        try:
            django_msg = resp.json()
        except:
            django_msg = resp.text 
        print(f"Django respondió: {django_status} — {django_msg}", flush=True)  # ← agregar esto

    except Exception as e:
        django_ok = False
        django_msg = str(e)
        django_status = 502
    # 3. Log de auditoría
    with open("licensing_log.txt", "a") as f:
        f.write(f"[{datetime.datetime.now()}] {license_type} | Track:{track_id} | {precio_convertido['amount']} {precio_convertido['currency']} | django_ok:{django_ok}\n")

    if not django_ok:
        return jsonify(django_msg), django_status
    return jsonify({
        "status": "approved",
        "license_type": license_type,
        "track_id": track_id,
        "precio_usd": precio_usd,
        f"precio_{currency.lower()}": precio_convertido["amount"],
        "currency": precio_convertido["currency"],
        "tasa": precio_convertido["rate"],
        "recibo_id": f"REC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
    }), 201


@app.route("/api/v2/licensing/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servicio": "flask-licensing"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)