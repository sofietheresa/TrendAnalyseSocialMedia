Here's an updated version of your `README.md` to reflect the current state of the project, including the TikTok integration and deployment via Render:

---

# TrendSage – Social Media Trend Discovery for Publishing

**TrendSage** is an open-source machine learning project designed to automatically discover trending topics and sentiments from social media platforms such as **Reddit**, **YouTube**, and **TikTok**. This tool is intended for publishers, authors, content creators, and media professionals who want to identify emerging trends before they go mainstream.

The project includes scheduled scraping, unsupervised topic modeling, sentiment analysis, and intuitive dashboards – built using free, open-source Python tools and deployed via **Render** and **GitHub Actions**.

---

## ✅ Project Goals

- Automatically extract trending social media data multiple times per day
- Identify and group emerging topics using unsupervised topic modeling
- Analyze sentiment around trending content
- Visualize trends and evolution of topics and sentiment in a clean interface
- Run reliably in a containerized environment like Render

---

## 📁 Project Structure

```text
trendsage/
│
├── api/                  # FastAPI application
│   └── main.py
│
├── scheduler/            # Scheduled scrapers and orchestration
│   ├── run_all_scrapers.py
│   └── jobs/
│       ├── reddit_scraper.py
│       ├── youtube_scraper.py
│       └── tiktok_scraper.py
│
├── data/
│   ├── raw/              # Scraped CSV files
│   └── processed/        # Cleaned and enriched data
│
├── logs/                 # Scraper logs
│
├── notebooks/            # Analysis and development
│
├── models/               # Saved models for topic/sentiment analysis
│
├── app/                  # Streamlit dashboard (WIP)
│
├── .env                  # Environment variables (not tracked)
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local multi-service setup
├── requirements.txt      # Python dependencies
├── Makefile              # Common commands
├── README.md             # This file
└── scheduler.yaml        # GitHub Actions workflow
```

---

## ⚙️ How It Works

### 1. Data Collection

- Reddit via `PRAW`
- YouTube via YouTube Data API v3
- TikTok via `TikTokApi` (browser automation with Playwright)

### 2. Scraper Scheduling

- `/run-scrapers` endpoint triggers all scrapers
- Automatically scheduled every 15 minutes via **GitHub Actions**
- Secured with API token-based authentication

### 3. Logging and Storage

- Logs for each platform are stored under `/app/logs/*.log`
- Raw data saved in `/app/data/raw/*.csv`
- Data and logs can be downloaded via HTTP endpoints or `make sync`

---

## 🚀 Deployment (Render + GitHub Actions)

1. **Deploy backend to [Render.com](https://render.com/)**

   - Use FastAPI + Uvicorn
   - Set up `.env` variables in Render (e.g. `YT_KEY`, `REDDIT_ID`, `MS_TOKEN`, `API_SECRET`)

2. **Trigger scrapers via GitHub Actions**

   ```yaml
   name: Trigger Scraper Every 15 Minutes

   on:
     schedule:
       - cron: "*/15 * * * *"
     workflow_dispatch:

   jobs:
     run-scraper:
       runs-on: ubuntu-latest
       steps:
         - name: Trigger Render scraper endpoint
           run: |
             curl -X POST https://trendanalysesocialmedia.onrender.com/run-scrapers \
                  -H "Authorization: Bearer ${{ secrets.API_SECRET }}"
   ```

3. **Secure sync to local machine**

   ```bash
   make sync
   ```

---

## 🧪 Run TikTok scraper (manual)

```bash
podman run --rm \
  --env-file .env \
  -v "${PWD}:/app/src" \
  tiktokapi:latest
```

---

## ✅ Status

- [x] Project initialized
- [x] Scraper jobs implemented for Reddit, YouTube, TikTok
- [x] Logging and persistent data storage working
- [x] FastAPI deployed and secured
- [x] GitHub Actions integration live
- [ ] Topic modeling pipeline
- [ ] Sentiment analysis pipeline
- [ ] Streamlit dashboard

---

Let me know if you want this written directly to your `README.md` file.
