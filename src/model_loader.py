import os
import requests

MODEL_URLS = {
    "modell1": "https://your-model-storage/modell1.h5",
    "modell2": "https://your-model-storage/modell2.h5",
    "modell3": "https://your-model-storage/modell3.h5",
}
MODEL_DIR = "/app/models"

def download_models():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_URLS.items():
        path = os.path.join(MODEL_DIR, f"{name}.h5")
        if not os.path.exists(path):
            print(f"Lade {name} von {url} ...")
            r = requests.get(url)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)

# Optional: Funktion, die prüft, ob alle Modelle vorhanden sind
def models_exist():
    return all(os.path.exists(os.path.join(MODEL_DIR, f"{name}.h5")) for name in MODEL_URLS)
