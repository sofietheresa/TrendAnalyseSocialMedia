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

# 🔁 Nur Scraper via API triggern (z. B. für Testzwecke)
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
		python scheduler/scraper_trigger.py

# --------------------------------------------
# 🧱 PODMAN CONTAINER-STEUERUNG
# --------------------------------------------

.PHONY: build run run-detached clean clean-all restart logs shell

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
clean:
	-podman stop $(CONTAINER_NAME)
	-podman rm $(CONTAINER_NAME)

# 🧨 Alles löschen (inkl. lokale Logs & Daten)
clean-all: clean
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
	python scheduler/run_all_scrapers.py

# --------------------------------------------
# 🐳 OPTIONAL: DOCKER-COMPOSE UNTERSTÜTZUNG
# --------------------------------------------

.PHONY: compose-up compose-logs

compose-up:
	docker-compose up --build

compose-logs:
	docker-compose logs -f scraper-trigger
