import logging
import os
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import seaborn as sns
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer

# Setup logging
log_path = Path("logs/evaluation.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_models():
    """Load trained models"""
    try:
        models_dir = Path('models')
        
        # Load TF-IDF vectorizer
        tfidf = joblib.load(models_dir / 'tfidf_vectorizer.joblib')
        
        # Load Random Forest model
        rf_model = joblib.load(models_dir / 'random_forest.joblib')
        
        # Load Sentence Transformer
        st_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load embeddings
        embeddings = np.load(models_dir / 'sentence_embeddings.npy')
        
        return {
            'tfidf': tfidf,
            'rf_model': rf_model,
            'st_model': st_model,
            'embeddings': embeddings
        }
    except Exception as e:
        logging.error(f"Error loading models: {str(e)}")
        raise

def evaluate_model_performance(models, test_data):
    """Evaluate model performance on test data"""
    try:
        # Transform test data
        X_test_tfidf = models['tfidf'].transform(test_data['combined_text'])
        
        # Get predictions
        y_pred = models['rf_model'].predict(X_test_tfidf)
        
        # Generate classification report
        report = classification_report(
            test_data['engagement_label'],
            y_pred,
            target_names=['Low Engagement', 'High Engagement']
        )
        logging.info(f"Classification Report:\n{report}")
        
        # Generate confusion matrix
        cm = confusion_matrix(test_data['engagement_label'], y_pred)
        
        # Plot confusion matrix
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Low Engagement', 'High Engagement'],
            yticklabels=['Low Engagement', 'High Engagement']
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        # Save plot
        plots_dir = Path('plots')
        plots_dir.mkdir(exist_ok=True)
        plt.savefig(plots_dir / 'confusion_matrix.png')
        plt.close()
        
        return report, cm
        
    except Exception as e:
        logging.error(f"Error evaluating model performance: {str(e)}")
        raise

def analyze_feature_importance(models):
    """Analyze feature importance"""
    try:
        # Get feature names
        feature_names = models['tfidf'].get_feature_names_out()
        
        # Get feature importance
        importance = models['rf_model'].feature_importances_
        
        # Create feature importance DataFrame
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        })
        
        # Sort by importance
        feature_importance = feature_importance.sort_values(
            'importance',
            ascending=False
        ).head(20)
        
        # Plot feature importance
        plt.figure(figsize=(12, 6))
        sns.barplot(
            x='importance',
            y='feature',
            data=feature_importance
        )
        plt.title('Top 20 Most Important Features')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        
        # Save plot
        plots_dir = Path('plots')
        plots_dir.mkdir(exist_ok=True)
        plt.savefig(plots_dir / 'feature_importance.png')
        plt.close()
        
        return feature_importance
        
    except Exception as e:
        logging.error(f"Error analyzing feature importance: {str(e)}")
        raise

def analyze_embeddings(models, test_data):
    """Analyze sentence embeddings"""
    try:
        # Get embeddings for test data
        test_embeddings = models['st_model'].encode(test_data['combined_text'].tolist())
        
        # Calculate average embedding for each class
        high_engagement_emb = test_embeddings[test_data['engagement_label'] == 1].mean(axis=0)
        low_engagement_emb = test_embeddings[test_data['engagement_label'] == 0].mean(axis=0)
        
        # Calculate cosine similarity between class embeddings
        similarity = np.dot(high_engagement_emb, low_engagement_emb) / (
            np.linalg.norm(high_engagement_emb) * np.linalg.norm(low_engagement_emb)
        )
        
        logging.info(f"Cosine similarity between high and low engagement embeddings: {similarity}")
        
        return similarity
        
    except Exception as e:
        logging.error(f"Error analyzing embeddings: {str(e)}")
        raise

def main():
    """Main evaluation function"""
    try:
        # Load models
        models = load_models()
        
        # Load test data
        test_data = pd.read_csv('data/processed/test_data.csv')
        
        # Evaluate model performance
        report, cm = evaluate_model_performance(models, test_data)
        
        # Analyze feature importance
        feature_importance = analyze_feature_importance(models)
        
        # Analyze embeddings
        similarity = analyze_embeddings(models, test_data)
        
        logging.info("Evaluation completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main evaluation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 