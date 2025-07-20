"""
Smart Invoice AI System - Main Streamlit Application
Production-grade invoice processing with auto fine-tuning capabilities
"""

import streamlit as st
import os
from pathlib import Path

st.set_page_config(page_title="Smart Invoice AI System", layout="wide")
st.title("Smart Invoice AI System")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Upload & Process", "Review & Corrections", "Download Results", "Dashboard"])

# Placeholder imports for core logic
try:
    from src.core.ocr_processor import OCRProcessor
    from src.core.field_extractor import AdvancedMLFieldExtractor
    from src.core.data_storage import DataStorage
    from src.utils.validators import InvoiceValidator
    from src.utils.config import Config
except ImportError:
    OCRProcessor = None
    AdvancedMLFieldExtractor = None
    DataStorage = None
    InvoiceValidator = None
    Config = None

# Initialize config and core modules if available
config = Config() if Config else None
ocr = OCRProcessor(config) if OCRProcessor and config else None
extractor = AdvancedMLFieldExtractor(config) if AdvancedMLFieldExtractor and config else None
data_storage = DataStorage(config) if DataStorage and config else None
validator = InvoiceValidator() if InvoiceValidator else None

if page == "Upload & Process":
    st.header("Upload & Process Invoices")
    uploaded_files = st.file_uploader("Upload invoice files (PDF, PNG, JPG, JPEG, CSV, TXT)", type=["pdf", "png", "jpg", "jpeg", "csv", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"**File:** {uploaded_file.name}")
            # Save file to temp location
            temp_path = Path("data") / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Extract text (placeholder)
            extracted_text = None
            if ocr:
                try:
                    extracted_text = ocr.extract_text(temp_path)
                except Exception as e:
                    st.error(f"OCR extraction failed: {e}")
            else:
                st.warning("OCR module not available. Showing file content as text.")
                try:
                    extracted_text = temp_path.read_text(errors="ignore")
                except Exception:
                    extracted_text = "(Unable to read file as text)"
            st.text_area("Extracted Text", extracted_text, height=200)
            # Extract fields (placeholder)
            fields = {}
            if extractor and extracted_text:
                try:
                    fields = extractor.extract_fields(extracted_text)
                except Exception as e:
                    st.error(f"Field extraction failed: {e}")
            else:
                fields = {"invoice_number": "", "date": "", "supplier_name": "", "total_amount": ""}
            st.write("### Extracted Fields")
            for k, v in fields.items():
                st.write(f"**{k}**: {v}")
            # Validation (placeholder)
            if validator and fields:
                try:
                    validation = validator.validate_invoice(fields)
                    st.write("#### Validation Results")
                    st.json(validation)
                except Exception as e:
                    st.warning(f"Validation failed: {e}")
            # Save to storage (placeholder)
            if data_storage and fields:
                try:
                    data_storage.store_invoice_data(uploaded_file.name, fields)
                    st.success("Invoice data saved.")
                except Exception as e:
                    st.warning(f"Data storage failed: {e}")

elif page == "Review & Corrections":
    st.header("Review & Corrections")
    st.info("Feature under development. Corrections and feedback will be available here.")

elif page == "Download Results":
    st.header("Download Results")
    st.info("Feature under development. You will be able to download processed invoices here.")

elif page == "Dashboard":
    st.header("Dashboard & Statistics")
    st.info("Feature under development. Model performance and statistics will be shown here.")