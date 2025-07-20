import sys
import json
from pathlib import Path

# Add src to path
sys.path.append("src")

def demo_extraction():
    """Demonstrate field extraction capabilities"""
    print("Smart Invoice AI System - Demo")
    print("=" * 40)
    
    # Sample invoice text
    sample_invoice = """
    Invoice #INV-2024-001
    Date: 2024-01-15
    From: ABC Company Ltd.
    
    Bill To: XYZ Corporation
    
    Description                 Qty    Price    Total
    Web Development Services     1     $2,500   $2,500
    Database Setup              1     $800     $800
    Testing & QA                1     $400     $400
    
    Subtotal:                           $3,700
    VAT (10%):                          $370
    Total Amount:                       $4,070
    """
    
    print("Sample Invoice Text:")
    print("-" * 20)
    print(sample_invoice)
    print("-" * 20)
    
    # Import and use the extractor
    try:
        try:
            from utils.config_fixed import Config
        except ImportError:
            from utils.config import Config
        
        try:
            from core.field_extractor_simple import FieldExtractor
        except ImportError:
            from core.field_extractor import FieldExtractor
        
        config = Config()
        extractor = FieldExtractor(config)
        
        # Extract fields
        result = extractor.extract_fields(sample_invoice)
        
        print("Extracted Fields:")
        print("-" * 20)
        
        for field, value in result.items():
            if field != "confidence_scores" and field != "line_items":
                confidence = result["confidence_scores"].get(field, 0)
                print(f"{field:15}: {str(value):20} (confidence: {confidence:.2%})")
        
        print("-" * 20)
        print("Extraction completed successfully!")
        
        # Save result
        with open("demo_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Result saved to demo_result.json")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    demo_extraction()

