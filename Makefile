# --------------------------------------------
# ⚙️ SCRAPER LOKAL AUSFÜHREN
# --------------------------------------------

.PHONY: run-reddit run-tiktok run-youtube run-scheduler

# Nur Reddit-Scraper ausführen
run-reddit:
	@echo "🚀 Starte Reddit-Scraper..."
	python -c "from src.scheduler.jobs.reddit_scraper import scrape_reddit; scrape_reddit()"
	@echo "✅ Reddit-Scraping abgeschlossen."

# Nur TikTok-Scraper ausführen
run-tiktok:
	@echo "🚀 Starte TikTok-Scraper..."
	python -c "from src.scheduler.jobs.tiktok_scraper import trending_videos; trending_videos()"
	@echo "✅ TikTok-Scraping abgeschlossen."

# Nur YouTube-Scraper ausführen
run-youtube:
	@echo "🚀 Starte YouTube-Scraper..."
	python -c "from src.scheduler.jobs.youtube_scraper import scrape_youtube_trending; scrape_youtube_trending()"
	@echo "✅ YouTube-Scraping abgeschlossen."

# Hauptscheduler für automatische Ausführung
run-scheduler:
	@echo "🕒 Starte Hauptscheduler für automatische Ausführung..."
	python src/scheduler/main_scraper.py

# --------------------------------------------
# 🛠️ ENTWICKLUNG & WARTUNG
# --------------------------------------------

.PHONY: install start clean

# 📦 Abhängigkeiten installieren
install:
	pip install -r requirements.txt

# 🚀 FastAPI-Server starten
start:
	uvicorn src.main:app --reload

# 🧹 Temporäre Dateien aufräumen
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	rm -rf data/processed/*.csv data/processed/*.json
	rm -rf .venv
	echo "Cleaned up temporary and output files."

# --------------------------------------------
# 🌐 FRONTEND VERWALTUNG
# --------------------------------------------

PORT ?= 3000
	
# ▶️ Startet das Frontend
start-frontend:
	cd frontend && npm start

# 🔁 Frontend neu starten
restart-frontend:
	-@kill -9 $$(lsof -t -i :$(PORT)) 2>/dev/null || true
	sleep 1
	make start-frontend

# 🛑 Beendet Frontend-Prozess auf dem Port
stop-frontend:
	-@kill -9 $$(lsof -t -i :$(PORT)) 2>/dev/null || echo "✅ Kein laufender Frontend-Prozess gefunden."

