import os
import sys
import logging
from sqlalchemy import create_engine, text
import urllib.parse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        url = os.getenv("DATABASE_URL")
        if not url:
            logger.error("DATABASE_URL is not set")
            return False

        parsed_url = urllib.parse.urlparse(url)
        safe_url = f"postgresql://{parsed_url.username}:***@{parsed_url.hostname}:{parsed_url.port}/{parsed_url.path}"
        logger.info(f"Testing connection to: {safe_url}")

        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row[0] == 1:
                logger.info("Database connection successful!")
                return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 