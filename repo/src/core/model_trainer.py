"""
Model Training Module
Handles model training and fine-tuning based on user corrections
"""

import pickle
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import sqlite3

class ModelTrainer:
    def __init__(self, config):
        self.config = config
        self.data_storage = None
    
    def set_data_storage(self, data_storage):
        """Set data storage reference"""
        self.data_storage = data_storage
    
    def retrain_model(self):
        """Retrain model with new correction data"""
        try:
            # Get training data from corrections
            training_data = self._prepare_training_data()
            
            if len(training_data) < self.config.min_training_samples:
                return {
                    "success": False,
                    "error": f"Not enough training samples. Need at least {self.config.min_training_samples}, got {len(training_data)}"
                }
            
            # Train new model
            model, vectorizer, accuracy = self._train_model(training_data)
            
            # Generate new version
            new_version = self._generate_version()
            
            # Save model
            self._save_model(model, vectorizer, new_version, accuracy, len(training_data))
            
            return {
                "success": True,
                "version": new_version,
                "accuracy": accuracy,
                "training_samples": len(training_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_training_data(self):
        """Prepare training data from corrections"""
        training_data = []
        
        if not self.data_storage:
            return training_data
        
        with sqlite3.connect(self.config.database_path) as conn:
            cursor = conn.cursor()
            
            # Get corrections with original invoice text
            cursor.execute("""
                SELECT c.field_name, c.original_value, c.corrected_value, i.extracted_data
                FROM corrections c
                JOIN invoices i ON c.invoice_id = i.id
            """)
            
            results = cursor.fetchall()
            
            for row in results:
                field_name, original_value, corrected_value, extracted_data_json = row
                
                try:
                    extracted_data = json.loads(extracted_data_json)
                    
                    # Create training example
                    training_example = {
                        "field_name": field_name,
                        "original_value": original_value,
                        "corrected_value": corrected_value,
                        "context": extracted_data,
                        "needs_correction": 1 if original_value != corrected_value else 0
                    }
                    
                    training_data.append(training_example)
                    
                except json.JSONDecodeError:
                    continue
        
        return training_data
    
    def _train_model(self, training_data):
        """Train the correction prediction model"""
        # Prepare features and labels
        features = []
        labels = []
        
        vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        
        # Extract text features
        texts = []
        for example in training_data:
            # Combine field context for feature extraction
            context_text = f"{example[\"field_name\"]} {example[\"original_value\"]}"
            texts.append(context_text)
            labels.append(example["needs_correction"])
        
        # Vectorize text
        text_features = vectorizer.fit_transform(texts)
        
        # Add additional features
        for i, example in enumerate(training_data):
            additional_features = [
                len(example["original_value"]),
                1 if example["original_value"] else 0,
                len(example["field_name"])
            ]
            
            # Combine text and additional features
            combined_features = np.hstack([
                text_features[i].toarray()[0],
                additional_features
            ])
            features.append(combined_features)
        
        features = np.array(features)
        labels = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=self.config.validation_split, random_state=42
        )
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return model, vectorizer, accuracy
    
    def _generate_version(self):
        """Generate new model version"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
    
    def _save_model(self, model, vectorizer, version, accuracy, training_samples):
        """Save trained model and metadata"""
        # Save model file
        model_path = self.config.models_dir / f"invoice_model_{version}.pkl"
        
        model_data = {
            "model": model,
            "vectorizer": vectorizer,
            "version": version,
            "accuracy": accuracy,
            "training_samples": training_samples,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)
        
        # Save metadata to database
        if self.data_storage:
            with sqlite3.connect(self.config.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO model_versions (id, version, accuracy, training_samples)
                    VALUES (?, ?, ?, ?)
                """, (version, version, accuracy, training_samples))
                conn.commit()
    
    def get_training_status(self):
        """Get current training status"""
        with sqlite3.connect(self.config.database_path) as conn:
            cursor = conn.cursor()
            
            # Get latest model version
            cursor.execute("SELECT version, accuracy, training_samples, created_at FROM model_versions ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                version, accuracy, training_samples, created_at = result
                return {
                    "current_version": version,
                    "accuracy": accuracy,
                    "training_samples": training_samples,
                    "last_training": created_at
                }
            else:
                return {
                    "current_version": "v1.0",
                    "accuracy": 0.75,
                    "training_samples": 0,
                    "last_training": "Never"
                }
    
    def export_current_model(self):
        """Export current model for download"""
        model_path = self.config.get_model_path()
        return model_path
