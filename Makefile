# Makefile für TikTok Trendanalyse Projekt

# === Variablen ===
PYTHON=python
DOCKER_IMAGE_NAME=tiktokapi
SRC_DIR=app/src
DATA_DIR=app/data
ENV_FILE=.env

# === Targets ===

# Container bauen
build:
	podman build -t $(DOCKER_IMAGE_NAME) .

# TikTok-Daten abrufen
tiktok:
	podman run --rm \
		--env-file $(ENV_FILE) \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME) \
		$(PYTHON) $(SRC_DIR)/tiktok.py

# Twitter-Daten abrufen (analog)
twitter:
	podman run --rm \
		--env-file $(ENV_FILE) \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME) \
		$(PYTHON) $(SRC_DIR)/twitter.py

# Reddit-Daten abrufen (analog)
reddit:
	podman run --rm \
		--env-file $(ENV_FILE) \
		-v $(PWD):/app \
		$(DOCKER_IMAGE_NAME) \
		$(PYTHON) $(SRC_DIR)/reddit.py

# Alle Datenquellen gleichzeitig abrufen
all: tiktok twitter reddit

# Aufräumen
clean:
	rm -f $(DATA_DIR)/*.csv

.PHONY: build tiktok twitter reddit all clean
