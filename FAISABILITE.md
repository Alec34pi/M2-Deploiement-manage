# TP3 Dermascan 

## Tableau de Décisions

| Décision | Contrainte | Votre valeur |
| :--- | :--- | :--- |
| **Suffixe personnel** | identique à S1 | `ap24` |
| **Région Azure** | une seule, la même partout, choisie en partie 1 | `francecentral` |
| **Nom du groupe de ressources** | préfixé `rg-dermascan-s3-` | `rg-dermascan-s3-ap24` |
| **Nom du registre ACR existant** | celui de S1 | `acrdermascanap24` |
| **Dépôt et tag de l'image S2** | ce qui est réellement dans le registre | `dermascan-api:1.0.0` |
| **Nom du plan de service** | préfixé `plan-dermascan-` | `plan-dermascan-ap24` |
| **Nom de l'application web** | unique sur Azure, minuscules et tirets | `dermascan-api-ap24` |

### Question 0.1
Contrairement à un registre ACR, l'application web expose directement une URL publique accessible sur le web (`.azurewebsites.net`). Un nom trop prévisible permet à un attaquant de cibler directement le point de terminaison pour lancer des requêtes HTTP malveillantes ou chercher des failles de sécurité.

---
---

# Partie 1 - Vérification de faisabilité et choix de la cible

## Mesure 1 - Sondes de faisabilité de l'abonnement

| Sonde | Commande source | Votre relevé |
| :--- | :--- | :--- |
| **Régions autorisées par la politique** | `az policy assignment list` | `[]` |
| **Microsoft.Web** | `az provider show` | `Registered` |
| **Microsoft.ContainerInstance** | `az provider show` | `Registered` |
| **Microsoft.ContainerRegistry** | `az provider show` | `Registered` |
| **Création du plan App Service Linux** | `az appservice plan create` | `succès` |
| **Code d'erreur exact, le cas échéant** | sortie de la commande | `N/A` |
| **Durée totale de la sonde** | chronomètre | `30s` |

## Mesure 2 - Cible retenue, fait déclencheur et heure de la décision

| Élément de la décision | Votre réponse |
| :--- | :--- |
| **Cible retenue** | A - App Service for Containers |
| **Fait déclencheur, cité avec le message d'erreur s'il y en a un** | Création du plan réussie avec l'état `Ready`. |
| **Heure de la décision** | 11:16 |
| **Ce que cette cible ne permettra pas de montrer aujourd'hui** | La gestion directe et manuelle de l'orchestration des conteneurs ou l'effet du scaling horizontal sur un cluster local (comme sous Docker Compose). |

### Question 1.1

| Cible | Modèle de service | Ce que vous ne gérez pas | Ce qui reste à votre charge |
| :--- | :--- | :--- | :--- |
| **App Service for Containers** | PaaS | L'infrastructure physique, l'OS sous-jacent, le routage réseau matériel et le load balancing. | Le conteneur (artefact), la configuration applicative, les secrets, le code et la gestion des logs. |
| **Azure Container Instances** | PaaS (Conteneur) | Les VMs hôtes, la gestion du cluster ou du plan de service. | Le conteneur isolé, le dimensionnement unitaire (CPU/RAM) et les politiques de redémarrage. |
| **Docker sur votre poste** | IaaS / Local | Rien (à part le matériel de son propre PC portable). | Le démon Docker, le cycle de vie complet des conteneurs, le réseau local, le stockage et l'OS hôte. |

### Question 1.2

* **SKU choisi :** `B1`
* **Coût mensuel estimé :** ~10 à 12 € / mois.
* **Crédit restant (relevé Cost Management) :** ~87,75 €.
* **Autonomie en fonctionnement continu :** Le crédit permet de financer environ 7 mois de fonctionnement continu avec cette configuration.
* **Justification du nettoyage :** Même si le crédit est large, un plan App Service est facturé à l'heure, qu'il reçoive du trafic ou pas du tout. Oublier une ressource active consomme du crédit inutilement qui sera nécessaire pour les prochaines séances.

---
---

# Partie 2 - Déploiement du conteneur depuis ACR

## Mesure 3 - Identification exacte de l'image à déployer

