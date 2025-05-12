# --------------------------------------------
# 🔧 ENV-VARIABLEN & BASISKONFIGURATION
# --------------------------------------------

include .env
export

API_URL=https://trendanalysesocialmedia.onrender.com
TOKEN=Bearer $(API_SECRET)

FILES=reddit_data.csv tiktok_data.csv youtube_data.csv
LOGS=reddit.log tiktok.log youtube.log

IMAGE_NAME=trendsage
CONTAINER_NAME=trend_scheduler
PORT=8080
CONTAINER_PORT=10000

# --------------------------------------------
# 📡 REMOTE SCRAPING & DATEN-SYNC
# --------------------------------------------

.PHONY: sync trigger-api trigger-loop

# ⏱️ Scraping-Job über API auf Render auslösen + Daten/Logs lokal abholen
sync:
	curl -X POST $(API_URL)/run-scrapers \
		-H "Authorization: $(TOKEN)"

	@echo "\n⬇️  Lade Daten herunter & hänge sie an bestehende Dateien an ..."
	@mkdir -p data/raw
	@for file in $(FILES); do \
		tmp="data/raw/tmp_$$file"; \
		curl -s $(API_URL)/data/download/$$file -H "Authorization: $(TOKEN)" -o $$tmp; \
		if [ -f data/raw/$$file ]; then \
			tail -n +2 $$tmp >> data/raw/$$file; \
		else \
			mv $$tmp data/raw/$$file; \
		fi; \
		rm -f $$tmp; \
	done

	@echo "\n⬇️  Lade Logs herunter & hänge sie an bestehende Dateien an ..."
	@mkdir -p logs
	@for log in $(LOGS); do \
		tmp="logs/tmp_$$log"; \
		curl -s $(API_URL)/logs/download/$$log -H "Authorization: $(TOKEN)" -o $$tmp; \
		if [ -f logs/$$log ]; then \
			cat $$tmp >> logs/$$log; \
		else \
			mv $$tmp logs/$$log; \
		fi; \
		rm -f $$tmp; \
	done

	@echo "\n✅ Alle Dateien synchronisiert."

# 🔁 Nur Scraper via API triggern (z. B. für Testzwecke)
trigger-api:
	curl -X POST $(API_URL)/run-scrapers \
		-H "Authorization: $(TOKEN)"

# 🕓 Lokal laufende Endlosschleife, die alle 15min Render abfragt & lokal scrapt
trigger-loop:
	podman run -it --rm \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME) \
		python src/scheduler/scraper_trigger.py

# --------------------------------------------
# 🧱 PODMAN CONTAINER-STEUERUNG
# --------------------------------------------

.PHONY: build run run-detached clean-container restart logs shell

# 📦 Container-Image bauen
build:
	podman build -t $(IMAGE_NAME) .

# 🚀 Container interaktiv starten (API lokal aufrufbar)
run:
	podman run -p $(PORT):$(CONTAINER_PORT) \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME)

# 🔁 Container im Hintergrund starten
run-detached:
	podman run -d -p $(PORT):$(CONTAINER_PORT) \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		-w /app \
		$(IMAGE_NAME)

# 🧼 Container stoppen und löschen
clean-container:
	-podman stop $(CONTAINER_NAME)
	-podman rm $(CONTAINER_NAME)

