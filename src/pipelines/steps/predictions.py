from zenml.steps import step
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import logging
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_squared_error, 
    r2_score, 
    mean_absolute_error,
    explained_variance_score,
    median_absolute_error
)
import joblib
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare features for model training."""
    # Drop rows with missing lemmatized_text
    initial_shape = df.shape
    df = df.dropna(subset=['lemmatized_text'])
    dropped = initial_shape[0] - df.shape[0]
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing lemmatized_text.")
    # Text features
    vectorizer = TfidfVectorizer(max_features=1000)
    text_features = vectorizer.fit_transform(df['lemmatized_text'])
    
    # Numerical features
    numerical_features = df[['hour', 'day_of_week', 'month', 'sentiment_score']].values
    
    # Combine features
    X = np.hstack([text_features.toarray(), numerical_features])
    y = df['normalized_engagement'].values
    
    return X, y

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate comprehensive model evaluation metrics."""
    return {
        'mse': mean_squared_error(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'median_ae': median_absolute_error(y_true, y_pred),
        'r2': r2_score(y_true, y_pred),
        'explained_variance': explained_variance_score(y_true, y_pred)
    }

def perform_cross_validation(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict[str, float]:
    """Perform k-fold cross-validation."""
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    
    # Initialize KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # Store scores
    cv_scores = {
        'mse': [],
        'rmse': [],
        'mae': [],
        'r2': []
    }
    
    # Perform cross-validation
    for train_idx, val_idx in kf.split(X):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Train and predict
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        # Calculate metrics
        cv_scores['mse'].append(mean_squared_error(y_val, y_pred))
        cv_scores['rmse'].append(np.sqrt(mean_squared_error(y_val, y_pred)))
        cv_scores['mae'].append(mean_absolute_error(y_val, y_pred))
        cv_scores['r2'].append(r2_score(y_val, y_pred))
    
    # Calculate mean and std of metrics
    cv_results = {
        metric: {
            'mean': np.mean(scores),
            'std': np.std(scores)
        }
        for metric, scores in cv_scores.items()
    }
    
    return cv_results

def plot_prediction_analysis(y_true: np.ndarray, y_pred: np.ndarray, output_dir: Path):
    """Create and save prediction analysis plots."""
    # Create plots directory
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Actual vs Predicted scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(y_true, y_pred, alpha=0.5)
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
    plt.xlabel('Actual Engagement')
    plt.ylabel('Predicted Engagement')
    plt.title('Actual vs Predicted Engagement')
    plt.savefig(plots_dir / "actual_vs_predicted.png")
    plt.close()
    
    # Residuals plot
    residuals = y_true - y_pred
    plt.figure(figsize=(10, 6))
    plt.scatter(y_pred, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Predicted Engagement')
    plt.ylabel('Residuals')
    plt.title('Residuals Plot')
    plt.savefig(plots_dir / "residuals.png")
    plt.close()
    
    # Residuals distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(residuals, kde=True)
    plt.xlabel('Residuals')
    plt.ylabel('Count')
    plt.title('Residuals Distribution')
    plt.savefig(plots_dir / "residuals_distribution.png")
    plt.close()

def train_model(X: np.ndarray, y: np.ndarray) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train the prediction model with comprehensive evaluation."""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = calculate_metrics(y_test, y_pred)
    
    # Perform cross-validation
    cv_results = perform_cross_validation(X, y)
    
    # Combine all metrics
    evaluation_results = {
        'test_metrics': metrics,
        'cross_validation': cv_results
    }
    
    return model, evaluation_results

def analyze_feature_importance(model: RandomForestRegressor, feature_names: list) -> Dict[str, float]:
    """Analyze feature importance."""
    importance = model.feature_importances_
    feature_importance = dict(zip(feature_names, importance))
    return dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

def predict_engagement(model: RandomForestRegressor, df: pd.DataFrame) -> pd.DataFrame:
    """Make predictions for engagement."""
    # Drop rows with missing lemmatized_text
    initial_shape = df.shape
    df = df.dropna(subset=['lemmatized_text'])
    dropped = initial_shape[0] - df.shape[0]
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing lemmatized_text in prediction.")
    # Prepare features for prediction
    vectorizer = TfidfVectorizer(max_features=1000)
    text_features = vectorizer.fit_transform(df['lemmatized_text'])
    numerical_features = df[['hour', 'day_of_week', 'month', 'sentiment_score']].values
    X = np.hstack([text_features.toarray(), numerical_features])
    # Make predictions
    predictions = model.predict(X)
    # Add predictions to dataframe
    df['predicted_engagement'] = predictions
    return df

@step
def make_predictions(data: pd.DataFrame, exploration_results: Dict[str, Any]) -> Dict[str, Any]:
    """Make predictions and analyze results."""
    logger.info("Starting prediction process...")
    
    # Prepare features
    logger.info("Preparing features...")
    X, y = prepare_features(data)
    
    # Train model and get evaluation results
    logger.info("Training model and evaluating performance...")
    model, evaluation_results = train_model(X, y)
    
    # Analyze feature importance
    logger.info("Analyzing feature importance...")
    feature_names = (
        [f'word_{i}' for i in range(1000)] +  # TF-IDF features
        ['hour', 'day_of_week', 'month', 'sentiment_score']  # Numerical features
    )
    feature_importance = analyze_feature_importance(model, feature_names)
    
    # Make predictions
    logger.info("Making predictions...")
    predictions_df = predict_engagement(model, data)
    
    # Create output directory
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate prediction analysis plots
    logger.info("Generating prediction analysis plots...")
    plot_prediction_analysis(y, model.predict(X), output_dir)
    
    # Prepare results
    results = {
        'model_evaluation': evaluation_results,
        'feature_importance': feature_importance,
        'predictions_summary': {
            'mean_predicted_engagement': predictions_df['predicted_engagement'].mean(),
            'std_predicted_engagement': predictions_df['predicted_engagement'].std(),
            'min_predicted_engagement': predictions_df['predicted_engagement'].min(),
            'max_predicted_engagement': predictions_df['predicted_engagement'].max()
        }
    }
    
    # Save model and results
    joblib.dump(model, output_dir / "engagement_model.joblib")
    predictions_df.to_csv(output_dir / "predictions.csv", index=False)
    
    with open(output_dir / "prediction_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Prediction process complete. Results saved to data/processed/")
    
    return results 