| Relevé | Votre valeur |
| :--- | :--- |
| **loginServer** | `acrdermascanap24.azurecr.io` |
| **Nom complet de l'image (`IMAGE_FULL`)** | `acrdermascanap24.azurecr.io/dermascan-api:1.0.0` |
| **Digest sha256 du tag déployé** | `sha256:230b01a8678f6cce5944bf22ec9f1b992821e7f3995c3ecd970ee546c67f6614` |
| **Architecture déclarée dans le manifeste** | `linux/amd64` |
| **Date de publication de ce tag** | 11:30 |

### Question 2.1
* **Comportement en cas de push sous le même tag :** Si un camarade pousse une nouvelle image sous le même tag `1.0.0` et que l'App Service redémarre, Azure va pull la nouvelle image. Cela risque de modifier ou casser l'application en prod sans qu'on s'en rende compte.
* **Utilité du digest :** Oui, le digest (`sha256:...`) permet d'identifier l'image de manière immuable et unique. En configurant le déploiement avec le digest, le service télécharge exactement le même artefact, peu importe si quelqu'un réécrase le tag juste après.

## Mesure 4 - Comportement du service avant tout octroi de droit sur le registre

| Relevé avant octroi des droits | Votre valeur |
| :--- | :--- |
| **Code HTTP retourné** | `000` |
| **Durée de la réponse** | 0.001037s |
| **Contenu de la page renvoyée (une ligne de résumé)** | (vide) |

## Mesure 5 - Identité managée, rôle accordé, portée et délai de propagation

| Relevé | Votre valeur |
| :--- | :--- |
| **principalId de l'identité managée** | `323befc9-c4ef-42f3-9316-025f90df07cf` |
| **Rôle accordé** | `AcrPull` |
| **Portée exacte du rôle (chemin complet)** | `/subscriptions/0f8250e1-72cb-4b9d-bfd8-9caeb8108c8c/resourceGroups/rg-dermascan-registre-ap24/providers/Microsoft.ContainerRegistry/registries/acrdermascanap24` |
| **Délai entre l'attribution du rôle et le premier pull réussi** | ~45 secondes |

### Question 2.2
* **Rôle plus large au niveau du registre :** Le rôle `Contributor` sur le registre ACR permettrait à l'application de pusher, modifier ou supprimer des images et configurer le registre.
* **Rôle encore plus large au niveau de l'abonnement :** Le rôle `Contributor` ou `Owner` au niveau du Groupe de ressources / Subscription complète.
* **Conséquence :** Ces rôles ne respectent pas le principe du moindre privilège. Si l'app web est compromise, un attaquant pourrait modifier le registre ou supprimer d'autres ressources sur Azure.

### Question 2.3
* **Délai de propagation observé :** Environ 45 secondes. C'est dû à la réplication du rôle RBAC dans Entra ID. C'est un élément important à prendre en compte si on veut scripter un déploiement automatisé (il faut ajouter un `sleep`).

## Mesure 6 - Premier démarrage réussi et performances

| Mesure du premier démarrage | Votre valeur |
| :--- | :--- |
| **Durée entre le restart et le premier 200 sur `/health`** | `18.07s` |
| **Codes HTTP observés pendant l'attente** | `000`, `200` |
| **Champ `model_loaded` de la réponse `/health`** | `true` |
| **Version de modèle retournée par `/model/info`** | `1.0.0` |
| **`probabilite_maligne` et `decision` retournés par `/predict`** | 0.990257 / benigne |
| **Le seuil appliqué est-il celui du paquet S2 ?** | Oui (`0.998593...`) |
| **Durée de la première requête `/predict`** | `0.235s` |
| **Durée de la cinquième requête `/predict`** | `0.122s` |

### Question 2.4
* **Écart constaté :** La première requête prend ~0.235s alors que la 5ème prend ~0.122s. On observe une réduction de la latence de moitié à cause d'un petit effet de warm-up.
* **Hypothèse 1 : Connexion réseau et TLS Handshake (Keep-Alive)**
  * *Explication :* La première requête paye le coût de l'ouverture de la connexion TCP et du handshake SSL/TLS. Les requêtes suivantes réutilisent la connexion déjà établie.
  * *Moyen de confirmation :* Utiliser `curl` avec des variables de chrono (`%{time_connect}`, `%{time_appconnect}`) pour séparer la latence réseau du traitement interne du serveur.
