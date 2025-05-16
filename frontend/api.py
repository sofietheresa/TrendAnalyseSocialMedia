from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import create_engine, text
import uvicorn
import os
from datetime import datetime, timedelta
import urllib.parse
import random
import json

app = FastAPI(title="Social Media Trend Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React Dev Server
        "https://trendanalysesocialmedia.vercel.app",  # Produktions-URL
        "https://trendanalysesocialmedia-production.up.railway.app",  # Railway App URL
        "https://trend-analyse-social-media.vercel.app"  # Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    result = urllib.parse.urlparse(url)
    conn_str = f"postgresql://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return create_engine(conn_str)

# Dictionary für die Datenbankverbindungen
db_engines = {}

@app.get("/api/scraper-status")
async def get_scraper_status():
    try:
        # Check if any data was added in the last 20 minutes to determine if scraper is running
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        # Initialize database engines if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_engines:
                db_engines[db] = get_db_connection(db)
        
        # Check Reddit
        with db_engines['reddit_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM reddit_data"))
            count, last_update = result.fetchone()
            status['reddit'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check TikTok
        with db_engines['tiktok_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM tiktok_data"))
            count, last_update = result.fetchone()
            status['tiktok'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check YouTube
        with db_engines['youtube_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM youtube_data"))
            count, last_update = result.fetchone()
            status['youtube'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/daily-stats")
async def get_daily_stats():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        # Initialize database engines if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_engines:
                db_engines[db] = get_db_connection(db)
        
        # Get Reddit daily stats
        with db_engines['reddit_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM reddit_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['reddit'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        # Get TikTok daily stats
        with db_engines['tiktok_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM tiktok_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['tiktok'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        # Get YouTube daily stats
        with db_engines['youtube_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM youtube_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['youtube'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-data")
async def get_recent_data(platform: str = "reddit", limit: int = 10):
    try:
        limit = min(int(limit), 100)  # Limit to max 100 records
        
        print(f"Fetching {platform} data with limit {limit}")
        
        # Ensure platform is valid
        if platform not in ['reddit', 'tiktok', 'youtube']:
            raise HTTPException(status_code=400, detail="Invalid platform specified")
        
        # Initialize database engine if it doesn't exist
        db_name = f"{platform}_data"
        if db_name not in db_engines:
            print(f"Initializing database connection for {db_name}")
            db_engines[db_name] = get_db_connection(db_name)
        
        # Try both table formats: platform_data and platform_posts
        table_names = [f"{platform}_data", f"{platform}_posts"]
        
        # Dynamically create the appropriate column selection query based on platform
        if platform == 'reddit':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, title, text, author, created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, title, text, author, created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
                
        elif platform == 'tiktok':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, text, author, create_time as created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, text, author, create_time as created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
                
        elif platform == 'youtube':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, title, description as text, author, published_at as created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, title, description as text, author, published_at as created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
        
        with db_engines[db_name].connect() as conn:
            print(f"Executing query: {query}")
            result = conn.execute(query, {'limit': limit})
            data = []
            for row in result:
                item = dict(row._mapping)
                # Convert datetime objects to ISO format strings
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                data.append(item)
            
            print(f"Found {len(data)} records for {platform}")
            return {'data': data}
            
    except Exception as e:
        print(f"Error in get_recent_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'data': []}

@app.get("/api/db/predictions")
async def get_predictions(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    Get topic predictions from ML models.
    
    Query Parameters:
    - start_date: (optional) Start date for the prediction period (YYYY-MM-DD)
    - end_date: (optional) End date for the prediction period (YYYY-MM-DD)
    
    Returns prediction data for future trends based on ML models.
    """
    try:
        # Use default dates if not provided
        if not start_date:
            start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
        # Convert to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate prediction data (mock data for now)
        predictions = generate_mock_predictions(start_dt, end_dt, num_topics=5)
        
        response = {
            'predictions': predictions,
            'time_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'prediction_trends': generate_mock_prediction_trends(predictions, start_dt, end_dt)
        }
        
        return response
    except Exception as e:
        print(f"Error in get_predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/pipelines")
async def get_pipelines(id: Optional[str] = None):
    """Get all available ML pipelines or a specific pipeline by ID."""
    try:
        # Generate mock pipeline data
        pipelines = [
            {
                "id": "topic-modeling-pipeline",
                "name": "Topic Modeling Pipeline",
                "description": "Extract topics from social media posts using TF-IDF and NMF",
                "status": "active",
                "last_run": (datetime.now() - timedelta(hours=6)).isoformat(),
                "success_rate": 92,
                "steps": ["data_extraction", "preprocessing", "topic_modeling", "evaluation"]
            },
            {
                "id": "sentiment-analysis-pipeline",
                "name": "Sentiment Analysis Pipeline",
                "description": "Analyze sentiment of social media posts using machine learning",
                "status": "active",
                "last_run": (datetime.now() - timedelta(hours=12)).isoformat(),
                "success_rate": 88,
                "steps": ["data_extraction", "preprocessing", "sentiment_classification", "evaluation"]
            },
            {
                "id": "trend-prediction-pipeline",
                "name": "Trend Prediction Pipeline",
                "description": "Predict future trends based on historical social media data",
                "status": "active",
                "last_run": (datetime.now() - timedelta(days=1)).isoformat(),
                "success_rate": 85,
                "steps": ["data_extraction", "preprocessing", "feature_engineering", "model_training", "forecasting"]
            }
        ]
        
        # Return specific pipeline if ID is provided
        if id:
            for pipeline in pipelines:
                if pipeline["id"] == id:
                    return pipeline
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Return all pipelines
        return pipelines
    except Exception as e:
        print(f"Error in get_pipelines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/pipelines/{pipeline_id}/executions")
async def get_pipeline_executions(pipeline_id: str):
    """Get execution history for a specific pipeline."""
    try:
        # Generate mock execution data
        executions = []
        # Create 5 mock executions with different statuses
        statuses = ["completed", "completed", "failed", "completed", "running"]
        
        for i in range(5):
            status = statuses[i]
            execution_time = datetime.now() - timedelta(days=i, hours=random.randint(0, 12))
            
            execution = {
                "id": f"exec-{pipeline_id}-{i}",
                "pipeline_id": pipeline_id,
                "status": status,
                "start_time": execution_time.isoformat(),
                "end_time": (execution_time + timedelta(minutes=random.randint(15, 45))).isoformat() if status != "running" else None,
                "logs": f"Execution logs for {pipeline_id} run {i}",
                "metrics": {
                    "accuracy": round(random.uniform(0.82, 0.94), 2) if status == "completed" else None,
                    "precision": round(random.uniform(0.80, 0.92), 2) if status == "completed" else None,
                    "recall": round(random.uniform(0.78, 0.90), 2) if status == "completed" else None,
                    "f1_score": round(random.uniform(0.80, 0.92), 2) if status == "completed" else None
                }
            }
            
            # Add error details for failed executions
            if status == "failed":
                execution["error"] = "Data preprocessing step failed due to missing values"
                
            executions.append(execution)
        
        return executions
    except Exception as e:
        print(f"Error in get_pipeline_executions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mlops/pipelines/{pipeline_id}/execute")
async def execute_pipeline(pipeline_id: str):
    """Trigger execution of a specific ML pipeline."""
    try:
        # Mock pipeline execution - in a real system this would trigger the actual pipeline
        execution_id = f"exec-{pipeline_id}-{int(datetime.now().timestamp())}"
        
        response = {
            "execution_id": execution_id,
            "pipeline_id": pipeline_id,
            "status": "started",
            "startTime": datetime.now().isoformat(),
            "message": f"Pipeline {pipeline_id} execution started successfully"
        }
        
        return response
    except Exception as e:
        print(f"Error in execute_pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/models")
async def get_models():
    """Get all available ML models."""
    try:
        # Generate mock model data
        models = [
            {
                "id": "topic-model",
                "name": "Topic Model",
                "type": "NMF",
                "description": "Non-negative Matrix Factorization for topic modeling",
                "latest_version": "v1.2.3",
                "created_at": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "id": "sentiment-model",
                "name": "Sentiment Analysis Model",
                "type": "RandomForest",
                "description": "Random Forest classifier for sentiment analysis",
                "latest_version": "v2.0.1",
                "created_at": (datetime.now() - timedelta(days=15)).isoformat()
            },
            {
                "id": "trend-prediction-model",
                "name": "Trend Prediction Model",
                "type": "ARIMA",
                "description": "Time series forecasting for trend prediction",
                "latest_version": "v0.9.5",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat()
            }
        ]
        
        return models
    except Exception as e:
        print(f"Error in get_models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/models/{model_name}/versions")
async def get_model_versions(model_name: str):
    """Get all versions of a specific model."""
    try:
        # Generate mock version data based on model name
        versions = []
        model_info = {
            "topic-model": {"base_version": "v1.0.0", "num_versions": 4},
            "sentiment-model": {"base_version": "v2.0.0", "num_versions": 2}, 
            "trend-prediction-model": {"base_version": "v0.9.0", "num_versions": 6}
        }
        
        if model_name not in model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        info = model_info[model_name]
        
        for i in range(info["num_versions"]):
            version_date = datetime.now() - timedelta(days=i*10)
            accuracy = 0.8 + (i * 0.02) if i < 3 else 0.8 + (3 * 0.02) - ((i-3) * 0.01)
            
            version = {
                "version": f"{info['base_version'][:-1]}{int(info['base_version'][-1]) + i}",
                "model_name": model_name,
                "created_at": version_date.isoformat(),
                "accuracy": round(accuracy, 2),
                "is_production": i == 0,  # Most recent version is in production
                "trained_on": f"{random.randint(5000, 15000)} samples",
                "parameters": {
                    "learning_rate": round(random.uniform(0.01, 0.1), 3),
                    "batch_size": random.choice([32, 64, 128]),
                    "epochs": random.randint(10, 50)
                }
            }
            versions.append(version)
        
        return versions
    except Exception as e:
        print(f"Error in get_model_versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/models/{model_name}/metrics")
async def get_model_metrics(model_name: str, version: Optional[str] = None):
    """Get performance metrics for a specific model version."""
    try:
        # Generate mock metrics data
        if model_name == "topic-model":
            metrics = {
                "coherence_score": round(random.uniform(0.4, 0.7), 2),
                "topic_diversity": round(random.uniform(0.6, 0.9), 2),
                "perplexity": round(random.uniform(35, 60), 1),
                "training_time": f"{random.randint(5, 15)} minutes",
                "topics_extracted": random.randint(5, 15),
                "avg_topic_size": random.randint(10, 30),
                "version": version or "latest",
                "evaluation_date": datetime.now().isoformat()
            }
        elif model_name == "sentiment-model":
            metrics = {
                "accuracy": round(random.uniform(0.82, 0.92), 2),
                "precision": round(random.uniform(0.80, 0.90), 2),
                "recall": round(random.uniform(0.78, 0.88), 2),
                "f1_score": round(random.uniform(0.80, 0.90), 2),
                "roc_auc": round(random.uniform(0.85, 0.95), 2),
                "confusion_matrix": {
                    "true_positive": random.randint(800, 1200),
                    "false_positive": random.randint(100, 200),
                    "true_negative": random.randint(800, 1200),
                    "false_negative": random.randint(100, 200)
                },
                "version": version or "latest",
                "evaluation_date": datetime.now().isoformat()
            }
        elif model_name == "trend-prediction-model":
            metrics = {
                "mse": round(random.uniform(10, 30), 2),
                "rmse": round(random.uniform(3, 5.5), 2),
                "mae": round(random.uniform(2.5, 4.5), 2),
                "r2_score": round(random.uniform(0.6, 0.8), 2),
                "forecast_horizon": f"{random.randint(3, 14)} days",
                "version": version or "latest",
                "evaluation_date": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return metrics
    except Exception as e:
        print(f"Error in get_model_metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mlops/models/{model_name}/drift")
async def get_model_drift(model_name: str, version: Optional[str] = None):
    """Get model drift analysis for a specific model."""
    try:
        # Generate mock drift data
        base_metrics = {
            "feature_drift": {
                "psi_scores": {
                    "feature1": round(random.uniform(0.01, 0.2), 3),
                    "feature2": round(random.uniform(0.01, 0.2), 3),
                    "feature3": round(random.uniform(0.01, 0.2), 3),
                    "feature4": round(random.uniform(0.01, 0.2), 3),
                    "feature5": round(random.uniform(0.01, 0.2), 3)
                },
                "drift_detected": False
            },
            "performance_drift": {
                "accuracy_change": round(random.uniform(-0.05, 0.02), 3),
                "precision_change": round(random.uniform(-0.05, 0.02), 3),
                "recall_change": round(random.uniform(-0.05, 0.02), 3),
                "significant_drift": False
            },
            "data_quality": {
                "missing_values": f"{round(random.uniform(0.1, 3), 1)}%",
                "outliers": f"{round(random.uniform(0.5, 5), 1)}%"
            },
            "version": version or "latest",
            "analysis_date": datetime.now().isoformat()
        }
        
        # Make drift detected true in some cases
        if random.random() > 0.7:
            base_metrics["feature_drift"]["drift_detected"] = True
            # Make one feature have significant drift
            key = random.choice(list(base_metrics["feature_drift"]["psi_scores"].keys()))
            base_metrics["feature_drift"]["psi_scores"][key] = round(random.uniform(0.2, 0.5), 3)
        
        if random.random() > 0.7:
            base_metrics["performance_drift"]["significant_drift"] = True
            base_metrics["performance_drift"]["accuracy_change"] = round(random.uniform(-0.15, -0.08), 3)
        
        return base_metrics
    except Exception as e:
        print(f"Error in get_model_drift: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_mock_predictions(start_date, end_date, num_topics=5):
    """Generate mock prediction data for topics."""
    topics = [
        {"id": 1, "name": "Artificial Intelligence", "keywords": ["AI", "machine learning", "neural networks", "deep learning", "GPT"]},
        {"id": 2, "name": "Climate Change", "keywords": ["environment", "global warming", "renewable energy", "sustainability", "carbon"]},
        {"id": 3, "name": "Digital Privacy", "keywords": ["data protection", "encryption", "surveillance", "security", "GDPR"]},
        {"id": 4, "name": "Quantum Computing", "keywords": ["qubits", "quantum supremacy", "superposition", "entanglement", "quantum algorithms"]},
        {"id": 5, "name": "Space Exploration", "keywords": ["Mars", "NASA", "SpaceX", "astronomy", "satellites"]},
        {"id": 6, "name": "Cryptocurrencies", "keywords": ["Bitcoin", "blockchain", "Ethereum", "NFT", "DeFi"]},
        {"id": 7, "name": "Remote Work", "keywords": ["WFH", "hybrid work", "virtual collaboration", "digital nomad", "productivity"]},
        {"id": 8, "name": "Mental Health", "keywords": ["wellness", "therapy", "mindfulness", "psychology", "self-care"]}
    ]
    
    # Randomly select topics for predictions
    selected_topics = random.sample(topics, min(num_topics, len(topics)))
    
    # Generate date range for forecast data (7 days from start_date)
    forecast_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    predictions = []
    for topic in selected_topics:
        # Generate random confidence between 60% and 95%
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        # Generate random sentiment score between -0.8 and 0.8
        sentiment_score = round(random.uniform(-0.8, 0.8), 2)
        
        # Generate forecast data (daily post counts)
        max_value = random.randint(80, 300)
        forecast_data = {}
        for date in forecast_dates:
            # Generate a slightly upward trend with some randomness
            day_index = forecast_dates.index(date)
            trend_factor = 1 + (day_index * 0.1)  # Increases by 10% each day
            randomness = random.uniform(0.8, 1.2)  # +/- 20% random variation
            value = max_value * trend_factor * randomness
            forecast_data[date] = round(value)
        
        predictions.append({
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "confidence": confidence,
            "sentiment_score": sentiment_score,
            "keywords": topic["keywords"],
            "forecast_data": forecast_data,
            "forecast_max": max(forecast_data.values())
        })
    
    # Sort predictions by confidence (highest first)
    predictions.sort(key=lambda x: x["confidence"], reverse=True)
    
    return predictions

def generate_mock_prediction_trends(predictions, start_date, end_date):
    """Generate mock trend data for the predictions chart."""
    # Create a date range from start_date to end_date
    delta = (end_date - start_date).days + 1
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta)]
    
    trends = {}
    for prediction in predictions:
        topic_id = prediction["topic_id"]
        trends[topic_id] = {}
        
        # Base value - higher for topics with higher confidence
        base_value = random.randint(50, 100) * prediction["confidence"]
        
        # Generate trend values for each date
        for i, date in enumerate(dates):
            # Create a slightly upward trend with random variations
            trend_factor = 1 + (i * 0.05)  # Increases by 5% each day
            randomness = random.uniform(0.9, 1.1)  # +/- 10% random variation
            value = base_value * trend_factor * randomness
            trends[topic_id][date] = round(value)
    
    return trends

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host="0.0.0.0", port=port) 