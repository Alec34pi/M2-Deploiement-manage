import json
import random
from locust import HttpUser, task, between


with open("charge.json", "r") as f:
    BASE_PAYLOAD = json.load(f)

def charge_utile_perturbee():
    """
    Génère une copie de la charge de base en perturbant légèrement 
    quelques variables numériques dans les plages valides relevées en S2.
    """
    payload = json.loads(json.dumps(BASE_PAYLOAD))
    
    
    if "age_approx" in payload:
        payload["age_approx"] = max(18, min(90, payload["age_approx"] + random.randint(-3, 3)))
        
        
    if "clin_size_long_diam_mm" in payload:
        payload["clin_size_long_diam_mm"] = round(max(0.5, payload["clin_size_long_diam_mm"] + random.uniform(-0.5, 0.5)), 2)
        
        
    if "tbp_lv_a" in payload:
        payload["tbp_lv_a"] = round(payload["tbp_lv_a"] + random.uniform(-1.0, 1.0), 2)
        
    return payload

class DermascanUser(HttpUser):
    
    wait_time = between(2.0, 5.0)

    @task(10)
    def predire(self):
        """Tâche principale : soumission de la lésion pour prédiction"""
        payload = charge_utile_perturbee()
        with self.client.post("/predict", json=payload, name="POST /predict", catch_response=True) as reponse:
            if reponse.status_code == 200:
                reponse.success()
            else:
                reponse.failure(f"statut {reponse.status_code}")

    @task(2)
    def verifier_sante(self):
        """Vérification de la santé de l'API (consultée périodiquement)"""
        self.client.get("/health", name="GET /health")

    @task(1)
    def info_modele(self):
        """Consultation des métadonnées du modèle (action plus rare)"""
        self.client.get("/model/info", name="GET /model/info")