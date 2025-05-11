from zenml.steps import step
import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, Any, List, Tuple
import logging
from sklearn.feature_extraction.text import CountVectorizer
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def analyze_platform_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the distribution of posts across platforms."""
    platform_counts = df['platform'].value_counts().to_dict()
    platform_percentages = (df['platform'].value_counts(normalize=True) * 100).to_dict()
    
    return {
        'counts': platform_counts,
        'percentages': platform_percentages
    }

def analyze_engagement_by_platform(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze engagement metrics by platform."""
    engagement_stats = df.groupby('platform').agg({
        'engagement_score': ['mean', 'median', 'std', 'min', 'max'],
        'sentiment_score': ['mean', 'median', 'std']
    }).round(2)
    
    return engagement_stats.to_dict()

def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze temporal patterns in the data."""
    # Hourly distribution
    hourly_dist = df.groupby('hour').size().to_dict()
    
    # Day of week distribution
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Fill NaN values with 0 and convert to integers
    df['day_of_week'] = df['day_of_week'].fillna(0).astype(int) % 7
    dow_dist = df.groupby('day_of_week').size()
    dow_dist.index = [day_names[i] for i in dow_dist.index]
    dow_dist = dow_dist.to_dict()
    
    # Monthly distribution
    monthly_dist = df.groupby('month').size().to_dict()
    
    return {
        'hourly': hourly_dist,
        'day_of_week': dow_dist,
        'monthly': monthly_dist
    }

def analyze_sentiment_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze sentiment distribution."""
    sentiment_stats = {
        'overall': {
            'mean': df['sentiment_score'].mean(),
            'median': df['sentiment_score'].median(),
            'std': df['sentiment_score'].std()
        },
        'by_platform': df.groupby('platform')['sentiment_score'].agg(['mean', 'median', 'std']).to_dict()
    }
    
    # Sentiment categories
    df['sentiment_category'] = pd.cut(
        df['sentiment_score'],
        bins=[-1, -0.3, 0.3, 1],
        labels=['Negative', 'Neutral', 'Positive']
    )
    sentiment_categories = df['sentiment_category'].value_counts().to_dict()
    
    sentiment_stats['categories'] = sentiment_categories
    return sentiment_stats

def analyze_top_words(df: pd.DataFrame, n_words: int = 20) -> Dict[str, List[Tuple[str, int]]]:
    """Analyze most common words in the text."""
    # Combine all lemmatized text
    all_text = ' '.join(df['lemmatized_text'].dropna())
    
    # Count words
    word_counts = Counter(all_text.split())
    
    # Get top N words
    top_words = word_counts.most_common(n_words)
    
    return {'top_words': top_words}

def analyze_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """Analyze correlations between numerical features."""
    numerical_cols = ['engagement_score', 'sentiment_score', 'hour', 'day_of_week', 'month']
    correlation_matrix = df[numerical_cols].corr()
    
    # Get correlations with engagement score
    engagement_correlations = correlation_matrix['engagement_score'].drop('engagement_score').to_dict()
    
    return engagement_correlations

def stringify_keys(obj):
    """Recursively convert all dict keys to strings (for JSON serialization)."""
    if isinstance(obj, dict):
        return {str(k): stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    else:
        return obj

@step
def explore_data(data: pd.DataFrame) -> Dict[str, Any]:
    """Perform comprehensive data exploration."""
    logger.info("Starting data exploration...")
    
    # Prüfe, ob die erforderlichen Spalten vorhanden sind
    required_columns = ['platform', 'engagement_score', 'sentiment_score', 'hour', 'day_of_week', 'month', 'lemmatized_text']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        logger.error(f"Fehlende Spalten: {missing_columns}")
        raise ValueError(f"Required columns missing: {missing_columns}")
    
    results = {}
    
    # Platform distribution
    logger.info("Analyzing platform distribution...")
    results['platform_distribution'] = analyze_platform_distribution(data)
    
    # Engagement analysis
    logger.info("Analyzing engagement metrics...")
    results['engagement_analysis'] = analyze_engagement_by_platform(data)
    
    # Temporal patterns
    logger.info("Analyzing temporal patterns...")
    results['temporal_patterns'] = analyze_temporal_patterns(data)
    
    # Sentiment analysis
    logger.info("Analyzing sentiment distribution...")
    results['sentiment_analysis'] = analyze_sentiment_distribution(data)
    
    # Word frequency analysis
    logger.info("Analyzing word frequencies...")
    results['word_analysis'] = analyze_top_words(data)
    
    # Correlation analysis
    logger.info("Analyzing correlations...")
    results['correlations'] = analyze_correlations(data)
    
    # Save results to file
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert all keys to strings before saving and returning
    results_str_keys = stringify_keys(results)
    with open(output_dir / "exploration_results.json", "w") as f:
        json.dump(results_str_keys, f, indent=2)
    
    logger.info("Data exploration complete. Results saved to data/processed/exploration_results.json")
    
    return results_str_keys 