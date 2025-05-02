include .env
export

API_URL=https://trendanalysesocialmedia.onrender.com
TOKEN= Bearer $(API_SECRET) 

FILES=reddit_data.csv tiktok_data.csv youtube_data.csv
LOGS=reddit.log tiktok.log youtube.log

.PHONY: sync

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

	@echo "\n⬇️  Lade Logs herunter ..."
	@mkdir -p logs
	@for log in $(LOGS); do \
		curl -s $(API_URL)/logs/download/$$log -H "Authorization: $(TOKEN)" -o logs/$$log; \
	done

	@echo "\n✅ Alle Dateien synchronisiert."


# Variablen
IMAGE_NAME=trendsage
CONTAINER_NAME=trend_scheduler
PORT=8080
CONTAINER_PORT=10000

# 🧱 Container-Image bauen
build:
	podman build -t $(IMAGE_NAME) .

# 🚀 Container interaktiv starten
run:
	podman run -p $(PORT):$(CONTAINER_PORT) \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME)

# 🔁 Container im Hintergrund starten
run-detached:
	podman run -d -p $(PORT):$(CONTAINER_PORT) \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME)

# 🧼 Container stoppen und löschen
clean:
	-podman stop $(CONTAINER_NAME)
	-podman rm $(CONTAINER_NAME)

# 🧨 Container + Logs/Daten löschen
clean-all: clean
	rm -rf logs/* data/*

# 🔄 Container neu starten
restart:
	podman restart $(CONTAINER_NAME)

# 📋 Container-Logs live anzeigen
logs:
	podman logs -f $(CONTAINER_NAME)

# 🧪 Scraper lokal ausführen
run-all-scrapers:
	python scheduler/run_all_scrapers.py

# 🔍 Shell im Container öffnen
shell:
	podman exec -it $(CONTAINER_NAME) /bin/sh
