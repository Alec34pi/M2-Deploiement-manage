# Model Card — DermaScan API

## Usage prévu
Le tri précoce et le pré-filtrage (*triage*) des lésions cutanées suspectes afin d'assister les professionnels de santé dans l'orientation clinique et la priorisation des rendez-vous.

## Usage explicitement exclu
* **Diagnostic médical autonome** : poser un diagnostic définitif sans validation par un médecin.
* **Prescription ou prise en charge automatique** : toute décision thérapeutique automatisée.
* **Auto-diagnostic grand public** : utilisation directe par les patients à domicile sans supervision médicale.

## Données d'entraînement
* **Origine** : données de santé anonymisées issues du consortium ISIC (9 institutions hospitalières occidentales).
* **Volumétrie** : jeu de test de 81 545 lésions cutanées.
* **Prévalence** : ~0,135 % de cas malignes dans le jeu d'entraînement (110 cas positifs sur 81 545).
* **Écart à la prévalence réelle** : la prévalence d'entraînement reflète un dépistage de masse non ciblé. Elle est très inférieure à la prévalence observée en consultation de dermatologie spécialisée (~5 %).

## Variables utilisées
* **Nombre** : 38 variables explicatives déclarées (`colonnes_attendues`).
* **Familles de variables** :
  * Démographiques (`age_approx`, `sex`).
  * Anatomiques (`anatom_site_general`).
  * Métadonnées d'acquisition et caractéristiques d'imagerie.

## Variables écartées et motif
* **`lesion_id` / `patient_id`** : exclues pour éviter tout risque de fuite d'information (*data leakage*) et de sur-apprentissage par mémorisation des patients (structure gérée via `GroupShuffleSplit`).
* **Variables de confirmation post-biopsie** (`target`, `diagnostic_confirmé`) : exclues en raison d'une fuite directe de la cible (*target leakage*), ces données étant indisponibles au moment du tri initial.

## Performance
| Indicateur | Valeur Modèle | Valeur du Hasard (Baseline) |
| :--- | :---: | :---: |
| **PR-AUC** | **0,0845** | **0,00135** (0,135 %) |
| **ROC-AUC** | **0,8834** | 0,5000 |

## Seuil et compromis
* **Rappel visé** : 90,0 %
* **Seuil de décision retenu** : `0,542`
* **Précision associée** : ~0,45 %
* **Coût clinique** : ~220 lésions examinées par le dermatologue pour 1 lésion maligne identifiée.
* **Faux négatifs restants** : 11 cancers manqués sur 110 cas positifs.

## Populations et angles morts
* **Biais géographique et ethnique** : données issues exclusivement de 9 hôpitaux occidentaux.
* **Sur-représentation des phototypes clairs** : distribution fortement centrée sur les peaux de phototypes I à III.
* **Angle mort documenté** : performances non garanties sur les peaux foncées (phototypes Fitzpatrick IV à VI), sous-représentées dans les données d'origine.

## Versions
* **Version du modèle** : `1.0.0`
* **Image Docker** : `dermascan-api:1.0.0`
* **Dépendances clés** : `scikit-learn==1.3.2`, `pandas==2.1.4`, `joblib==1.3.2`