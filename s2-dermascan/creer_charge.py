import json
import joblib
import pandas as pd

paquet = joblib.load("model/modele.joblib")
cols = paquet["colonnes_attendues"]

df = pd.read_csv("data/train-metadata.csv", low_memory=False)
charge = df[cols].iloc[0].to_dict()

charge_clean = {k: (None if pd.isna(v) else v) for k, v in charge.items()}

with open("charge.json", "w") as f:
    json.dump(charge_clean, f, indent=2)

print("Fichier charge.json créé avec succès.")