* **Hypothèse 2 : Initialisation paresseuse (JIT / allocations NumPy/Pandas)**
  * *Explication :* Même si le modèle est chargé au boot, les bibliothèques comme NumPy/Scikit-Learn allouent de la mémoire ou compilent des fonctions mathématiques lors de la toute première inférence.
  * *Moyen de confirmation :* Mettre des logs avec `time.time()` dans `app.py` autour de l'appel `predict_proba()` pour mesurer le temps de calcul brut sans le réseau.

---
---

# Partie 3 - Configuration d'exécution

### Question 3.1
* **Alignement des ports :** `WEBSITES_PORT` et `PORT` doivent idéalement avoir la même valeur (ex: 5000).
* **Qui lit quoi ?** `WEBSITES_PORT` est lu par la plateforme Azure App Service (reverse proxy) pour savoir vers quel port diriger le trafic. `PORT` est lu par l'application (Flask/Gunicorn) dans le conteneur.
* **Si ils diffèrent :** Azure tente d'envoyer le trafic sur un port non écouté par l'application. Le client obtiendra une erreur `502 Bad Gateway` ou un timeout.

## Mesure 7 - Visibilité réelle du secret `INFERENCE_LOG_SALT`

| Contrôle | Votre observation |
| :--- | :--- |
| **La valeur du sel est-elle masquée dans la sortie du CLI ?** | Non, `az webapp config appsettings list` l'affiche en clair dans la table. |
| **Est-elle visible dans le portail Azure, onglet Configuration ?** | Oui, il suffit de cliquer sur le bouton "Afficher la valeur" pour la lire. |
| **Est-elle lisible par un processus qui s'exécuterait dans le conteneur ?** | Oui, Azure l'injecte sous forme de variable d'environnement (`os.environ`). |

### Question 3.2
* **Service coffre-fort :** **Azure Key Vault**.
* **Utilisation avec Managed Identity :** En liant Key Vault et l'identité managée, on peut remplacer la valeur en clair du paramètre d'application par une référence Key Vault. L'application va chercher le secret de façon sécurisée à l'exécution sans rien stocker en clair dans la configuration.

## Mesure 8 - Effet de la configuration complète et test du seuil à chaud

| Relevé après redémarrage | Votre valeur |
| :--- | :--- |
| **Chemin de sonde enregistré** | `/health` |
| **Durée du redémarrage jusqu'au premier 200** | `~18s` |
| **Délai entre le `appsettings set` du seuil abaissé et l'apparition du nouveau seuil dans la réponse** | **Infini / Non pris en compte** (le seuil de la réponse reste bloqué à l'ancienne valeur) |
| **Nombre total de réglages d'application** | `8` |
| **La valeur de `MODEL_VERSION` apparaît-elle dans la réponse de `/model/info` ?** | Oui |
| **`probabilite_maligne`, avec votre seuil de S2** | `0.990257` |
| **seuil et decision retournés, avec votre seuil de S2** | Seuil : `0.9985934962507592` / Décision : `benigne` |
| **`probabilite_maligne`, avec le seuil abaissé** | `0.990257` (inchangée) |
| **seuil et decision retournés, avec le seuil abaissé** | Seuil : `0.9985934962507592` / Décision : `benigne` *(l'application ne lit pas la variable `SEUIL` de l'environnement)* |

### Question 3.3
* **Choix de version :** Je déploie la **Version 2**.
* **Risque de la version 1 :** La version 1 renvoie un 200 dès que le serveur web tourne, même si le modèle `.joblib` a planté ou n'est pas chargé.
* **Cas d'une instance sans modèle :** L'instance sera marquée comme "saine" par Azure qui continuera de lui envoyer des requêtes. Les utilisateurs recevront des erreurs `500` systématiques lors des appels à `/predict`.

