"""
Simple OCR Processing Module
Handles text extraction from images and PDFs
"""

import os
from pathlib import Path

class OCRProcessor:
    def __init__(self, config):
        self.config = config
        
    def extract_text(self, file_path):
        """Extract text from file based on its type"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in self.config.supported_image_types:
            return self.extract_from_image(file_path)
        elif file_path.suffix.lower() in self.config.supported_document_types:
            return self.extract_from_pdf(file_path)
        else:
            # For text files, just read directly
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    
    def extract_from_image(self, image_path):
        """Extract text from image using OCR (simplified version)"""
        try:
            import pytesseract
            from PIL import Image
            
            # Load image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.config.ocr_language,
                config=f'--dpi {self.config.ocr_dpi}'
            )
            
            return text.strip()
            
        except ImportError:
            # Fallback if OCR libraries not available
            return f"OCR not available. Please install pytesseract and tesseract-ocr.\nFile: {image_path.name}"
        except Exception as e:
            return f"Error processing image: {str(e)}"
    
    def extract_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except ImportError:
            return f"PDF processing not available. Please install PyPDF2.\nFile: {pdf_path.name}"
        except Exception as e:
            return f"Error processing PDF: {str(e)}"