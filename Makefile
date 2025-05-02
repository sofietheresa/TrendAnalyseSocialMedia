.PHONY: build run run-detached clean restart logs run-all-scrapers shell clean-all

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
