import pandas as pd

d = pd.read_csv("data/train-metadata.csv", low_memory=False)

print("lignes, colonnes :", d.shape)
print("patients distincts :", d["patient_id"].nunique())

tailles = d.groupby("patient_id").size()
print(
    "lesions par patient :",
    tailles.min(),
    int(tailles.median()),
    tailles.max(),
)

print("\nTypes de colonnes :")
print(d.dtypes)

print("\n--- MESURE 3 : Fuites de données (Data Leakage) ---")
SUSPECTES = [
    "iddx_full",
    "iddx_1",
    "mel_thick_mm",
    "mel_mitotic_index",
    "lesion_id",
]

for c in SUSPECTES:
    if c in d.columns:
        rempli = d[c].notna().sum()
        malignes = d.loc[d[c].notna(), "target"].sum()
        print(f"{c:<22} rempli {rempli:>7} dont malignes {int(malignes):>4}")

print("\n--- --- ---")

na = d.isna().sum()
print(na[na > 0].sort_values(ascending=False))

constantes = [c for c in d.columns if d[c].nunique(dropna=True) <= 1]
print("constantes :", constantes)



print("\n--- MESURE 5 : Distribution de la cible ---")
nb_benignes = (d["target"] == 0).sum()
nb_malignes = (d["target"] == 1).sum()
taux_pos = d["target"].mean() * 100
rapport = nb_benignes / nb_malignes

print(f"Lésions target = 1 (malignes) : {nb_malignes}")
print(f"Lésions target = 0 (bénignes) : {nb_benignes}")
print(f"Taux de positifs : {taux_pos:.4f} %")
print(f"Rapport : 1 maligne pour {int(rapport)} bénignes")