"""
ML OPS Pipeline Module

This module defines ML Operations (MLOps) pipelines using modern best practices.
The pipelines handle the entire lifecycle of machine learning models:
- Data extraction and validation
- Feature engineering
- Model training
- Model evaluation
- Model deployment
- Model monitoring
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.sklearn
import mlflow.tensorflow
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset, TargetDriftPreset
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path("logs/mlops_pipeline.log").resolve())
    ]
)

# Create logger
logger = logging.getLogger("mlops_pipeline")

# Configure MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "social_media_trend_analysis")

# Model registry path
MODEL_REGISTRY_PATH = Path("models/registry").resolve()
MODEL_REGISTRY_PATH.mkdir(parents=True, exist_ok=True)

class MLOpsPipeline:
    """
    MLOps Pipeline for Social Media Trend Analysis
    
    This class implements a complete MLOps pipeline with:
    - Data validation
    - Feature engineering
    - Model training with experiment tracking
    - Model evaluation
    - Model versioning and deployment
    - Data drift detection
    """
    
    def __init__(
        self,
        model_name: str,
        version: str = None,
        config_path: str = None,
        data_path: str = None
    ):
        """
        Initialize the MLOps pipeline
        
        Args:
            model_name: Name of the model
            version: Model version (if None, will be generated)
            config_path: Path to configuration file
            data_path: Path to the data directory
        """
        self.model_name = model_name
        self.version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config_path = config_path or f"config/{model_name}_config.json"
        self.data_path = data_path or "data/processed"
        
        # Load configuration if exists
        self.config = self._load_config()
        
        # Setup directories
        self.model_dir = MODEL_REGISTRY_PATH / model_name / self.version
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MLflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        
        logger.info(f"Initialized MLOps pipeline for {model_name} (version: {self.version})")
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        config_path = Path(self.config_path)
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        
        # Default configuration
        logger.warning(f"Configuration file {self.config_path} not found. Using default configuration.")
        return {
            "data_split": {
                "test_size": 0.2,
                "validation_size": 0.1,
                "random_state": 42
            },
            "feature_engineering": {
                "categorical_features": [],
                "numerical_features": [],
                "text_features": [],
                "target": "target"
            },
            "model_params": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 2,
                "min_samples_leaf": 1
            },
            "training": {
                "epochs": 50,
                "batch_size": 32,
                "learning_rate": 0.001,
                "early_stopping_patience": 5
            },
            "evaluation": {
                "metrics": ["accuracy", "precision", "recall", "f1"]
            },
            "deployment": {
                "min_accuracy": 0.7,
                "auto_deploy": False
            },
            "monitoring": {
                "drift_threshold": 0.1,
                "check_frequency": "daily"
            }
        }
    
    def load_data(self) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        Load the training and reference data
        
        Returns:
            Tuple containing (training_data, reference_data)
        """
        logger.info("Loading data...")
        
        # Training data
        train_file = Path(self.data_path) / f"{self.model_name}_training_data.csv"
        if not train_file.exists():
            raise FileNotFoundError(f"Training data file not found: {train_file}")
        
        training_data = pd.read_csv(train_file)
        logger.info(f"Loaded training data: {training_data.shape}")
        
        # Reference data (for drift detection, optional)
        ref_file = Path(self.data_path) / f"{self.model_name}_reference_data.csv"
        reference_data = None
        if ref_file.exists():
            reference_data = pd.read_csv(ref_file)
            logger.info(f"Loaded reference data: {reference_data.shape}")
        
        return training_data, reference_data
    
    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Validate data quality
        
        Args:
            data: Input DataFrame
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        logger.info("Validating data quality...")
        
        # Data quality checks
        validation_report = {
            "total_rows": len(data),
            "missing_values": data.isnull().sum().to_dict(),
            "duplicate_rows": data.duplicated().sum(),
            "column_types": {col: str(dtype) for col, dtype in data.dtypes.items()},
            "numeric_stats": {},
            "categorical_stats": {}
        }
        
        # Check required columns
        required_columns = (
            self.config["feature_engineering"]["categorical_features"] +
            self.config["feature_engineering"]["numerical_features"] +
            self.config["feature_engineering"]["text_features"] +
            [self.config["feature_engineering"]["target"]]
        )
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        validation_report["missing_columns"] = missing_columns
        
        # Generate column statistics
        for col in data.columns:
            if pd.api.types.is_numeric_dtype(data[col]):
                validation_report["numeric_stats"][col] = {
                    "min": float(data[col].min()),
                    "max": float(data[col].max()),
                    "mean": float(data[col].mean()),
                    "std": float(data[col].std())
                }
            else:
                validation_report["categorical_stats"][col] = {
                    "unique_values": int(data[col].nunique()),
                    "top_5_values": data[col].value_counts().head(5).to_dict()
                }
        
        # Validation criteria
        is_valid = (
            len(missing_columns) == 0 and
            validation_report["duplicate_rows"] < len(data) * 0.05 and
            all(data[col].isnull().sum() < len(data) * 0.2 for col in required_columns if col in data.columns)
        )
        
        if is_valid:
            logger.info("Data validation successful")
        else:
            logger.warning("Data validation failed")
            logger.warning(f"Missing columns: {missing_columns}")
            
        # Save validation report
        report_path = self.model_dir / "data_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(validation_report, f, indent=2)
        
        return is_valid, validation_report
    
    def preprocess_data(self, data: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
        """
        Preprocess the data
        
        Args:
            data: Input DataFrame
            
        Returns:
            Tuple of (preprocessors, processed_data)
        """
        logger.info("Preprocessing data...")
        
        processed_data = data.copy()
        preprocessors = {}
        
        # Handle missing values
        for col in processed_data.columns:
            if processed_data[col].isnull().sum() > 0:
                if pd.api.types.is_numeric_dtype(processed_data[col]):
                    # Fill numeric with mean
                    fill_value = processed_data[col].mean()
                    processed_data[col] = processed_data[col].fillna(fill_value)
                    preprocessors[f"{col}_fillna"] = {"type": "fillna", "value": float(fill_value)}
                else:
                    # Fill categorical with mode
                    fill_value = processed_data[col].mode()[0]
                    processed_data[col] = processed_data[col].fillna(fill_value)
                    preprocessors[f"{col}_fillna"] = {"type": "fillna", "value": fill_value}
        
        # Scale numerical features
        numerical_features = self.config["feature_engineering"]["numerical_features"]
        if numerical_features:
            scaler = StandardScaler()
            processed_data[numerical_features] = scaler.fit_transform(processed_data[numerical_features])
            preprocessors["scaler"] = {"type": "standard_scaler", "object": scaler}
            
            # Save scaler
            scaler_path = self.model_dir / "scaler.joblib"
            joblib.dump(scaler, scaler_path)
        
        # Encode categorical features (one-hot encoding)
        categorical_features = self.config["feature_engineering"]["categorical_features"]
        for col in categorical_features:
            if col in processed_data.columns:
                # Get one-hot encoded columns
                one_hot = pd.get_dummies(processed_data[col], prefix=col, drop_first=False)
                
                # Save categories for later use
                preprocessors[f"{col}_categories"] = {
                    "type": "one_hot_encoder",
                    "categories": list(one_hot.columns)
                }
                
                # Add one-hot encoded columns to processed data
                processed_data = pd.concat([processed_data, one_hot], axis=1)
                
                # Drop original categorical column
                processed_data = processed_data.drop(col, axis=1)
        
        # Save preprocessors
        preprocessors_path = self.model_dir / "preprocessors.json"
        with open(preprocessors_path, "w") as f:
            # Remove non-serializable objects before saving
            serializable_preprocessors = {k: v for k, v in preprocessors.items() if "object" not in v}
            json.dump(serializable_preprocessors, f, indent=2)
            
        return preprocessors, processed_data
    
    def create_train_val_test_split(
        self, 
        data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Split data into training, validation, and test sets
        
        Args:
            data: Processed DataFrame
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        logger.info("Creating train-validation-test split...")
        
        # Get target column
        target = self.config["feature_engineering"]["target"]
        if target not in data.columns:
            raise ValueError(f"Target column '{target}' not found in data")
        
        # Extract target
        y = data[target]
        X = data.drop(target, axis=1)
        
        # First split: training+validation and test
        test_size = self.config["data_split"]["test_size"]
        random_state = self.config["data_split"]["random_state"]
        
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Second split: training and validation
        val_size = self.config["data_split"]["validation_size"] / (1 - test_size)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_size, random_state=random_state
        )
        
        logger.info(f"Training set: {X_train.shape}")
        logger.info(f"Validation set: {X_val.shape}")
        logger.info(f"Test set: {X_test.shape}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> Any:
        """
        Train the model using MLflow for tracking
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            
        Returns:
            Trained model object
        """
        logger.info(f"Training {self.model_name} model...")
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"{self.model_name}-{self.version}") as run:
            # Log parameters
            mlflow.log_params(self.config["model_params"])
            
            # Train model (example implementation for a neural network)
            # In production, you'd select model type based on config
            input_dim = X_train.shape[1]
            
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            # Compile model
            model.compile(
                optimizer=tf.keras.optimizers.Adam(
                    learning_rate=self.config["training"]["learning_rate"]
                ),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            # Create callbacks
            callbacks = [
                EarlyStopping(
                    patience=self.config["training"]["early_stopping_patience"],
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    factor=0.2,
                    patience=3,
                    min_lr=1e-6
                ),
                ModelCheckpoint(
                    filepath=str(self.model_dir / "best_model"),
                    save_best_only=True
                )
            ]
            
            # Train model
            history = model.fit(
                X_train.values,
                y_train.values,
                epochs=self.config["training"]["epochs"],
                batch_size=self.config["training"]["batch_size"],
                validation_data=(X_val.values, y_val.values),
                callbacks=callbacks,
                verbose=1
            )
            
            # Log metrics from training
            for epoch, (loss, val_loss) in enumerate(zip(history.history['loss'], history.history['val_loss'])):
                mlflow.log_metrics({
                    "train_loss": loss,
                    "val_loss": val_loss
                }, step=epoch)
            
            # Save model
            mlflow.tensorflow.log_model(model, "model")
            
            # Save training history
            history_path = self.model_dir / "training_history.json"
            with open(history_path, "w") as f:
                history_dict = {key: [float(x) for x in values] for key, values in history.history.items()}
                json.dump(history_dict, f, indent=2)
            
            logger.info(f"Model training completed. Run ID: {run.info.run_id}")
            
            return model
    
    def evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict:
        """
        Evaluate the model and log metrics
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test target
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model...")
        
        # Get predictions
        y_pred_proba = model.predict(X_test.values)
        y_pred = (y_pred_proba > 0.5).astype(int).flatten()
        
        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
            "recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
            "f1": f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        # Log metrics to MLflow
        with mlflow.start_run(run_name=f"{self.model_name}-{self.version}-evaluation"):
            mlflow.log_metrics(metrics)
        
        # Save evaluation results
        eval_path = self.model_dir / "evaluation_results.json"
        with open(eval_path, "w") as f:
            json.dump({k: float(v) for k, v in metrics.items()}, f, indent=2)
        
        logger.info(f"Evaluation metrics: {metrics}")
        
        return metrics
    
    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame
    ) -> Dict:
        """
        Detect data drift between reference and current data
        
        Args:
            reference_data: Reference data
            current_data: Current data
            
        Returns:
            Dictionary with drift metrics
        """
        logger.info("Detecting data drift...")
        
        # Use Evidently for drift detection
        data_drift_report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset()
        ])
        
        # Prepare column mapping
        target = self.config["feature_engineering"]["target"]
        column_mapping = {
            "target": target,
            "numerical_features": self.config["feature_engineering"]["numerical_features"],
            "categorical_features": self.config["feature_engineering"]["categorical_features"]
        }
        
        # Run drift detection
        data_drift_report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Save report
        report_path = self.model_dir / "data_drift_report.html"
        data_drift_report.save_html(str(report_path))
        
        # Extract metrics
        drift_metrics = {
            "timestamp": datetime.now().isoformat(),
            "dataset_drift": data_drift_report.as_dict()["metrics"][0]["result"]["dataset_drift"],
            "share_of_drifted_columns": data_drift_report.as_dict()["metrics"][0]["result"]["share_of_drifted_columns"],
            "drifted_columns": data_drift_report.as_dict()["metrics"][0]["result"]["drifted_columns_names"]
        }
        
        # Save drift metrics
        metrics_path = self.model_dir / "drift_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(drift_metrics, f, indent=2)
        
        logger.info(f"Data drift detected: {drift_metrics['dataset_drift']}")
        logger.info(f"Share of drifted columns: {drift_metrics['share_of_drifted_columns']}")
        
        return drift_metrics
    
    def register_model(self, metrics: Dict) -> Dict:
        """
        Register model in the registry
        
        Args:
            metrics: Evaluation metrics
            
        Returns:
            Dictionary with registration info
        """
        logger.info(f"Registering model {self.model_name} (version {self.version})...")
        
        # Check if model meets deployment criteria
        meets_criteria = metrics["accuracy"] >= self.config["deployment"]["min_accuracy"]
        
        # Registration info
        registration_info = {
            "model_name": self.model_name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "meets_criteria": meets_criteria,
            "status": "registered"
        }
        
        # Save registration info
        reg_path = self.model_dir / "registration_info.json"
        with open(reg_path, "w") as f:
            json.dump(registration_info, f, indent=2)
        
        # Update registry index
        registry_index_path = MODEL_REGISTRY_PATH / "registry_index.json"
        if registry_index_path.exists():
            with open(registry_index_path, "r") as f:
                registry_index = json.load(f)
        else:
            registry_index = {"models": {}}
        
        # Add or update model entry
        if self.model_name not in registry_index["models"]:
            registry_index["models"][self.model_name] = {
                "versions": [],
                "latest_version": None,
                "production_version": None
            }
        
        # Add version info
        registry_index["models"][self.model_name]["versions"].append({
            "version": self.version,
            "created_at": datetime.now().isoformat(),
            "accuracy": float(metrics["accuracy"]),
            "status": "registered"
        })
        
        # Update latest version
        registry_index["models"][self.model_name]["latest_version"] = self.version
        
        # If meets criteria and auto-deploy is True, set as production
        if meets_criteria and self.config["deployment"]["auto_deploy"]:
            registry_index["models"][self.model_name]["production_version"] = self.version
            registration_info["status"] = "production"
        
        # Save updated registry index
        with open(registry_index_path, "w") as f:
            json.dump(registry_index, f, indent=2)
        
        logger.info(f"Model registered: {registration_info['status']}")
        
        return registration_info
    
    def run_pipeline(self) -> Dict:
        """
        Run the complete ML pipeline
        
        Returns:
            Dictionary with pipeline results
        """
        logger.info(f"Starting ML pipeline for {self.model_name} (version: {self.version})")
        
        try:
            # Step 1: Load data
            training_data, reference_data = self.load_data()
            
            # Step 2: Validate data
            is_valid, validation_report = self.validate_data(training_data)
            if not is_valid:
                logger.error("Data validation failed, stopping pipeline")
                return {"status": "failed", "stage": "data_validation"}
            
            # Step 3: Preprocess data
            preprocessors, processed_data = self.preprocess_data(training_data)
            
            # Step 4: Split data
            X_train, X_val, X_test, y_train, y_val, y_test = self.create_train_val_test_split(processed_data)
            
            # Step 5: Train model
            model = self.train_model(X_train, y_train, X_val, y_val)
            
            # Step 6: Evaluate model
            metrics = self.evaluate_model(model, X_test, y_test)
            
            # Step 7: Detect data drift (if reference data is available)
            drift_metrics = None
            if reference_data is not None:
                # Preprocess reference data
                _, processed_reference = self.preprocess_data(reference_data)
                drift_metrics = self.detect_data_drift(processed_reference, processed_data)
            
            # Step 8: Register model
            registration_info = self.register_model(metrics)
            
            # Final pipeline status
            pipeline_results = {
                "status": "success",
                "model_name": self.model_name,
                "version": self.version,
                "metrics": metrics,
                "drift_detected": drift_metrics["dataset_drift"] if drift_metrics else None,
                "registration": registration_info
            }
            
            # Save pipeline results
            results_path = self.model_dir / "pipeline_results.json"
            with open(results_path, "w") as f:
                json.dump(pipeline_results, f, indent=2)
            
            logger.info(f"ML pipeline completed successfully for {self.model_name}")
            
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            logger.exception("Exception details:")
            
            return {"status": "failed", "error": str(e)}


def run_mlops_pipeline(model_name: str, config_path: str = None, data_path: str = None) -> Dict:
    """
    Run MLOps pipeline for a specific model
    
    Args:
        model_name: Name of the model
        config_path: Path to configuration file
        data_path: Path to the data directory
        
    Returns:
        Dictionary with pipeline results
    """
    pipeline = MLOpsPipeline(
        model_name=model_name,
        config_path=config_path,
        data_path=data_path
    )
    
    return pipeline.run_pipeline()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MLOps pipeline")
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--data", help="Path to data directory")
    
    args = parser.parse_args()
    
    results = run_mlops_pipeline(
        model_name=args.model,
        config_path=args.config,
        data_path=args.data
    )
    
    print(json.dumps(results, indent=2)) 