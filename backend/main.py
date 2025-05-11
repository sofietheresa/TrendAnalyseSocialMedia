from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import subprocess
from pathlib import Path

app = FastAPI()

# Endpoint to fetch scraped data information
@app.get("/data")
async def get_data_info():
    # Placeholder for fetching data info
    return JSONResponse(content={"count": 100, "last_scraped": "2023-10-01"})

# Endpoint to fetch logs
@app.get("/logs")
async def get_logs():
    log_file_path = Path("logs/some_log_file.log")
    if not log_file_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    with open(log_file_path, "r") as log_file:
        logs = log_file.read()
    return JSONResponse(content={"logs": logs})

# Endpoint to control the pipeline
@app.post("/pipeline/start")
async def start_pipeline():
    try:
        subprocess.Popen(["python", "src/scheduler/run_all_scrapers.py"])
        return JSONResponse(content={"status": "Pipeline started"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipeline/stop")
async def stop_pipeline():
    # Placeholder for stopping the pipeline
    return JSONResponse(content={"status": "Pipeline stopped"}) 