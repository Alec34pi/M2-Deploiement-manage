import datetime
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --- CONFIGURATION ---
RAPPEL_CIBLE = 0.90  # Décidé au tableau de décisions (ex: 90%)
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "modele.joblib")

# --- 1. CHARGEMENT ET NETTOYAGE DES DONNÉES ---
print("1. Chargement des données...")
d = pd.read_csv("data/train-metadata.csv", low_memory=False)

# Retrait des fuites de données (Data Leakage), identifiants et constantes
fuites = ["iddx_full", "iddx_1", "mel_thick_mm", "mel_mitotic_index", "lesion_id"]
constantes = [c for c in d.columns if d[c].nunique(dropna=True) <= 1]
identifiants = ["isic_id"]

a_retirer = list(set(fuites + constantes + identifiants + ["target", "patient_id"]))

X = d.drop(columns=[c for c in a_retirer if c in d.columns])
y = d["target"]
groupes = d["patient_id"]

# --- 2. DÉCOUPAGE PAR PATIENT (MESURE 6) ---
print("2. Découpage sans fuite par patient...")
decoupe = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train, test = next(decoupe.split(X, y, groups=groupes))

# Contrôle strict d'absence de fuite par patient
assert not (
    set(groupes.iloc[train]) & set(groupes.iloc[test])
), "ERREUR : Fuite de patients détectée !"

print("\n--- MESURE 6 : Découpage par patient ---")
print(f"Entraînement : {len(train)} lignes | {groupes.iloc[train].nunique()} patients | {y.iloc[train].sum()} positifs ({y.iloc[train].mean()*100:.4f} %)")
print(f"Test         : {len(test)} lignes | {groupes.iloc[test].nunique()} patients | {y.iloc[test].sum()} positifs ({y.iloc[test].mean()*100:.4f} %)")

# --- 3. PIPELINE DE PRÉTRAITEMENT ---
colonnes_numeriques = X.select_dtypes(include=[np.number]).columns.tolist()
colonnes_categorielles = X.select_dtypes(include=["object", "category"]).columns.tolist()

preprocesseur = ColumnTransformer(
    transformers=[
        (
            "num",
            Pipeline([
                ("imputation", SimpleImputer(strategy="median")),
                ("echelle", StandardScaler()),
            ]),
            colonnes_numeriques,
        ),
        (
            "cat",
            Pipeline([
                ("imputation", SimpleImputer(strategy="most_frequent")),
                ("encodage", OneHotEncoder(handle_unknown="ignore")),
            ]),
            colonnes_categorielles,
        ),
    ]
)

# --- 4. ENTRAÎNEMENT DES MODÈLES (MESURE 7) ---
print("\n3. Entraînement des modèles...")

# Modèle de référence (Dummy)
modele_ref = DummyClassifier(strategy="most_frequent")
modele_ref.fit(X.iloc[train], y.iloc[train])

# Modèle principal
modele = Pipeline([
    ("pre", preprocesseur),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
])

start_time = datetime.datetime.now()
modele.fit(X.iloc[train], y.iloc[train])
duree_entrainement = (datetime.datetime.now() - start_time).total_seconds()

# Évaluation sur le jeu de test
proba = modele.predict_proba(X.iloc[test])[:, 1]
y_test = y.iloc[test]

acc_ref = accuracy_score(y_test, modele_ref.predict(X.iloc[test]))
acc_mod = accuracy_score(y_test, modele.predict(X.iloc[test]))
roc_auc = roc_auc_score(y_test, proba)
pr_auc = average_precision_score(y_test, proba)
hasard_pr_auc = y_test.mean()

print("\n--- MESURE 7 : Comparaison des modèles (sur jeu de test) ---")
print(f"DummyClassifier    | Exactitude: {acc_ref:.4f} | ROC-AUC: 0.5000 | PR-AUC: {hasard_pr_auc:.6f}")
print(f"Régression Logist. | Exactitude: {acc_mod:.4f} | ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}")
print(f"Valeur du hasard   | PR-AUC: {hasard_pr_auc:.6f}")

# --- 5. CHOIX DU SEUIL (MESURES 8 & 9) ---
precision, rappel, seuils = precision_recall_curve(y_test, proba)

# Trouver le plus petit seuil garantissant le rappel visé
i = np.where(rappel >= RAPPEL_CIBLE)[0][-1]
seuil_retenu = seuils[min(i, len(seuils) - 1)]
precision_a_seuil = precision[i]

print("\n--- MESURE 9 : Seuil retenu et son coût ---")
print(f"Rappel visé                         : {RAPPEL_CIBLE*100:.1f} %")
print(f"Seuil correspondant                 : {seuil_retenu:.6f}")
print(f"Précision à ce seuil                : {precision_a_seuil:.6f} ({precision_a_seuil*100:.2f} %)")
if precision_a_seuil > 0:
    print(f"Lésions examinées par maligne trouvée : {round(1 / precision_a_seuil)}")

# --- 6. SÉRIALISATION DU PAQUET (MESURE 10) ---
os.makedirs(MODEL_DIR, exist_ok=True)

paquet = {
    "pipeline": modele,
    "version": "1.0.0",
    "colonnes_attendues": X.columns.tolist(),
    "seuil": float(seuil_retenu),
    "rappel_cible": float(RAPPEL_CIBLE),
    "metriques": {
        "accuracy": float(acc_mod),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
    },
    "prevalence_entrainement": float(y.iloc[train].mean()),
    "entraine_le": datetime.datetime.now().isoformat(),
}

joblib.dump(paquet, MODEL_PATH)

poids_ko = os.path.getsize(MODEL_PATH) / 1024

print("\n--- MESURE 10 : Paquet produit ---")
print(f"Modèle sauvegardé dans             : {MODEL_PATH}")
print(f"Taille du fichier                   : {poids_ko:.2f} Ko")
print(f"Nombre de colonnes attendues        : {len(X.columns)}")
print(f"Durée de l'entraînement             : {duree_entrainement:.2f} secondes")



print("\n--- MESURE 8 : Tableau du compromis ---")
print(
    f"{'Seuil':<6} | {'Rappel':<8} | {'Précision':<9} | {'TP':>4} | {'FP':>6} | {'FN':>4} | {'Alertes/1000':>12}"
)
print("-" * 65)

for s in [0.50, 0.80, 0.90, 0.99]:
    preds = (proba >= s).astype(int)
    tp = np.sum((preds == 1) & (y_test == 1))
    fp = np.sum((preds == 1) & (y_test == 0))
    fn = np.sum((preds == 0) & (y_test == 1))
    rap = tp / (tp + fn) if (tp + fn) > 0 else 0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    alertes_1000 = ((tp + fp) / len(y_test)) * 1000
    print(
        f"{s:<6.2f} | {rap:<8.4f} | {prec:<9.4f} | {tp:>4} | {fp:>6} | {fn:>4} | {alertes_1000:>12.1f}"
    )