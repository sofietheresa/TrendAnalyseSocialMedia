from transformers import pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisiere Sentiment-Pipeline mit Roberta-Modell optimiert für Social Media
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
except Exception as e:
    logger.error(f"Fehler beim Laden des Sentiment-Modells: {e}")
    sentiment_pipeline = None

def analyze_sentiment(text: str):
    """
    Führt Sentimentanalyse durch und gibt (Label, Score) zurück.
    """
    if not sentiment_pipeline or not isinstance(text, str) or not text.strip():
        return "neutral", 0.0

    try:
        result = sentiment_pipeline(text[:512])[0]  # Input max 512 Tokens
        return result["label"].lower(), result["score"]
    except Exception as e:
        logger.warning(f"Sentimentanalyse fehlgeschlagen: {e}")
        return "neutral", 0.0