# 🧨 Alles löschen (inkl. lokale Logs & Daten)
clean-all: clean-container
	rm -rf logs/* data/*

# 🔄 Container neustarten
restart:
	podman restart $(CONTAINER_NAME)

# 📋 Live-Logs anzeigen
logs:
	podman logs -f $(CONTAINER_NAME)

# 🔍 Interaktive Shell im Container öffnen
shell:
	podman exec -it $(CONTAINER_NAME) /bin/sh

# --------------------------------------------
# ⚙️ SCRAPER LOKAL AUSFÜHREN (zum Debuggen)
# --------------------------------------------

.PHONY: run-all-scrapers

run-all-scrapers:
	python src/scheduler/run_all_scrapers.py

# --------------------------------------------
# 🐳 OPTIONAL: DOCKER-COMPOSE UNTERSTÜTZUNG
# --------------------------------------------

.PHONY: compose-up compose-logs

compose-up:
	docker-compose up --build

compose-logs:
	docker-compose logs -f scraper-trigger

# --------------------------------------------
# 🛠️ ENTWICKLUNG & WARTUNG
# --------------------------------------------

.PHONY: install start qdrant stop-qdrant lint test pipeline download-nltk clean

# 📦 Abhängigkeiten installieren
install:
	pip install -e .

# 🚀 FastAPI-Server starten
start:
	uvicorn src.main:app --reload

# 🔍 Qdrant Vektordatenbank starten
qdrant:
	docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 🛑 Qdrant stoppen
stop-qdrant:
	docker stop qdrant || true
	docker rm qdrant || true

# ✨ Code formatieren und linten
lint:
	black src/ || true
	flake8 src/ || true

# 🧪 Tests ausführen
test:
	pytest || echo "No tests found."

# 🔄 Pipeline ausführen
pipeline:
	python src/setup_pipeline.py

# 📚 NLTK-Ressourcen herunterladen
download-nltk:
	python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng')"

# 🧹 Temporäre Dateien aufräumen
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	rm -rf data/processed/*.csv data/processed/*.json
	rm -rf .venv
	echo "Cleaned up temporary and output files."

# Add this section to your Makefile

.PHONY: restart-server

# 🔄 Restart FastAPI server
restart-server:
	@echo "Stopping any running FastAPI server..."
	-pkill -f "uvicorn src.main:app" || true
	@echo "Starting FastAPI server..."
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

	# Port, auf dem Streamlit läuft
PORT ?= 8501
APP ?= frontend/app.py  # Pfad zu deiner Streamlit-Hauptdatei

# ▶️ Startet das Streamlit-Frontend
start-frontend:
	streamlit run $(APP) --server.port=$(PORT)

# 🔁 Startet neu, beendet ggf. laufende Instanz
restart-frontend:
	-@kill -9 $$(lsof -t -i :$(PORT)) 2>/dev/null || true
	sleep 1
	make start-frontend

# 🛑 Beendet Frontend-Prozess auf dem Port
stop-frontend:
	-@kill -9 $$(lsof -t -i :$(PORT)) 2>/dev/null || echo "✅ Kein laufender Streamlit-Prozess gefunden."

# 📂 Öffnet das Frontend im Browser
open-frontend:
	python -m webbrowser http://localhost:$(PORT)

# --------------------------------------------
# ☁️ CLOUDFLARE TUNNEL & AUTHENTIFIZIERUNG
# --------------------------------------------

.PHONY: tunnel tunnel-login tunnel-route db-tunnel

# 🔑 Cloudflare Login & Tunnel Setup
tunnel-login:
	cloudflared tunnel login

# 🚇 Tunnel erstellen und konfigurieren
tunnel-create:
	@if [ -z "$(TUNNEL_NAME)" ]; then \
		echo "Error: TUNNEL_NAME nicht gesetzt. Bitte setzen Sie die Variable, z.B.: make tunnel-create TUNNEL_NAME=mein-tunnel"; \
		exit 1; \
	fi
	cloudflared tunnel create $(TUNNEL_NAME)
	@echo "Erstelle config.yml..."
	@echo "tunnel: $(TUNNEL_NAME)" > ~/.cloudflared/config.yml
	@echo "credentials-file: /Users/$(USER)/.cloudflared/$(TUNNEL_NAME).json" >> ~/.cloudflared/config.yml
	@echo "ingress:" >> ~/.cloudflared/config.yml
	@echo "  - hostname: api.$(DOMAIN)" >> ~/.cloudflared/config.yml
	@echo "    service: http://localhost:8000" >> ~/.cloudflared/config.yml
	@echo "    originRequest:" >> ~/.cloudflared/config.yml
	@echo "      noTLSVerify: true" >> ~/.cloudflared/config.yml
	@echo "      headers:" >> ~/.cloudflared/config.yml
	@echo "        X-API-Key: \${API_KEY}" >> ~/.cloudflared/config.yml
	@echo "  - hostname: app.$(DOMAIN)" >> ~/.cloudflared/config.yml
	@echo "    service: http://localhost:3000" >> ~/.cloudflared/config.yml
	@echo "  - hostname: db.$(DOMAIN)" >> ~/.cloudflared/config.yml
	@echo "    service: http://localhost:6333" >> ~/.cloudflared/config.yml
	@echo "  - service: http_status:404" >> ~/.cloudflared/config.yml

# 🌐 DNS Routen einrichten
tunnel-route:
	@if [ -z "$(TUNNEL_NAME)" ] || [ -z "$(DOMAIN)" ]; then \
		echo "Error: TUNNEL_NAME oder DOMAIN nicht gesetzt"; \
		echo "Verwendung: make tunnel-route TUNNEL_NAME=mein-tunnel DOMAIN=meine-domain.com"; \
		exit 1; \
	fi
	cloudflared tunnel route dns $(TUNNEL_NAME) api.$(DOMAIN)
	cloudflared tunnel route dns $(TUNNEL_NAME) app.$(DOMAIN)
	cloudflared tunnel route dns $(TUNNEL_NAME) db.$(DOMAIN)

# 🚀 Tunnel starten
tunnel:
	@if [ -z "$(TUNNEL_NAME)" ]; then \
		echo "Error: TUNNEL_NAME nicht gesetzt. Bitte setzen Sie die Variable, z.B.: make tunnel TUNNEL_NAME=mein-tunnel"; \
		exit 1; \
	fi
	cloudflared tunnel run $(TUNNEL_NAME)

# --------------------------------------------

