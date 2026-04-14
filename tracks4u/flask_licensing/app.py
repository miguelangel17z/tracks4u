from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

LICENSE_PRICES = {
    "basic": 9.99,
    "premium": 29.99,
    "exclusive": 99.99,
}

@app.route("/api/v2/licensing/", methods=["POST"])
def crear_licencia():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    license_type = data.get("license_type")
    track_id = data.get("track_id")
    user_id = data.get("user_id")

    if not all([license_type, track_id, user_id]):
        return jsonify({"error": "Faltan campos: license_type, track_id, user_id"}), 400

    if license_type not in LICENSE_PRICES:
        return jsonify({"error": f"Tipo de licencia inválido: {license_type}"}), 400

    precio = LICENSE_PRICES[license_type]

    # Log de auditoría
    with open("licensing_log.txt", "a") as f:
        f.write(f"[{datetime.datetime.now()}] Licencia '{license_type}' creada - Track:{track_id} User:{user_id} Precio:${precio}\n")

    return jsonify({
        "mensaje": "Licencia creada correctamente",
        "license_type": license_type,
        "track_id": track_id,
        "user_id": user_id,
        "precio": precio,
    }), 201


@app.route("/api/v2/licensing/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "servicio": "flask-licensing"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)