# === Konfiguration ===
CONTAINER_NAME=scraper-container
IMAGE_NAME=social-scraper
ENV_FILE=.env
LOG_DIR=./logs

# === Build Container ===
build:
	podman build -t $(IMAGE_NAME) .

# === Run Container (detached) ===
run:
	podman run -d --name $(CONTAINER_NAME) --env-file $(ENV_FILE) -v "$(PWD)/logs:/logs" $(IMAGE_NAME)

# === Stop + Remove Container ===
clean:
	podman stop $(CONTAINER_NAME) || true
	podman rm $(CONTAINER_NAME) || true

# === Restart ===
rebuild: clean build run

# === Live Logs ===
logs:
	podman logs -f $(CONTAINER_NAME)

# === Shell in Container ===
bash:
	podman exec -it $(CONTAINER_NAME) bash

# === Cron überprüfen ===
cron:
	podman exec -it $(CONTAINER_NAME) crontab -l

# === TikTok manuell testen ===
run-tiktok:
	podman exec -it $(CONTAINER_NAME) python /app/src/tiktok_scraper.py

# === Notebook (lokal öffnen, nicht im Container) ===
notebook:
	jupyter notebook app/notebooks/

# === Hilfe anzeigen ===
help:
	@echo "📦 Available commands:"
	@echo "  make build       – Docker-Image bauen"
	@echo "  make run         – Container starten"
	@echo "  make clean       – Container stoppen & löschen"
	@echo "  make rebuild     – Neu bauen + starten"
	@echo "  make logs        – Container-Logs anzeigen"
	@echo "  make bash        – In Container bash öffnen"
	@echo "  make cron        – Cronjobs anzeigen"
	@echo "  make run-tiktok  – TikTok-Scraper manuell ausführen"
	@echo "  make notebook    – Notebook lokal öffnen"
