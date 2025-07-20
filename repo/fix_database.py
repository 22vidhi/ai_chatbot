#!/usr/bin/env python3
"""
Database Fix Script for Smart Invoice AI System
Fixes database schema issues
"""

import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.append("src")

try:
    from utils.config_fixed import Config
except ImportError:
    from utils.config import Config

def fix_database():
    """Fix database schema issues"""
    print("Smart Invoice AI - Database Fix")
    print("=" * 40)
    
    try:
        config = Config()
        db_path = config.database_path
        
        print(f"Database path: {db_path}")
        
        # Ensure database directory exists
        db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("Checking database schema...")
            
            # Check current schema
            cursor.execute("PRAGMA table_info(invoices)")
            columns = cursor.fetchall()
            
            if not columns:
                print("Creating invoices table...")
                cursor.execute("""
                    CREATE TABLE invoices (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        extracted_data TEXT NOT NULL,
                        validation_results TEXT,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                print("Invoices table exists. Checking columns...")
                column_names = [col[1] for col in columns]
                print(f"Current columns: {column_names}")
                
                # Add missing columns
                if 'validation_results' not in column_names:
                    print("Adding validation_results column...")
                    cursor.execute("ALTER TABLE invoices ADD COLUMN validation_results TEXT")
                
                if 'processing_time' not in column_names:
                    print("Adding processing_time column...")
                    cursor.execute("ALTER TABLE invoices ADD COLUMN processing_time REAL")
            
            # Create other tables
            print("Creating corrections table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    original_value TEXT,
                    corrected_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
                )
            """)
            
            print("Creating model_versions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    accuracy REAL,
                    training_samples INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            print("Creating system_stats table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
        print("✅ Database schema fixed successfully!")
        print("\nYou can now run the application:")
        print("streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Error fixing database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    fix_database()