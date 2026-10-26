import os
import joblib
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

# --- CHARGEMENT DU MODÈLE AU DÉMARRAGE ---
PIPELINE = None
SEUIL = 0.5
PAQUET = {}
ERREUR = None

try:
    PAQUET = joblib.load(os.environ.get("MODEL_PATH", "model/modele.joblib"))
    PIPELINE = PAQUET["pipeline"]
    SEUIL = float(os.environ.get("SEUIL", PAQUET["seuil"]))
    COLONNES = PAQUET.get("colonnes_attendues", [])
    print("✅ Modèle chargé avec succès.")
except Exception as exc:
    PIPELINE = None
    ERREUR = f"{type(exc).__name__}: {exc}"
    print(f"⚠️ Erreur au chargement : {ERREUR}")


# 1. GET /health
@app.route("/health", methods=["GET"])
def health():
    if PIPELINE is None:
        return jsonify({"status": "error", "erreur": ERREUR}), 503
    return jsonify({"status": "ok", "modele_charge": True}), 200


# 2. GET /model/info
@app.route("/model/info", methods=["GET"])
def model_info():
    if PIPELINE is None:
        return jsonify({"error": "Modèle non disponible"}), 503

    return jsonify({
        "version": PAQUET.get("version"),
        "seuil": SEUIL,
        "rappel_cible": PAQUET.get("rappel_cible"),
        "metriques": PAQUET.get("metriques"),
        "prevalence_entrainement": PAQUET.get("prevalence_entrainement"),
        "colonnes_attendues": COLONNES,
        "entraine_le": PAQUET.get("entraine_le"),
    }), 200


# 3. POST /predict
@app.route("/predict", methods=["POST"])
def predict():
    if PIPELINE is None:
        return jsonify({"error": "Modèle non disponible"}), 503

    charge = request.get_json(silent=True) or {}

    # Validation de la charge utile
    manquantes = [c for c in COLONNES if c not in charge]
    if manquantes:
        return jsonify({
            "error": "Colonnes manquantes dans la charge utile",
            "manquantes": manquantes[:10]
        }), 400

    # Transformation en DataFrame (1 ligne)
    df_input = pd.DataFrame([charge])[COLONNES]

    # Inférence
    proba = float(PIPELINE.predict_proba(df_input)[:, 1][0])

    return jsonify({
        "probabilite_maligne": round(proba, 6),
        "seuil": SEUIL,
        "decision": "suspecte" if proba >= SEUIL else "benigne",
        "version_modele": PAQUET["version"],
        "rappel_cible": PAQUET["rappel_cible"],
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)