### Question 3.4
1. **Comportement :** C'est le paramètre d'environnement métier (seuil de décision) du service qui a bougé, le modèle est resté identique.
2. **Vocabulaire d'audit :** Non, dire que "le modèle a changé d'avis" est faux. Le modèle sort la même probabilité brute, c'est la règle de décision métier côté service qui a été modifiée.
3. **Trace de découverte :** On retrouve la modification dans les **Azure Activity Logs** (historique des modifications App Settings) ainsi que dans les logs d'inférence.
4. **Progrès ou risque :** C'est un **progrès** pour ajuster la sensibilité rapidement sans redéployer tout le conteneur, mais un **risque** si ce n'est pas tracé dans la CI/CD.

---
---

# Partie 4 - Observation, diagnostic et tolérance aux pannes

## Mesure 9 - Analyse du flux de logs et conformité des données

| Observation dans le flux de logs | Votre relevé |
| :--- | :--- |
| **Le nom du conteneur apparaît-il en préfixe de chaque ligne ?** | Oui |
| **Retrouve-t-on la ligne d'accès de Gunicorn pour chaque requête ?** | Oui |
| **Que journalise votre API sur un `/predict` incomplet ?** | Une exception Python (`KeyError`) levée lors de la validation. |
| **La liste des variables manquantes apparaît-elle dans les logs ?** | Oui, la stack trace affiche la clé manquante. |
| **Délai approximatif entre la requête et l'apparition de sa ligne** | Presque instantané (`< 2s`) |
| **La charge utile complète du POST apparaît-elle dans les logs ?** | **Oui** (Problème de conformité RGPD/Données de santé) |

## Mesure 10 - Diagnostic de la panne provoquée

| Élément du diagnostic | Votre relevé |
| :--- | :--- |
| **Code HTTP vu par le client** | `502 Bad Gateway` |
| **Délai avant la réponse d'erreur** | ~60 secondes |
| **Ligne de log exacte qui nomme la cause, recopiée intégralement** | `Container didn't respond to HTTP pings on port: 9999, failing site start` |
| **Combien de fois la plateforme a-t-elle retenté avant d'abandonner ?** | 5 tentatives |
| **Le processus applicatif a-t-il démarré, oui ou non ?** | **Oui** |
| **Temps écoulé entre le redémarrage et la ligne fautive** | ~45 secondes |

## Mesure 11 - Délai de retour au service après correction

| Élément | Votre relevé |
| :--- | :--- |
| **Durée entre la correction et le premier 200** | ~20 secondes |
| **A-t-il fallu un redémarrage explicite, ou la plateforme a-t-elle repris seule ?** | Redémarrage explicite requis (`az webapp restart`) |

### Question 4.1
1. **Différence vue du client :** Du point de vue du client, il n'y a **aucune différence**. Dans les deux cas le navigateur/curl reçoit un code HTTP d'erreur générique (`502 Bad Gateway` / `503 Service Unavailable`).
2. **Différence dans les logs (Lignes discriminantes) :**
   * *Cas 1 (Erreur de droit/pull ACR) :* `Error response from daemon: pull access denied for acrdermascanap24.azurecr.io/...`
   * *Cas 2 (Mauvais port) :* `Container didn't respond to HTTP pings on port: 9999, failing site start`
3. **Valeur d'un code HTTP pour le diagnostic :** Un code HTTP est insuffisant à lui seul pour trouver l'origine d'une panne. Il indique simplement que le service est inaccessible, mais il faut obligatoirement consulter les logs d'infrastructure pour comprendre le vrai problème.

## Mesure 12 - Métriques de plateforme (1 heure)

| Métrique | Votre relevé sur l'heure écoulée |
| :--- | :--- |
| **Nombre total de requêtes** | `6.0` |
| **Nombre de réponses 5xx** | `0.0` |
| **Temps de réponse moyen** | `2.50 ms` |

### Question 4.2
Non, la moyenne masque complètement les pics de latence et les percentiles élevés (ex: p95/p99) subis par certains utilisateurs.

---
---

# Partie 5 - Évaluation des performances et qualification de charge

## Configuration du scénario Locust

