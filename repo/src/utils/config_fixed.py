"""
Configuration settings for the Smart Invoice AI System
"""

import os
from pathlib import Path

class Config:
    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.models_dir = self.base_dir / "models"
        self.data_dir = self.base_dir / "data"
        self.database_dir = self.base_dir / "database"
        
        # Create directories if they don't exist
        self.models_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.database_dir.mkdir(exist_ok=True)
        
        # OCR settings
        self.ocr_language = 'eng'
        self.ocr_dpi = 300
        self.preprocessing_enabled = True
        
        # Model settings
        self.confidence_threshold = 0.7
        self.auto_retrain_threshold = 10
        self.max_model_versions = 5
        
        # Database settings
        self.database_path = self.database_dir / "invoice_system.db"
        
        # Supported file types
        self.supported_image_types = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        self.supported_document_types = ['.pdf']
        self.supported_data_types = ['.csv', '.txt']
        
        # Field extraction settings
        self.required_fields = [
            'invoice_number',
            'date',
            'supplier_name',
            'total_amount',
            'vat_amount',
            'line_items'
        ]
        
        # Model training settings
        self.min_training_samples = 5
        self.validation_split = 0.2
        self.max_epochs = 10
        self.batch_size = 8
    
    def update_settings(self, settings_dict):
        """Update configuration settings"""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_model_path(self, version="latest"):
        """Get path to model file"""
        if version == "latest":
            model_files = list(self.models_dir.glob("invoice_model_v*.pkl"))
            if model_files:
                return max(model_files, key=lambda x: x.stat().st_mtime)
            else:
                return self.models_dir / "invoice_model_v1.0.pkl"
        else:
            return self.models_dir / f"invoice_model_{version}.pkl"