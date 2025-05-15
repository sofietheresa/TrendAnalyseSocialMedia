from zenml.steps import step
import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, Any, List, Tuple
import logging
import json
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

# Optional sklearn dependency
try:
    from sklearn.feature_extraction.text import CountVectorizer
    SKLEARN_AVAILABLE = True
    logger.info("scikit-learn successfully imported")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, some functionality will be limited")

def analyze_platform_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the distribution of posts across platforms."""
    try:
        if 'platform' not in df.columns or df.empty:
            logger.warning("No platform column found or dataframe is empty")
            return {
                'counts': {},
                'percentages': {}
            }
            
        platform_counts = df['platform'].value_counts().to_dict()
        platform_percentages = (df['platform'].value_counts(normalize=True) * 100).to_dict()
        
        return {
            'counts': platform_counts,
            'percentages': platform_percentages
        }
    except Exception as e:
        logger.error(f"Error in platform distribution analysis: {str(e)}")
        return {
            'counts': {},
            'percentages': {},
            'error': str(e)
        }

def analyze_engagement_by_platform(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze engagement metrics by platform."""
    try:
        required_cols = ['platform', 'engagement_score', 'sentiment_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols or df.empty:
            logger.warning(f"Missing columns for engagement analysis: {missing_cols}")
            return {}
            
        # Create a safe aggregation by handling missing columns
        agg_dict = {}
        
        if 'engagement_score' in df.columns:
            agg_dict['engagement_score'] = ['mean', 'median', 'std', 'min', 'max']
        
        if 'sentiment_score' in df.columns:
            agg_dict['sentiment_score'] = ['mean', 'median', 'std']
            
        if not agg_dict:
            return {}
            
        engagement_stats = df.groupby('platform').agg(agg_dict).round(2)
        
        return engagement_stats.to_dict()
    except Exception as e:
        logger.error(f"Error in engagement analysis: {str(e)}")
        return {'error': str(e)}

def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze temporal patterns in the data."""
    try:
        results = {}
        
        # Check if required columns exist
        time_cols = ['hour', 'day_of_week', 'month']
        missing_cols = [col for col in time_cols if col not in df.columns]
        
        if missing_cols or df.empty:
            logger.warning(f"Missing columns for temporal analysis: {missing_cols}")
            return {}
        
        # Hourly distribution
        if 'hour' in df.columns:
            hourly_dist = df.groupby('hour').size().to_dict()
            results['hourly'] = hourly_dist
        
        # Day of week distribution
        if 'day_of_week' in df.columns:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            # Fill NaN values with 0 and convert to integers
            df['day_of_week'] = df['day_of_week'].fillna(0).astype(int) % 7
            dow_dist = df.groupby('day_of_week').size()
            dow_dist.index = [day_names[i] for i in dow_dist.index]
            results['day_of_week'] = dow_dist.to_dict()
        
        # Monthly distribution
        if 'month' in df.columns:
            monthly_dist = df.groupby('month').size().to_dict()
            results['monthly'] = monthly_dist
        
        return results
    except Exception as e:
        logger.error(f"Error in temporal pattern analysis: {str(e)}")
        return {'error': str(e)}

def analyze_sentiment_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze sentiment distribution."""
    try:
        required_cols = ['sentiment_score', 'platform']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols or df.empty:
            logger.warning(f"Missing columns for sentiment analysis: {missing_cols}")
            return {}
            
        sentiment_stats = {
            'overall': {
                'mean': df['sentiment_score'].mean(),
                'median': df['sentiment_score'].median(),
                'std': df['sentiment_score'].std()
            },
            'by_platform': df.groupby('platform')['sentiment_score'].agg(['mean', 'median', 'std']).to_dict()
        }
        
        # Sentiment categories
        try:
            df['sentiment_category'] = pd.cut(
                df['sentiment_score'],
                bins=[-1, -0.3, 0.3, 1],
                labels=['Negative', 'Neutral', 'Positive']
            )
            sentiment_categories = df['sentiment_category'].value_counts().to_dict()
            sentiment_stats['categories'] = sentiment_categories
        except Exception as e:
            logger.warning(f"Error creating sentiment categories: {str(e)}")
            sentiment_stats['categories'] = {}
        
        return sentiment_stats
    except Exception as e:
        logger.error(f"Error in sentiment distribution analysis: {str(e)}")
        return {'error': str(e)}

def analyze_top_words(df: pd.DataFrame, n_words: int = 20) -> Dict[str, List[Tuple[str, int]]]:
    """Analyze most common words in the text."""
    try:
        if 'lemmatized_text' not in df.columns or df.empty:
            logger.warning("No lemmatized_text column found or dataframe is empty")
            return {'top_words': []}
            
        # Combine all lemmatized text
        all_text = ' '.join(df['lemmatized_text'].dropna())
        
        if not all_text.strip():
            logger.warning("No text content to analyze")
            return {'top_words': []}
        
        # Count words
        word_counts = Counter(all_text.split())
        
        # Get top N words
        top_words = word_counts.most_common(n_words)
        
        return {'top_words': top_words}
    except Exception as e:
        logger.error(f"Error in word analysis: {str(e)}")
        return {'top_words': [], 'error': str(e)}

def analyze_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """Analyze correlations between numerical features."""
    try:
        numerical_cols = ['engagement_score', 'sentiment_score', 'hour', 'day_of_week', 'month']
        available_cols = [col for col in numerical_cols if col in df.columns]
        
        if not available_cols or df.empty:
            logger.warning(f"Missing columns for correlation analysis. Available: {available_cols}")
            return {}
            
        # If engagement_score is not available, can't compute correlations with it
        if 'engagement_score' not in available_cols:
            logger.warning("engagement_score not available for correlation analysis")
            return {}
            
        correlation_matrix = df[available_cols].corr()
        
        # Get correlations with engagement score
        engagement_correlations = correlation_matrix['engagement_score'].drop('engagement_score').to_dict()
        
        return engagement_correlations
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}")
        return {'error': str(e)}

