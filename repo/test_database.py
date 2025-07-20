#!/usr/bin/env python3
"""
Test Database Operations
"""

import sys
import uuid
import json
from datetime import datetime

# Add src to path
sys.path.append("src")

try:
    from utils.config_fixed import Config
    from core.data_storage import DataStorage
except ImportError:
    print("Error importing modules")
    sys.exit(1)

def test_database():
    """Test database operations"""
    print("Testing Database Operations")
    print("=" * 30)
    
    try:
        # Initialize
        config = Config()
        storage = DataStorage(config)
        
        # Test data
        invoice_id = str(uuid.uuid4())
        filename = "test_invoice.pdf"
        extracted_data = {
            "invoice_number": "TEST-001",
            "date": "2024-01-15",
            "supplier_name": "Test Company",
            "total_amount": "1000.00",
            "confidence_scores": {
                "invoice_number": 0.95,
                "date": 0.85,
                "supplier_name": 0.80,
                "total_amount": 0.90
            }
        }
        validation_results = {
            "errors": [],
            "warnings": ["Test warning"],
            "is_valid": True
        }
        processing_time = 2.5
        
        print("1. Testing save_invoice...")
        storage.save_invoice(invoice_id, filename, extracted_data, validation_results, processing_time)
        print("✅ Invoice saved successfully")
        
        print("2. Testing save_correction...")
        storage.save_correction(invoice_id, "total_amount", "1000.00", "1050.00")
        print("✅ Correction saved successfully")
        
        print("3. Testing get_system_stats...")
        stats = storage.get_system_stats()
        print(f"✅ Stats retrieved: {stats}")
        
        print("4. Testing get_recent_invoices...")
        recent = storage.get_recent_invoices(limit=5)
        print(f"✅ Recent invoices: {len(recent)} found")
        
        print("\n🎉 All database operations working correctly!")
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_database()