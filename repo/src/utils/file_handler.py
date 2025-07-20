"""
File Handler Module
Handles file operations and temporary file management
"""

import os
import tempfile
from pathlib import Path
import shutil

class FileHandler:
    def __init__(self, config):
        self.config = config
        self.temp_dir = Path(tempfile.gettempdir()) / "smart_invoice_ai"
        self.temp_dir.mkdir(exist_ok=True)
    
    def save_temp_file(self, uploaded_file):
        """Save uploaded file to temporary location"""
        temp_path = self.temp_dir / uploaded_file.name
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return temp_path
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
    
    def is_supported_file(self, filename):
        """Check if file type is supported"""
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        supported_extensions = (
            self.config.supported_image_types +
            self.config.supported_document_types +
            self.config.supported_data_types
        )
        
        return extension in supported_extensions
    
    def get_file_type(self, filename):
        """Get file type category"""
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension in self.config.supported_image_types:
            return "image"
        elif extension in self.config.supported_document_types:
            return "document"
        elif extension in self.config.supported_data_types:
            return "data"
        else:
            return "unknown"
