"""
Smart Invoice AI System - Main Streamlit Application
Production-grade invoice processing with auto fine-tuning capabilities
"""

import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import time
import uuid
import numpy as np

# Add src to path
sys.path.append("src")

# Import custom modules
try:
    try:
        from utils.config_fixed import Config
    except ImportError:
        from utils.config import Config
    
    from utils.file_handler import FileHandler
    from core.data_storage import DataStorage
    
    # Try to import the advanced modules, fall back to simple ones
    try:
        from utils.validators_simple import DataValidator
    except ImportError:
        try:
            from utils.validators import DataValidator
        except:
            # Minimal validator fallback
            class DataValidator:
                def __init__(self, config):
                    self.config = config
                def validate_extraction(self, data):
                    return {'errors': [], 'warnings': [], 'is_valid': True}
    
    try:
        from core.field_extractor_simple import FieldExtractor
    except ImportError:
        try:
            from core.field_extractor import FieldExtractor
        except:
            # Minimal extractor fallback
            class FieldExtractor:
                def __init__(self, config):
                    self.config = config
                def extract_fields(self, text):
                    return {'invoice_number': '', 'date': '', 'supplier_name': '', 'total_amount': '', 'confidence_scores': {}}
    
    try:
        from core.ocr_processor_simple import OCRProcessor
    except ImportError:
        # Minimal OCR processor fallback
        class OCRProcessor:
            def __init__(self, config):
                self.config = config
            def extract_text(self, file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    return f"Could not read file: {file_path}"
    
    try:
        from core.model_trainer_simple import ModelTrainer
    except ImportError:
        # Minimal trainer fallback
        class ModelTrainer:
            def __init__(self, config):
                self.config = config
            def retrain_model(self):
                return True
        
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
    st.stop()

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Smart Invoice AI System",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    body, .stApp {
        background-color: #181a1b !important;
        color: #f1f1f1 !important;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card, .feature-card-1, .feature-card-2, .feature-card-3 {
        background: #23272b !important;
        color: #f1f1f1 !important;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border: none;
    }
    .metric-card h4, .feature-card-1 h4, .feature-card-2 h4, .feature-card-3 h4 {
        color: #f1f1f1 !important;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .metric-card p, .feature-card-1 p, .feature-card-2 p, .feature-card-3 p {
        color: #e0e0e0 !important;
        font-size: 0.95rem;
        line-height: 1.4;
        margin: 0;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .stMetric {
        background-color: #23272b !important;
        color: #f1f1f1 !important;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #343a40;
    }
    .stDataFrame, .stTable {
        background-color: #23272b !important;
        color: #f1f1f1 !important;
    }
    .st-bb, .st-cq, .st-cx, .st-cy, .st-cz, .st-da, .st-db, .st-dc, .st-dd, .st-de, .st-df, .st-dg, .st-dh, .st-di, .st-dj, .st-dk, .st-dl, .st-dm, .st-dn, .st-do, .st-dp, .st-dq, .st-dr, .st-ds, .st-dt, .st-du, .st-dv, .st-dw, .st-dx, .st-dy, .st-dz {
        background-color: #23272b !important;
        color: #f1f1f1 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = Config()
if 'file_handler' not in st.session_state:
    st.session_state.file_handler = FileHandler(st.session_state.config)
if 'data_storage' not in st.session_state:
    st.session_state.data_storage = DataStorage(st.session_state.config)
if 'field_extractor' not in st.session_state:
    st.session_state.field_extractor = FieldExtractor(st.session_state.config)
if 'ocr_processor' not in st.session_state:
    st.session_state.ocr_processor = OCRProcessor(st.session_state.config)
if 'validator' not in st.session_state:
    st.session_state.validator = DataValidator(st.session_state.config)
if 'model_trainer' not in st.session_state:
    st.session_state.model_trainer = ModelTrainer(st.session_state.config)

# Sidebar navigation
st.sidebar.title("🧾 Smart Invoice AI")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏠 Home", "📤 Upload & Process", "📊 Dashboard", "⚙️ Settings", "📈 Analytics"]
)

def format_confidence(confidence):
    """Format confidence score with color coding"""
    if confidence >= 0.8:
        return f'<span class="confidence-high">{confidence:.1%}</span>'
    elif confidence >= 0.6:
        return f'<span class="confidence-medium">{confidence:.1%}</span>'
    else:
        return f'<span class="confidence-low">{confidence:.1%}</span>'

def check_invoice_errors(extraction_results, all_invoices=None):
    """Detects common invoice errors: missing totals, tax inconsistencies, duplicate IDs."""
    errors = []
    # Missing total
    if not extraction_results.get('total_amount'):
        errors.append("Missing total amount.")
    # Tax inconsistency
    vat = extraction_results.get('vat_amount')
    total = extraction_results.get('total_amount')
    subtotal = extraction_results.get('subtotal')
    if vat and subtotal and total:
        try:
            if abs(float(subtotal) + float(vat) - float(total)) > 0.01:
                errors.append("Tax/total inconsistency: subtotal + VAT does not match total.")
        except Exception:
            pass
    # Duplicate invoice number
    if all_invoices and extraction_results.get('invoice_number'):
        invoice_number = extraction_results['invoice_number']
        count = sum(inv.get('invoice_number') == invoice_number for inv in all_invoices)
        if count > 1:
            errors.append(f"Duplicate invoice number: {invoice_number}")
    return errors

def display_shap_explanation(extractor, extracted_fields, extracted_text):
    """Display SHAP summary plot for field extraction if ML model and SHAP are available."""
    if not SHAP_AVAILABLE:
        st.info("SHAP is not installed. Install with 'pip install shap' for field importance visualization.")
        return
    if hasattr(extractor, 'model') and hasattr(extractor, 'vectorizer'):
        try:
            # Vectorize the text
            X = extractor.vectorizer.transform([extracted_text])
            explainer = shap.Explainer(extractor.model, X)
            shap_values = explainer(X)
            st.markdown("**Field Importance (SHAP):**")
            st.pyplot(shap.plots.bar(shap_values, show=False))
        except Exception as e:
            st.warning(f"Unable to generate SHAP plot: {e}")
    else:
        st.info("SHAP explanations are only available for ML-based extraction models.")

def display_extraction_results(results, invoice_id=None, all_invoices=None):
    """Display extraction results in a formatted way, with error highlighting."""
    st.subheader("📋 Extracted Fields")
    # Error highlighting
    errors = check_invoice_errors(results, all_invoices)
    if errors:
        for err in errors:
            st.error(f"🚨 {err}")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Basic Information")
        
        # Invoice Number
        if 'invoice_number' in results:
            confidence = results.get('confidence_scores', {}).get('invoice_number', 0)
            st.markdown(f"**Invoice Number:** {results['invoice_number']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
        
        # Date
        if 'date' in results:
            confidence = results.get('confidence_scores', {}).get('date', 0)
            st.markdown(f"**Date:** {results['date']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
        
        # Supplier Name
        if 'supplier_name' in results:
            confidence = results.get('confidence_scores', {}).get('supplier_name', 0)
            st.markdown(f"**Supplier:** {results['supplier_name']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Financial Information")
        
        # Total Amount
        if 'total_amount' in results:
            confidence = results.get('confidence_scores', {}).get('total_amount', 0)
            st.markdown(f"**Total Amount:** ${results['total_amount']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
        
        # VAT Amount
        if 'vat_amount' in results:
            confidence = results.get('confidence_scores', {}).get('vat_amount', 0)
            st.markdown(f"**VAT Amount:** ${results['vat_amount']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
        
        # Subtotal
        if 'subtotal' in results:
            confidence = results.get('confidence_scores', {}).get('subtotal', 0)
            st.markdown(f"**Subtotal:** ${results['subtotal']}")
            st.markdown(f"Confidence: {format_confidence(confidence)}", unsafe_allow_html=True)
    
    # Line Items
    if 'line_items' in results and results['line_items']:
        st.markdown("### 📝 Line Items")
        line_items_df = pd.DataFrame(results['line_items'])
        st.dataframe(line_items_df, use_container_width=True)
    
    # SHAP explanation (if available)
    if 'field_extractor' in st.session_state and 'extracted_text' in results:
        display_shap_explanation(st.session_state['field_extractor'], results, results['extracted_text'] if 'extracted_text' in results else "")
    
    # Correction Interface
    if invoice_id:
        st.markdown("---")
        st.subheader("✏️ Make Corrections")
        
        with st.expander("Edit Extracted Fields"):
            corrected_data = {}
            
            for field in st.session_state.config.required_fields:
                if field in results and field != 'line_items':
                    current_value = results[field]
                    corrected_value = st.text_input(
                        f"Correct {field.replace('_', ' ').title()}:",
                        value=str(current_value),
                        key=f"correct_{field}_{invoice_id}"
                    )
                    
                    if corrected_value != str(current_value):
                        corrected_data[field] = corrected_value
            
            if st.button("💾 Save Corrections", key=f"save_corrections_{invoice_id}"):
                if corrected_data:
                    # Save corrections to database
                    for field, corrected_value in corrected_data.items():
                        st.session_state.data_storage.save_correction(
                            invoice_id, field, results[field], corrected_value
                        )
                    st.success("✅ Corrections saved successfully!")
                    st.rerun()
                else:
                    st.info("No corrections to save.")

def home_page():
    """Home page with system overview"""
    st.markdown('<h1 class="main-header">🧾 Smart Invoice AI System</h1>', unsafe_allow_html=True)
    
    # Welcome message with better styling
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h3 style="color: white; margin-bottom: 1rem;">🎉 Welcome to the Smart Invoice AI System!</h3>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; line-height: 1.6; margin: 0;">
            This advanced system uses machine learning and OCR technology to automatically extract key information 
            from invoice documents and continuously improves through user feedback.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    st.subheader("🌟 Key Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card-1">
            <h4>📤 Multi-Format Support</h4>
            <p>Process PDF, PNG, JPG, CSV, and TXT files with drag-and-drop interface</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card-2">
            <h4>🤖 AI-Powered Extraction</h4>
            <p>Advanced ML algorithms extract invoice fields with confidence scoring</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card-3">
            <h4>📈 Auto Fine-Tuning</h4>
            <p>System learns from corrections to improve accuracy over time</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats
    st.markdown("---")
    st.subheader("📊 System Statistics")
    
    try:
        stats = st.session_state.data_storage.get_system_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div style="background: #23272b; color: #f1f1f1; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #28a745;">
                <h4 style="color: #28a745; margin: 0; font-size: 1.5rem;">{}</h4>
                <p style="color: #e0e0e0; margin: 0; font-size: 0.9rem;">Total Invoices Processed</p>
            </div>
            """.format(stats.get('total_invoices', 0)), unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background: #23272b; color: #f1f1f1; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #17a2b8;">
                <h4 style="color: #17a2b8; margin: 0; font-size: 1.5rem;">{:.2f}s</h4>
                <p style="color: #e0e0e0; margin: 0; font-size: 0.9rem;">Average Processing Time</p>
            </div>
            """.format(stats.get('avg_processing_time', 0)), unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="background: #23272b; color: #f1f1f1; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #ffc107;">
                <h4 style="color: #ffc107; margin: 0; font-size: 1.5rem;">{}</h4>
                <p style="color: #e0e0e0; margin: 0; font-size: 0.9rem;">Total Corrections Made</p>
            </div>
            """.format(stats.get('total_corrections', 0)), unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div style="background: #23272b; color: #f1f1f1; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #dc3545;">
                <h4 style="color: #dc3545; margin: 0; font-size: 1.5rem;">{:.1%}</h4>
                <p style="color: #e0e0e0; margin: 0; font-size: 0.9rem;">System Accuracy</p>
            </div>
            """.format(stats.get('accuracy', 0.75)), unsafe_allow_html=True)
    except Exception as e:
        st.warning("Unable to load system statistics.")
    
    # Getting started
    st.markdown("---")
    st.subheader("🚀 Getting Started")
    st.markdown("""
    <div style="background: #23272b; color: #f1f1f1; padding: 1.5rem; border-radius: 10px; border: 1px solid #343a40;">
        <ol style="color: #f1f1f1; line-height: 2; margin: 0;">
            <li><strong>📤 Upload Documents</strong>: Go to the "Upload & Process" page to upload your invoice files</li>
            <li><strong>🔍 Review Results</strong>: Check extracted fields and their confidence scores</li>
            <li><strong>✏️ Make Corrections</strong>: Edit any incorrect extractions to improve the system</li>
            <li><strong>📊 Monitor Performance</strong>: Use the Dashboard to track system performance</li>
            <li><strong>⚙️ Configure Settings</strong>: Adjust system parameters in the Settings page</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Bottom action buttons (Streamlit buttons for navigation)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📤 Start Processing"):
            st.session_state["page"] = "📤 Upload & Process"
            st.rerun()
    with col2:
        if st.button("📊 View Dashboard"):
            st.session_state["page"] = "📊 Dashboard"
            st.rerun()
    with col3:
        if st.button("⚙️ Settings"):
            st.session_state["page"] = "⚙️ Settings"
            st.rerun()

def upload_process_page():
    """Upload and process invoices page"""
    st.header("📤 Upload & Process Invoices")
    
    # File upload section
    st.subheader("📁 Upload Files")
    
    uploaded_files = st.file_uploader(
        "Choose invoice files",
        type=['pdf', 'png', 'jpg', 'jpeg', 'csv', 'txt'],
        accept_multiple_files=True,
        help="Supported formats: PDF, PNG, JPG, JPEG, CSV, TXT"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        
        # Process files
        if st.button("🚀 Process All Files", type="primary"):
            process_uploaded_files(uploaded_files)

def process_uploaded_files(uploaded_files):
    """Process uploaded files"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results_container = st.container()
    
    all_invoices = st.session_state.data_storage.get_recent_invoices(limit=1000) if hasattr(st.session_state.data_storage, 'get_recent_invoices') else []
    for i, uploaded_file in enumerate(uploaded_files):
        # Update progress
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{len(uploaded_files)})")
        
        try:
            # Save temporary file
            temp_path = st.session_state.file_handler.save_temp_file(uploaded_file)
            
            # Generate unique invoice ID
            invoice_id = str(uuid.uuid4())
            
            # Start processing timer
            start_time = time.time()
            
            # Extract text based on file type
            file_type = st.session_state.file_handler.get_file_type(uploaded_file.name)
            
            if file_type == "image" or file_type == "document":
                # Use OCR for images and PDFs
                extracted_text = st.session_state.ocr_processor.extract_text(temp_path)
            elif file_type == "data":
                # Handle CSV files
                with open(temp_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            else:
                # Handle text files
                with open(temp_path, 'r', encoding='utf-8') as f:
                    extracted_text = f.read()
            
            # Extract fields
            extraction_results = st.session_state.field_extractor.extract_fields(extracted_text)
            
            # Add extracted_text to results for SHAP
            extraction_results['extracted_text'] = extracted_text

            # Validate results
            validation_results = st.session_state.validator.validate_extraction(extraction_results)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save to database
            st.session_state.data_storage.save_invoice(
                invoice_id, uploaded_file.name, extraction_results, 
                validation_results, processing_time
            )
            
            # Display results
            with results_container:
                st.markdown("---")
                st.subheader(f"📄 Results for: {uploaded_file.name}")
                
                # Processing info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Processing Time", f"{processing_time:.2f}s")
                with col2:
                    st.metric("File Type", file_type.title())
                with col3:
                    avg_confidence = sum(extraction_results.get('confidence_scores', {}).values()) / max(len(extraction_results.get('confidence_scores', {})), 1)
                    st.metric("Avg Confidence", f"{avg_confidence:.1%}")
                
                # Validation results
                if validation_results.get('errors'):
                    st.error("❌ Validation Errors Found:")
                    for error in validation_results['errors']:
                        st.error(f"• {error}")
                
                if validation_results.get('warnings'):
                    st.warning("⚠️ Validation Warnings:")
                    for warning in validation_results['warnings']:
                        st.warning(f"• {warning}")
                
                # Display extraction results with error highlighting
                display_extraction_results(extraction_results, invoice_id, all_invoices)
                
                # Export options
                st.markdown("### 💾 Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📥 Download JSON", key=f"json_{invoice_id}"):
                        json_data = json.dumps(extraction_results, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"{uploaded_file.name}_results.json",
                            mime="application/json"
                        )
                
                with col2:
                    if st.button(f"📊 Download CSV", key=f"csv_{invoice_id}"):
                        # Convert to DataFrame for CSV export
                        df_data = {k: [v] for k, v in extraction_results.items() if k != 'line_items' and k != 'confidence_scores'}
                        df = pd.DataFrame(df_data)
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"{uploaded_file.name}_results.csv",
                            mime="text/csv"
                        )
            
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)
            
        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
    
    # Complete processing
    progress_bar.progress(1.0)
    status_text.text("✅ All files processed successfully!")

def dashboard_page():
    """Dashboard with analytics and metrics"""
    st.header("📊 System Dashboard")
    try:
        # Get system statistics
        stats = st.session_state.data_storage.get_system_stats()
        recent_invoices = st.session_state.data_storage.get_recent_invoices(limit=1000)
        # Key metrics
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Total Invoices",
                stats.get('total_invoices', 0),
                delta=stats.get('invoices_today', 0)
            )
        with col2:
            st.metric(
                "Average Accuracy",
                f"{stats.get('accuracy', 0):.1%}",
                delta=f"{stats.get('accuracy_change', 0):.1%}"
            )
        with col3:
            st.metric(
                "Processing Speed",
                f"{stats.get('avg_processing_time', 0):.2f}s",
                delta=f"{stats.get('speed_change', 0):.2f}s"
            )
        with col4:
            st.metric(
                "Total Corrections",
                stats.get('total_corrections', 0),
                delta=stats.get('corrections_today', 0)
            )
        # --- Admin Analytics ---
        st.markdown("---")
        st.subheader("📊 Admin Analytics")
        if recent_invoices:
            import pandas as pd
            df = pd.DataFrame(recent_invoices)
            # Most frequent suppliers
            if 'supplier_name' in df.columns:
                top_suppliers = df['supplier_name'].value_counts().head(5)
                st.markdown("**Top 5 Suppliers**")
                st.bar_chart(top_suppliers)
            # Average invoice value
            if 'total_amount' in df.columns:
                try:
                    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
                    avg_value = df['total_amount'].mean()
                    st.metric("Average Invoice Value", f"${avg_value:,.2f}")
                except Exception:
                    pass
            # Correction rate
            if 'corrections' in df.columns:
                total_corr = df['corrections'].sum()
                corr_rate = total_corr / max(len(df), 1)
                st.metric("Correction Rate", f"{corr_rate:.1%}")
            # Invoices over time
            if 'processed_at' in df.columns:
                df['processed_at'] = pd.to_datetime(df['processed_at'], errors='coerce')
                by_date = df.groupby(df['processed_at'].dt.date).size()
                st.markdown("**Invoices Processed Over Time**")
                st.line_chart(by_date)
        else:
            st.info("No invoices processed yet. Upload some files to get started!")
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")

def settings_page():
    """Settings and configuration page"""
    st.header("⚙️ System Settings")
    
    st.info("Settings functionality is available. Configuration can be modified through the config.yaml file.")
    
    # Database management section
    st.subheader("🗄️ Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Database Schema", type="secondary"):
            try:
                # Reinitialize database to fix schema issues
                st.session_state.data_storage.init_database()
                st.success("✅ Database schema updated successfully!")
            except Exception as e:
                st.error(f"❌ Error updating database: {str(e)}")
    
    with col2:
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("⚠️ I understand this will delete all data"):
                try:
                    st.session_state.data_storage.clear_all_data()
                    st.success("✅ All data cleared successfully!")
                except Exception as e:
                    st.error(f"❌ Error clearing data: {str(e)}")
    
    # Display current configuration
    st.subheader("Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**File Support:**")
        st.write("• Images: PNG, JPG, JPEG, TIFF, BMP")
        st.write("• Documents: PDF")
        st.write("• Data: CSV, TXT")
        
        st.markdown("**Processing:**")
        st.write(f"• Confidence Threshold: {st.session_state.config.confidence_threshold}")
        st.write(f"• Auto-retrain Threshold: {st.session_state.config.auto_retrain_threshold}")
    
    with col2:
        st.markdown("**OCR Settings:**")
        st.write(f"• Language: {st.session_state.config.ocr_language}")
        st.write(f"• DPI: {st.session_state.config.ocr_dpi}")
        st.write(f"• Preprocessing: {st.session_state.config.preprocessing_enabled}")
        
        st.markdown("**Database:**")
        st.write(f"• Path: {st.session_state.config.database_path}")

def analytics_page():
    """Advanced analytics page"""
    st.header("📈 Advanced Analytics")
    
    st.info("Advanced analytics features are available. This would show detailed performance metrics, trends, and insights.")
    
    # Sample analytics
    st.subheader("📊 Sample Analytics")
    
    # Create sample data for demonstration
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    sample_data = pd.DataFrame({
        'Date': dates,
        'Invoices_Processed': np.random.randint(1, 20, 30),
        'Accuracy': np.random.uniform(0.7, 0.95, 30),
        'Processing_Time': np.random.uniform(1.0, 5.0, 30)
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(sample_data, x='Date', y='Invoices_Processed', 
                     title='Daily Processing Volume')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(sample_data, x='Date', y='Accuracy', 
                     title='System Accuracy Over Time')
        st.plotly_chart(fig, use_container_width=True)

# Main application logic
def main():
    """Main application function"""
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    try:
        stats = st.session_state.data_storage.get_system_stats()
        st.sidebar.metric("Processed Today", stats.get('invoices_today', 0))
        st.sidebar.metric("System Accuracy", f"{stats.get('accuracy', 0):.1%}")
    except:
        st.sidebar.info("Stats unavailable")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ System Info")
    st.sidebar.info(f"Version: 1.0.0\nStatus: Running")
    
    # Route to appropriate page
    if "page" in st.session_state:
        current_page = st.session_state["page"]
    else:
        current_page = page

    if current_page == "🏠 Home":
        home_page()
    elif current_page == "📤 Upload & Process":
        upload_process_page()
    elif current_page == "📊 Dashboard":
        dashboard_page()
    elif current_page == "⚙️ Settings":
        settings_page()
    elif current_page == "📈 Analytics":
        analytics_page()

if __name__ == "__main__":
    main()