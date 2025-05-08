import hashlib
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def compute_row_hash(row: pd.Series) -> str:
    """
    Berechnet einen Hash für eine gegebene Zeile.
    """
    row_string = str(row.values)
    return hashlib.md5(row_string.encode('utf-8')).hexdigest()

def skip_already_processed(new_df: pd.DataFrame, processed_path: Path) -> pd.DataFrame:
    """
    Entfernt Zeilen aus dem neuen DataFrame, die bereits in der verarbeiteten Datei enthalten sind.
    """
    if not processed_path.exists():
        return new_df

    try:
        processed_df = pd.read_csv(processed_path)
    except Exception as e:
        logger.warning(f"Konnte {processed_path} nicht laden: {e}")
        return new_df

    if 'hash' not in processed_df.columns:
        logger.warning("Keine 'hash'-Spalte in bereits verarbeiteter Datei – keine Duplikaterkennung möglich.")
        return new_df

    existing_hashes = set(processed_df['hash'].dropna().astype(str))
    filtered_df = new_df[~new_df['hash'].isin(existing_hashes)]

    logger.info(f"{len(new_df) - len(filtered_df)} bereits verarbeitete Zeilen übersprungen.")
    return filtered_df
