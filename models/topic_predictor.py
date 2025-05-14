import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from typing import List, Tuple, Dict

class TopicPredictor:
    def __init__(self, sequence_length: int = 10):
        """
        Initialize the TopicPredictor model.
        
        Args:
            sequence_length (int): Number of time steps to use for prediction
        """
        self.sequence_length = sequence_length
        self.scaler = StandardScaler()
        self.model = None
        
    def _build_model(self, input_shape: Tuple[int, int]) -> None:
        """
        Build the LSTM model architecture.
        
        Args:
            input_shape (tuple): Shape of input data (sequence_length, features)
        """
        self.model = Sequential([
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(input_shape[1])  # Output dimension same as number of topics
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare input sequences for the LSTM model.
        
        Args:
            data (pd.DataFrame): Topic frequency data over time
            
        Returns:
            Tuple of input sequences and target values
        """
        scaled_data = self.scaler.fit_transform(data)
        X, y = [], []
        
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:(i + self.sequence_length)])
            y.append(scaled_data[i + self.sequence_length])
            
        return np.array(X), np.array(y)
    
    def fit(self, data: pd.DataFrame, epochs: int = 100, batch_size: int = 32) -> None:
        """
        Train the model on historical topic data.
        
        Args:
            data (pd.DataFrame): Historical topic frequency data
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
        """
        X, y = self.prepare_sequences(data)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        if self.model is None:
            self._build_model((self.sequence_length, data.shape[1]))
            
        self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            verbose=1
        )
    
    def predict_next_period(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Predict topic frequencies for the next time period.
        
        Args:
            data (pd.DataFrame): Recent topic frequency data
            
        Returns:
            pd.DataFrame: Predicted topic frequencies
        """
        if len(data) < self.sequence_length:
            raise ValueError(f"Input data must contain at least {self.sequence_length} time periods")
            
        # Scale the input data
        scaled_data = self.scaler.transform(data)
        
        # Prepare the input sequence
        sequence = scaled_data[-self.sequence_length:]
        sequence = sequence.reshape(1, self.sequence_length, data.shape[1])
        
        # Make prediction
        prediction = self.model.predict(sequence)
        
        # Inverse transform the prediction
        prediction_unscaled = self.scaler.inverse_transform(prediction)
        
        # Convert to DataFrame with same column names as input
        return pd.DataFrame(prediction_unscaled, columns=data.columns) 