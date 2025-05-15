from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "database.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_engine():
    """Get SQLAlchemy engine for PostgreSQL connection"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        logger.error(f"Error creating database connection: {e}")
        raise 