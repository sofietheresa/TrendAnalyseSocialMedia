from zenml.steps import step
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Union, List
import logging
import joblib
from pathlib import Path
import json
import traceback
import os

logger = logging.getLogger(__name__)

# Optional dependencies
try:
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
    SKLEARN_AVAILABLE = True
    logger.info("scikit-learn successfully imported")
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, prediction functionality will be disabled")

# Optional visualization dependencies
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
    logger.info("Matplotlib and Seaborn successfully imported")
except ImportError:
    PLOTTING_AVAILABLE = False
    logger.warning("Matplotlib or Seaborn not available, plotting will be disabled")

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare features for model training."""
    if not SKLEARN_AVAILABLE:
        logger.error("scikit-learn is not available, cannot prepare features")
        raise ImportError("scikit-learn is required for feature preparation")
        
    # Check required columns
    required_cols = ['lemmatized_text', 'normalized_engagement']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns for feature preparation: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Drop rows with missing lemmatized_text
    initial_shape = df.shape
    df = df.dropna(subset=['lemmatized_text'])
    dropped = initial_shape[0] - df.shape[0]
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing lemmatized_text.")
        
    if len(df) == 0:
        logger.error("No data left after dropping rows with missing text")
        raise ValueError("No valid data for feature preparation")
    
    try:
        # Text features
        vectorizer = TfidfVectorizer(max_features=1000)
        text_features = vectorizer.fit_transform(df['lemmatized_text'])
        
        # Numerical features - use only available columns
        numerical_cols = []
        for col in ['hour', 'day_of_week', 'month', 'sentiment_score']:
            if col in df.columns:
                numerical_cols.append(col)
                
        if not numerical_cols:
            logger.warning("No numerical columns available, using only text features")
            numerical_features = np.zeros((len(df), 1))
        else:
            numerical_features = df[numerical_cols].fillna(0).values
        
        # Combine features
        X = np.hstack([text_features.toarray(), numerical_features])
        y = df['normalized_engagement'].values
        
        return X, y
    except Exception as e:
        logger.error(f"Error preparing features: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate comprehensive model evaluation metrics."""
    if not SKLEARN_AVAILABLE:
        return {"error": "scikit-learn not available"}
        
    try:
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'median_ae': median_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'explained_variance': explained_variance_score(y_true, y_pred)
        }
        
        # Ensure metrics are valid numbers
        for key, value in metrics.items():
            if np.isnan(value) or np.isinf(value):
                logger.warning(f"Invalid {key} value: {value}, replacing with 0")
                metrics[key] = 0
                
        return metrics
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        return {
            'mse': 0,
            'rmse': 0,
            'mae': 0,
            'median_ae': 0,
            'r2': 0,
            'explained_variance': 0,
            'error': str(e)
        }

