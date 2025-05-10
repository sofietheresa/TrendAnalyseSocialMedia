import logging
import os
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
from sentence_transformers import SentenceTransformer

# Setup logging
log_path = Path("logs/training.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_processed_data():
    """Load processed data from all platforms"""
    try:
        data = {}
        platforms = ['reddit', 'tiktok', 'youtube', 'twitter']
        
        for platform in platforms:
            file_path = f'data/processed/{platform}_processed.csv'
            if os.path.exists(file_path):
                data[platform] = pd.read_csv(file_path)
                logging.info(f"Loaded {len(data[platform])} processed records from {platform}")
            else:
                logging.warning(f"No processed data file found for {platform}")
                
        return data
    except Exception as e:
        logging.error(f"Error loading processed data: {str(e)}")
        raise

def prepare_training_data(data):
    """Prepare data for training"""
    try:
        # Combine all platform data
        combined_data = []
        
        for platform, df in data.items():
            # Platform-specific text columns
            text_columns = {
                'reddit': ['title_processed', 'text_processed'],
                'tiktok': ['desc_processed'],
                'youtube': ['title_processed', 'description_processed'],
                'twitter': ['content_processed']
            }
            
            # Combine text columns
            text_cols = text_columns.get(platform, [])
            df['combined_text'] = df[text_cols].fillna('').apply(
                lambda x: ' '.join(x.astype(str)), axis=1
            )
            
            # Add to combined data
            combined_data.append(df[['combined_text', 'engagement_score']])
        
        # Concatenate all data
        combined_df = pd.concat(combined_data, ignore_index=True)
        
        # Create binary engagement labels (high/low)
        combined_df['engagement_label'] = (
            combined_df['engagement_score'] > combined_df['engagement_score'].median()
        ).astype(int)
        
        return combined_df
        
    except Exception as e:
        logging.error(f"Error preparing training data: {str(e)}")
        raise

def train_models(data):
    """Train text classification models"""
    try:
        # Split data
        X = data['combined_text']
        y = data['engagement_label']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # TF-IDF Vectorizer
        tfidf = TfidfVectorizer(max_features=5000)
        X_train_tfidf = tfidf.fit_transform(X_train)
        X_test_tfidf = tfidf.transform(X_test)
        
        # Train Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train_tfidf, y_train)
        
        # Evaluate
        y_pred = rf_model.predict(X_test_tfidf)
        report = classification_report(y_test, y_pred)
        logging.info(f"Random Forest Classification Report:\n{report}")
        
        # Save models
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        joblib.dump(tfidf, models_dir / 'tfidf_vectorizer.joblib')
        joblib.dump(rf_model, models_dir / 'random_forest.joblib')
        
        # Train Sentence Transformer
        st_model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = st_model.encode(X.tolist())
        
        # Save embeddings
        np.save(models_dir / 'sentence_embeddings.npy', embeddings)
        
        logging.info("Models trained and saved successfully")
        
    except Exception as e:
        logging.error(f"Error training models: {str(e)}")
        raise

def main():
    """Main training function"""
    try:
        # Load processed data
        processed_data = load_processed_data()
        
        # Prepare training data
        training_data = prepare_training_data(processed_data)
        
        # Train models
        train_models(training_data)
        
        logging.info("Training completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main training: {str(e)}")
        raise

if __name__ == "__main__":
    main() 