def stringify_keys(obj):
    """Recursively convert all dict keys to strings (for JSON serialization)."""
    if isinstance(obj, dict):
        return {str(k): stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_keys(i) for i in obj]
    elif isinstance(obj, pd.Series):
        return stringify_keys(obj.to_dict())
    elif isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
        return float(obj) if isinstance(obj, (np.float64, np.float32)) else int(obj)
    else:
        return obj

@step
def explore_data(data: pd.DataFrame) -> Dict[str, Any]:
    """Perform comprehensive data exploration."""
    logger.info("Starting data exploration...")
    
    try:
        # Check if DataFrame is empty
        if data is None or len(data) == 0:
            logger.warning("Input data is empty or None")
            return {
                'warning': 'No data available for analysis',
                'platform_distribution': {'counts': {}, 'percentages': {}},
                'empty': True
            }
        
        # Required columns for basic functionality
        required_columns = ['platform', 'engagement_score', 'sentiment_score', 'lemmatized_text']
        available_columns = [col for col in required_columns if col in data.columns]
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            logger.warning(f"Some required columns are missing: {missing_columns}")
        
        results = {
            'data_shape': {
                'rows': len(data),
                'columns': len(data.columns)
            },
            'available_columns': list(data.columns),
            'missing_columns': missing_columns
        }
        
        # Platform distribution - can always try to run this
        logger.info("Analyzing platform distribution...")
        results['platform_distribution'] = analyze_platform_distribution(data)
        
        # Engagement analysis - needs engagement_score column
        if 'engagement_score' in data.columns:
            logger.info("Analyzing engagement metrics...")
            results['engagement_analysis'] = analyze_engagement_by_platform(data)
        else:
            results['engagement_analysis'] = {'error': 'engagement_score column missing'}
        
        # Temporal patterns - needs time-based columns
        time_cols = ['hour', 'day_of_week', 'month']
        if any(col in data.columns for col in time_cols):
            logger.info("Analyzing temporal patterns...")
            results['temporal_patterns'] = analyze_temporal_patterns(data)
        else:
            results['temporal_patterns'] = {'error': 'time-based columns missing'}
        
        # Sentiment analysis - needs sentiment_score column
        if 'sentiment_score' in data.columns:
            logger.info("Analyzing sentiment distribution...")
            results['sentiment_analysis'] = analyze_sentiment_distribution(data)
        else:
            results['sentiment_analysis'] = {'error': 'sentiment_score column missing'}
        
        # Word frequency analysis - needs lemmatized_text column
        if 'lemmatized_text' in data.columns:
            logger.info("Analyzing word frequencies...")
            results['word_analysis'] = analyze_top_words(data)
        else:
            results['word_analysis'] = {'error': 'lemmatized_text column missing'}
        
        # Correlation analysis - needs numerical columns
        numerical_cols = ['engagement_score', 'sentiment_score', 'hour', 'day_of_week', 'month']
        if any(col in data.columns for col in numerical_cols):
            logger.info("Analyzing correlations...")
            results['correlations'] = analyze_correlations(data)
        else:
            results['correlations'] = {'error': 'numerical columns missing'}
        
        # Save results to file
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert all keys to strings before saving and returning
        results_str_keys = stringify_keys(results)
        
        # Ensure the JSON is serializable
        try:
            with open(output_dir / "exploration_results.json", "w") as f:
                json.dump(results_str_keys, f, indent=2)
            logger.info("Results saved to data/processed/exploration_results.json")
        except Exception as e:
            logger.error(f"Error saving exploration results: {str(e)}")
        
        logger.info("Data exploration complete.")
        return results_str_keys
        
    except Exception as e:
        logger.error(f"Error in data exploration: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return minimal results
        minimal_results = {
            'error': str(e),
            'error_trace': traceback.format_exc(),
            'platform_distribution': {'counts': {}, 'percentages': {}},
            'empty': True
        }
        
        return stringify_keys(minimal_results) 