| Décision | Contrainte | Votre valeur |
| :--- | :--- | :--- |
| **Temps de réflexion** | Non nul | `between(2, 5)` secondes |
| **Poids des tâches** | Trois entiers non égaux | `/predict`: **10**, `/health`: **2**, `/model/info`: **1** |
| **Variables perturbées** | Au moins 2 variables | `age_approx`, `clin_size_long_diam_mm`, `tbp_lv_a` |

### Question 5.1
* **Poids `/predict` (10) :** C'est l'appel métier principal effectué en continu par les praticiens.
* **Poids `/health` (2) :** Représente les pings de vérification automatiques périodiques.
* **Poids `/model/info` (1) :** Consultation très occasionnelle des métadonnées du modèle.

## Mesure 13 - Résultats des paliers de charge

| Palier | Utilisateurs | Débit (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Taux d'échec (%) | Échecs les plus fréquents |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | 5 | 1.22 | 48 | 52 | 55 | 0.0% | Aucun |
| **2** | 20 | 5.69 | 47 | 51 | 56 | 0.0% | Aucun |
| **3** | 50 | 13.99 | 49 | 56 | 66 | 0.0% | Aucun |
| **4** | 100 | 26.18 | 84 | 130 | 190 | 0.0% | Aucun |

## Mesure 14 - Ligne de base réseau

| Ligne de base | Votre valeur |
| :--- | :--- |
| **Temps d'établissement de connexion (médiane sur 20 mesures)** | 69.23 ms |
| **Part que cela représente dans votre p50 du palier 1** | 144.23 % |

## Critère de rupture posé avant mesure

| Élément du critère | Votre choix | Justification en une ligne |
| :--- | :--- | :--- |
| **Seuil de taux d'échec jugé inacceptable** | **> 1.0 %** | Au-delà de 1%, l'expérience utilisateur et les consultations sont dégradées. |
| **Seuil de p95 jugé inacceptable** | **> 3 fois** le p95 du palier 1 | Au-delà du triple du temps nominal, le praticien ressent un ralentissement dérangeant. |
| **Règle de franchissement** | **Atteint dès que l'un des deux critères est franchi.** | |

## Mesure 15 - Synthèse du point de rupture

| Conclusion | Votre réponse |
| :--- | :--- |
| **Palier où le critère est franchi pour la première fois** | **Aucun palier (Rupture non atteinte à 100 users)** |
| **Nombre d'utilisateurs simultanés supporté** | **> 100 utilisateurs** |
| **Débit maximal observé avant dégradation** | **26.18 requêtes / seconde** |
| **Ressource qui sature en premier** | **CPU** |
| **Ce que valait Http5xx au palier le plus chargé** | **0** |

### Question 5.2
Au palier 4 (100 users), on observe un écart entre le **p50 (84ms)** et le **p99 (190ms)**.
Cela montre que la majorité des requêtes restent très rapides, mais que les percentiles extrêmes commencent à ralentir un peu à cause du queuing des requêtes concurrentes. Pour le praticien, 1% des appels prendra ~190ms au lieu de 84ms, ce qui reste quasi imperceptible.

### Question 5.3 - Engagement de service
> *"Jusqu'à 100 utilisateurs simultanés, 95 % des prédictions sont rendues en moins de 130 ms, avec moins de 0.0 % d'échecs."*

### Question 5.4 - Passage à l'échelle
Pour supporter deux fois plus de charge :
1. **Scale Up (Vertical) :** Augmenter le SKU du plan App Service (ex: passer de B1 à B2 ou P1v2).
2. **Scale Out (Horizontal) :** Augmenter le nombre d'instances (passer de 1 à 2 instances derrière le load balancer).

**Choix :** Je testerais le **Scale Out** en premier car notre conteneur est *stateless*, ce qui permet de doubler la capacité de traitement CPU de façon linéaire sans changer de famille de prix.

### Question 5.5
Si le modèle était rechargé à partir du disque à chaque requête, les E/S disque et l'instanciation feraient exploser le temps de traitement.
L'impact serait très visible sur la **latence (p50/p95/p99)** dans le tableau. Le débit aux premiers paliers ne bougerait pas trop car il est limité par le temps de pause des utilisateurs virtuels et non par le serveur.

---
---

# Partie 6 - Gouvernance : journalisation des inférences

## Grille de décision (Section 6.1)

| Donnée | Journaliser ? | Forme | Justification |
| :--- | :--- | :--- | :--- |
| **Horodatage de la requête, en UTC** | Toujours | Brut | Indispensable pour la chronologie des événements. |
| **Identifiant de corrélation de la requête** | Toujours | Brut, généré si absent | Permet de lier une ligne de log à un appel client/incident. |
| **Version du modèle et digest de l'image** | Toujours | Brut | Traçabilité de l'artefact exact ayant produit la décision. |
| **Identifiant du patient (`patient_id`)** | **Jamais** | **Exclu / Masqué** | Donnée nominative/personnelle sensible (RGPD). |
| **Identifiant de la lésion (`isic_id`)** | **Sous conditions** | **Pseudonymisé / Hashé** | Permet le suivi de la lésion sans exposer l'identité directe. |
| **Âge et sexe (`age_approx`, `sex`)** | **Oui (agrégé)** | **Non nominatif** | Utile pour analyser les biais du modèle. |
| **Site anatomique (`anatom_site_general`)** | **Toujours** | **Brut** | Donnée médicale non nominative utile pour le suivi clinique. |
| **Valeurs brutes morphologiques (`tbp_lv_*`)** | **Jamais** | **Exclu** | Trop lourd et risque de fuite de données de santé brutes. |
| **Probabilité maligne prédite** | Toujours | Brut (float) | Essentiel pour la traçabilité de la prédiction. |
| **Seuil appliqué et rappel visé** | Toujours | Brut | Permet de comprendre pourquoi une décision a été prise. |
| **Décision rendue (`a_examiner` / `surveillance`)** | Toujours | Brut | Output métier final renvoyé au praticien. |
| **Latence d'inférence** | Toujours | Brut (ms) | Monitoring des performances techniques. |
| **Code HTTP et message d'erreur** | Toujours | Brut | Nécessaire pour le debug technique. |
| **Adresse IP source de l'appel** | **Jamais** | **Exclue** | Donnée personnelle (RGPD) à gérer au niveau réseau/Azure. |
| **Identité du praticien** | **Jamais en clair** | **ID Technique** | Évite l'exposition directe de l'identité du professionnel. |
| **Jeton d'authentification ou clé d'API** | **Jamais** | **Exclu** | Risque critique de sécurité/fuite de credentials. |
| **Sel de pseudonymisation `INFERENCE_LOG_SALT`** | **Jamais** | **Secret** | Doit rester strictly confidentiel dans l'environnement. |

### Question 6.1 - Qualification RGPD
1. **`tbp_lv_*` seules :** Neither Article 4 nor Article 9 (Données techniques anonymes si aucun recoupement n'est possible).
2. **`tbp_lv_*` + `patient_id` :** **Article 4 et Article 9**. L'identifiant rend la personne identifiable et les variables sont liées à sa santé.
3. **`tbp_lv_*` + `age_approx` + `sex` + `anatom_site_general` (sans `patient_id`) :** **Article 4 et Article 9**. Faisceau de quasi-identifiants permettant la réidentification par re-croisement.
4. **Probabilité maligne prédite + patient identifiable :** **Article 4 et Article 9**. Le fait que la donnée soit générée par une IA ne change rien : elle qualifie l'état de santé d'un individu.

### Question 6.2 - Quasi-identifiants
En croisant 3 à 4 variables (ex: âge, sexe, localisation, taille de lésion), un individu devient très facilement réidentifiable dans un centre médical local.
La mesure statistique à utiliser est le **k-anonymat ($k$-anonymity)**.

### Question 6.3 - Analyse de fuite de logs
Si les champs "Toujours" fuitent : l'attaquant apprend les volumes d'utilisation, les versions de logiciels, les statistiques médicales globales et les métriques de performance, mais aucune identité patient n'est compromise. Une fuite de probabilité reste un problème de confidentialité médicale globale mais sans lien patient, son impact est fortement limité.

## Format de ligne de log JSON (Section 6.2)

```json
{
  "ts": "2026-10-26T15:12:00.123Z",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef0123456789",
  "model_version": "1.0.0",
  "image_digest": "sha256:230b01a8678f6cce5944bf22ec9f1b992821e7f3995c3ecd970ee546c67f6614",
  "patient_ref": "4a5f8c9b2d1e3f6a",
  "probabilite_maligne": 0.0412,
  "seuil_applique": 0.99859,
  "decision": "benigne",
  "inference_ms": 42.5,
  "http_status": 200,
  "input_schema_version": "1.0.0",
  "covariables_echantillon": {
    "age_approx": 45,
    "clin_size_long_diam_mm": 5.2
  }
}
```

### Question 6.4 - Pseudonymisation et Salt
1. **Utilité du sel :** Sans sel, un hachage `SHA-256(patient_id)` est vulnérable aux attaques par dictionnaire/rainbow tables, car il n'y a que 1 042 patients avec des IDs très réguliers. Le sel rajoute de l'aléa irréversible.
2. **Stabilité du `patient_ref` :**
   * *Avantage :* Permet de suivre plusieurs lésions chez un même patient au fil du temps.
   * *Faiblesse :* Si un patient est réidentifié une fois, tout son historique lié à ce hash est compromis.
3. **Remontée `patient_ref` -> `patient_id` :** Seul un admin autorisé possédant la table de correspondance sécurisée et isolée (hors environnement de prod) peut faire le lien.
4. **Rotation du sel :** Modifier le sel invalide tous les anciens `patient_ref`. C'est une propriété de sécurité appelée **crypto-shredding** (destruction cryptographique de l'historique).

## Durées de conservation (Section 6.3)

| Catégorie de trace | Durée de conservation | Besoin qui la justifie | Ce qui se passe à l'échéance |
| :--- | :--- | :--- | :--- |
| **Journal d'inférence complet** | 30 jours | Analyse de dérive et debug immédiat | Purge automatique Blob Storage |
| **Journal d'erreurs applicatives** | 90 jours | Support technique et maintenance | Purge Log Analytics |
| **Métriques agrégées (sans PII)** | 1 an | Monitoring global de charge | Archivage / Rétention longue |
| **Journal d'accès plateforme** | 6 mois | Obligation de sécurité/Audit Azure | Supprimé automatiquement |

### Question 6.5
Les deux exigences opposées sont la **minimisation des données** (RGPD) et la **capacité d'audit / traçabilité**.
On concilie les deux en séparant les métadonnées techniques anonymes (conservées longtemps) des données personnelles/identifiants (purgés rapidement).

### Question 6.6
La purge doit être configurée au niveau de **l'infrastructure cloud (Azure Log Analytics / Blob Storage Lifecycle policies)**. Si elle est faite uniquement en Python, la plateforme Azure gardera ses propres copies des logs indéfiniment.

---
---

# Partie 7 - Nettoyage obligatoire

## Mesure 16 - Inventaire de ce qui a réellement été créé, avant destruction

| Relevé avant destruction | Votre valeur |
| :--- | :--- |
| **Nombre de ressources dans le groupe** | `2` (App Service + App Service Plan) |
| **Types de ressources listés** | `Microsoft.Web/serverfarms`, `Microsoft.Web/sites` |
| **Le registre ACR est-il dans ce groupe ou dans le groupe du registre?** | Dans le groupe dédié au registre (`rg-dermascan-registre-ap24`) |

## Mesure 17 - Contrôles de destruction

| Contrôle de fin de séance | Votre observation |
| :--- | :--- |
| **Le groupe apparaît-il encore ?** | Non (`az group exists` renvoie `false`) |
| **Reste-t-il une attribution de rôle sur le registre ?** | Non, supprimée avec `az role assignment delete` |
| **Le groupe du registre est-il, lui, toujours debout?** | Oui |
| **Crédit restant, relevé dans Cost Management** | ~87,00 € |
| **Écart avec le relevé de la séance précédente** | -0,75 € |

### Question 7.1
Ayant séparé l'infrastructure de déploiement (S3) et le stockage de l'image/registre (S1) dans deux groupes de ressources distincts, la suppression du groupe `rg-dermascan-s3-ap24` supprime l'App Service sans risquer d'effacer le registre ACR indispensable pour les prochains TPs. Si tout était dans le même groupe, il aurait fallu supprimer les ressources une par une à la main.