def perform_cross_validation(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict[str, Any]:
    """Perform k-fold cross-validation."""
    if not SKLEARN_AVAILABLE:
        return {"error": "scikit-learn not available"}
        
    try:
        # Check if we have enough data for cross-validation
        if len(y) < n_splits * 2:
            logger.warning(f"Not enough data for {n_splits}-fold cross-validation, reducing folds")
            n_splits = max(2, len(y) // 2)
            
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
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores))
            }
            for metric, scores in cv_scores.items()
        }
        
        return cv_results
    except Exception as e:
        logger.error(f"Error in cross validation: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def plot_prediction_analysis(y_true: np.ndarray, y_pred: np.ndarray, output_dir: Path):
    """Create and save prediction analysis plots."""
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotting libraries not available, skipping visualization")
        return
        
    try:
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
        
        logger.info(f"Saved prediction analysis plots to {plots_dir}")
    except Exception as e:
        logger.error(f"Error creating plots: {str(e)}")
        logger.error(traceback.format_exc())

def train_model(X: np.ndarray, y: np.ndarray) -> Tuple[RandomForestRegressor, Dict[str, Any]]:
    """Train the prediction model with comprehensive evaluation."""
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for model training")
        
    try:
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
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def analyze_feature_importance(model: RandomForestRegressor, feature_names: List[str]) -> Dict[str, float]:
    """Analyze feature importance."""
    try:
        importance = model.feature_importances_
        if len(importance) != len(feature_names):
            logger.warning(f"Feature importance length mismatch: {len(importance)} vs {len(feature_names)}")
            return {}
            
        feature_importance = dict(zip(feature_names, importance))
        return dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    except Exception as e:
        logger.error(f"Error analyzing feature importance: {str(e)}")
        return {}

def predict_engagement(model: RandomForestRegressor, df: pd.DataFrame) -> pd.DataFrame:
    """Make predictions for engagement."""
    if not SKLEARN_AVAILABLE:
        logger.error("scikit-learn is not available, cannot make predictions")
        df['predicted_engagement'] = 0
        return df
        
    try:
        # Check if required columns exist
        if 'lemmatized_text' not in df.columns:
            logger.error("lemmatized_text column missing, cannot make predictions")
            df['predicted_engagement'] = 0
            return df
            
        # Drop rows with missing lemmatized_text
        initial_shape = df.shape
        df = df.dropna(subset=['lemmatized_text'])
        dropped = initial_shape[0] - df.shape[0]
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with missing lemmatized_text in prediction.")
            
        if len(df) == 0:
            logger.error("No data left after dropping rows with missing text")
            df['predicted_engagement'] = 0
            return df
        
        # Prepare features for prediction
        vectorizer = TfidfVectorizer(max_features=1000)
        text_features = vectorizer.fit_transform(df['lemmatized_text'])
        
        # Check which numerical columns are available
        available_num_cols = []
        for col in ['hour', 'day_of_week', 'month', 'sentiment_score']:
            if col in df.columns:
                available_num_cols.append(col)
                
        if available_num_cols:
            numerical_features = df[available_num_cols].fillna(0).values
        else:
            logger.warning("No numerical features available for prediction")
            numerical_features = np.zeros((len(df), 1))
        
        X = np.hstack([text_features.toarray(), numerical_features])
        
        # Make predictions
        predictions = model.predict(X)
        
        # Add predictions to dataframe
        df['predicted_engagement'] = predictions
        
        return df
    except Exception as e:
        logger.error(f"Error making predictions: {str(e)}")
        logger.error(traceback.format_exc())
        # Return original dataframe with zero predictions
        df['predicted_engagement'] = 0
        return df

@step
def make_predictions(data: pd.DataFrame, exploration_results: Dict[str, Any]) -> Dict[str, Any]:
    """Make predictions and analyze results."""
    logger.info("Starting prediction process...")
    
    # Create output directory
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check if scikit-learn is available
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn is required for predictions but not available")
            return {
                "error": "scikit-learn not available",
                "predictions_summary": {
                    "status": "error",
                    "message": "Required dependencies not available"
                }
            }
            
        # Check if data is empty
        if data is None or len(data) == 0:
            logger.error("Input data is empty or None")
            return {
                "error": "No data available for predictions",
                "predictions_summary": {
                    "status": "error",
                    "message": "No data available"
                }
            }
            
        # Check required columns
        required_cols = ['lemmatized_text', 'normalized_engagement']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            logger.error(f"Missing required columns for predictions: {missing_cols}")
            return {
                "error": f"Missing required columns: {missing_cols}",
                "predictions_summary": {
                    "status": "error",
                    "message": f"Missing required columns: {missing_cols}"
                }
            }
            
        # Prepare features
        logger.info("Preparing features...")
        try:
            X, y = prepare_features(data)
            logger.info(f"Features prepared: {X.shape[0]} samples, {X.shape[1]} features")
        except Exception as e:
            logger.error(f"Feature preparation failed: {str(e)}")
            return {
                "error": f"Feature preparation failed: {str(e)}",
                "predictions_summary": {
                    "status": "error",
                    "message": "Feature preparation failed"
                }
            }
        
        # Train model and get evaluation results
        logger.info("Training model and evaluating performance...")
        try:
            model, evaluation_results = train_model(X, y)
            logger.info("Model training successful")
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return {
                "error": f"Model training failed: {str(e)}",
                "predictions_summary": {
                    "status": "error",
                    "message": "Model training failed"
                }
            }
        
        # Analyze feature importance
        logger.info("Analyzing feature importance...")
        feature_names = (
            [f'word_{i}' for i in range(1000)] +  # TF-IDF features
            ['hour', 'day_of_week', 'month', 'sentiment_score']  # Numerical features (add only those available)
        )
        feature_importance = analyze_feature_importance(model, feature_names)
        
        # Make predictions
        logger.info("Making predictions...")
        try:
            predictions_df = predict_engagement(model, data)
            logger.info(f"Predictions generated for {len(predictions_df)} samples")
        except Exception as e:
            logger.error(f"Prediction generation failed: {str(e)}")
            return {
                "error": f"Prediction generation failed: {str(e)}",
                "model_evaluation": evaluation_results,
                "feature_importance": feature_importance,
                "predictions_summary": {
                    "status": "error",
                    "message": "Prediction generation failed"
                }
            }
        
        # Generate prediction analysis plots
        logger.info("Generating prediction analysis plots...")
        plot_prediction_analysis(y, model.predict(X), output_dir)
        
        # Prepare results
        predictions_summary = {}
        try:
            predictions_summary = {
                'status': 'success',
                'mean_predicted_engagement': float(predictions_df['predicted_engagement'].mean()),
                'std_predicted_engagement': float(predictions_df['predicted_engagement'].std()),
                'min_predicted_engagement': float(predictions_df['predicted_engagement'].min()),
                'max_predicted_engagement': float(predictions_df['predicted_engagement'].max()),
                'samples': len(predictions_df)
            }
        except Exception as e:
            logger.error(f"Error calculating prediction summary: {str(e)}")
            predictions_summary = {
                'status': 'partial_success',
                'error': str(e),
                'samples': len(predictions_df)
            }
        
        results = {
            'model_evaluation': evaluation_results,
            'feature_importance': feature_importance,
            'predictions_summary': predictions_summary
        }
        
        # Save model and results
        try:
            joblib.dump(model, output_dir / "engagement_model.joblib")
            logger.info(f"Model saved to {output_dir / 'engagement_model.joblib'}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            results['model_save_error'] = str(e)
            
        try:
            predictions_df.to_csv(output_dir / "predictions.csv", index=False)
            logger.info(f"Predictions saved to {output_dir / 'predictions.csv'}")
        except Exception as e:
            logger.error(f"Error saving predictions: {str(e)}")
            results['predictions_save_error'] = str(e)
            
        try:
            with open(output_dir / "prediction_results.json", "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {output_dir / 'prediction_results.json'}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            results['results_save_error'] = str(e)
        
        logger.info("Prediction process complete.")
        return results
        
    except Exception as e:
        logger.error(f"Unexpected error in prediction process: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "error_trace": traceback.format_exc(),
            "predictions_summary": {
                "status": "error",
                "message": "Unexpected error in prediction process"
            }
        } 