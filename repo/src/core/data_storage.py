"""
Data Storage Module
Handles database operations and data persistence
"""

import sqlite3
import json
from datetime import datetime
import uuid
from pathlib import Path

class DataStorage:
    def __init__(self, config):
        self.config = config
        self.db_path = config.database_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    extracted_data TEXT NOT NULL,
                    validation_results TEXT,
                    processing_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if validation_results column exists, add if missing
            cursor.execute("PRAGMA table_info(invoices)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'validation_results' not in columns:
                cursor.execute("ALTER TABLE invoices ADD COLUMN validation_results TEXT")
            
            if 'processing_time' not in columns:
                cursor.execute("ALTER TABLE invoices ADD COLUMN processing_time REAL")
            
            # Corrections table
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
            
            # Model versions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id TEXT PRIMARY KEY,
                    version TEXT NOT NULL,
                    accuracy REAL,
                    training_samples INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def store_invoice_data(self, filename, extracted_data, validation_results=None, processing_time=None):
        """Store invoice processing results"""
        invoice_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (id, filename, extracted_data, validation_results, processing_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                invoice_id,
                filename,
                json.dumps(extracted_data),
                json.dumps(validation_results) if validation_results else None,
                processing_time
            ))
            conn.commit()
        
        return invoice_id
    
    def store_corrections(self, invoice_id, corrections):
        """Store user corrections"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for field_name, correction_data in corrections.items():
                correction_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO corrections (id, invoice_id, field_name, original_value, corrected_value)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    correction_id,
                    invoice_id,
                    field_name,
                    correction_data["original"],
                    correction_data["corrected"]
                ))
            
            conn.commit()
    
    def get_system_stats(self):
        """Get system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total invoices
            cursor.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cursor.fetchone()[0]
            
            # Total corrections
            cursor.execute("SELECT COUNT(*) FROM corrections")
            total_corrections = cursor.fetchone()[0]
            
            # Current model version
            cursor.execute("SELECT version FROM model_versions ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            model_version = result[0] if result else "v1.0"
            
            # Model accuracy
            cursor.execute("SELECT accuracy FROM model_versions ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            model_accuracy = result[0] if result else 0.75
            
            # Average processing time
            cursor.execute("SELECT AVG(processing_time) FROM invoices WHERE processing_time IS NOT NULL")
            result = cursor.fetchone()
            avg_processing_time = result[0] if result and result[0] else 0.0
            
            # Today's invoices
            cursor.execute("""
                SELECT COUNT(*) FROM invoices 
                WHERE DATE(created_at) = DATE('now')
            """)
            invoices_today = cursor.fetchone()[0]
            
            # Today's corrections
            cursor.execute("""
                SELECT COUNT(*) FROM corrections 
                WHERE DATE(created_at) = DATE('now')
            """)
            corrections_today = cursor.fetchone()[0]
            
            return {
                "total_invoices": total_invoices,
                "total_corrections": total_corrections,
                "model_version": model_version,
                "accuracy": model_accuracy,
                "avg_processing_time": avg_processing_time,
                "invoices_today": invoices_today,
                "corrections_today": corrections_today,
                "accuracy_change": 0.0,  # Placeholder
                "speed_change": 0.0      # Placeholder
            }
    
    def get_recent_activity(self, limit=10):
        """Get recent processing activity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, created_at, processing_time
                FROM invoices
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            
            return [
                {
                    "filename": row[0],
                    "processed_at": row[1],
                    "processing_time": row[2]
                }
                for row in results
            ]
    
    def get_correction_count(self):
        """Get total number of corrections"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM corrections")
            return cursor.fetchone()[0]
    
    def save_invoice(self, invoice_id, filename, extracted_data, validation_results=None, processing_time=None):
        """Save invoice processing results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (id, filename, extracted_data, validation_results, processing_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                invoice_id,
                filename,
                json.dumps(extracted_data),
                json.dumps(validation_results) if validation_results else None,
                processing_time
            ))
            conn.commit()
    
    def save_correction(self, invoice_id, field_name, original_value, corrected_value):
        """Save a single correction"""
        correction_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO corrections (id, invoice_id, field_name, original_value, corrected_value)
                VALUES (?, ?, ?, ?, ?)
            """, (
                correction_id,
                invoice_id,
                field_name,
                str(original_value),
                str(corrected_value)
            ))
            conn.commit()
    
    def get_recent_invoices(self, limit=10):
        """Get recent invoices for dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, created_at, processing_time
                FROM invoices
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            
            return [
                {
                    "filename": row[0],
                    "processed_at": row[1],
                    "processing_time": f"{row[2]:.2f}s" if row[2] else "N/A"
                }
                for row in results
            ]
    
    def clear_all_data(self):
        """Clear all data from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM corrections")
            cursor.execute("DELETE FROM invoices")
            cursor.execute("DELETE FROM model_versions")
            cursor.execute("DELETE FROM system_stats")
            conn.commit()
    
    def backup_database(self):
        """Create a backup of the database"""
        import shutil
        backup_path = self.db_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(self.db_path, backup_path)
        return backup_path
    
    def get_dashboard_metrics(self):
        """Get metrics for dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Basic metrics
            cursor.execute("SELECT COUNT(*) FROM invoices")
            total_invoices = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(processing_time) FROM invoices WHERE processing_time IS NOT NULL")
            result = cursor.fetchone()
            avg_processing_time = result[0] if result[0] else 0
            
            return {
                "total_invoices": total_invoices,
                "invoices_delta": 0,
                "avg_accuracy": 0.85,
                "accuracy_delta": 0.02,
                "avg_processing_time": avg_processing_time,
                "time_delta": 0,
                "error_rate": 0.05,
                "error_delta": -0.01
            }
    
    def clear_all_data(self):
        """Clear all data from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM corrections")
            cursor.execute("DELETE FROM invoices")
            cursor.execute("DELETE FROM model_versions")
            cursor.execute("DELETE FROM system_stats")
            conn.commit()
    
    def export_all_data(self):
        """Export all data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Export invoices
            cursor.execute("SELECT * FROM invoices")
            invoices = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            
            # Export corrections
            cursor.execute("SELECT * FROM corrections")
            corrections = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            
            return {
                "invoices": invoices,
                "corrections": corrections,
                "export_timestamp": datetime.now().isoformat()
            }
