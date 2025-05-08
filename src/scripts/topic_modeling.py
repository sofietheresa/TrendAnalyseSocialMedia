from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisiere Sentence-Embedding-Modell
try:
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    topic_model = BERTopic(embedding_model=embedding_model, verbose=False)
except Exception as e:
    logger.error(f"Fehler beim Laden von BERTopic oder dem SentenceTransformer-Modell: {e}")
    embedding_model = None
    topic_model = None

def generate_topics(texts):
    """
    Führt BERTopic durch und gibt Topic-Zuweisungen pro Text zurück.
    """
    if not topic_model or not isinstance(texts, list) or not texts:
        return ["unknown"] * len(texts)

    try:
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        topics, _ = topic_model.fit_transform(texts, embeddings)
        return topics
    except Exception as e:
        logger.warning(f"Topic Modeling fehlgeschlagen: {e}")
        return ["unknown"] * len(texts)
