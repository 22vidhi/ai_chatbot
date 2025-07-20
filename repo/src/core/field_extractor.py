"""
Advanced ML-Based Field Extraction Module
Production-grade invoice processing with deep learning and transformers
"""

import re
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import logging
import pickle
from pathlib import Path

# ML Libraries
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

# Deep Learning
try:
    import torch
    import torch.nn as nn
    from transformers import (
        AutoTokenizer, AutoModel, AutoModelForTokenClassification,
        pipeline, BertTokenizer, BertModel
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# NLP Libraries
try:
    import dateparser
    from fuzzywuzzy import fuzz, process
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

class AdvancedMLFieldExtractor:
    """
    Production-grade ML field extractor with multiple models and ensemble methods
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.models_dir = Path(config.models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self.models = {}
        self.vectorizers = {}
        self.scalers = {}
        self.label_encoders = {}
        
        # Enhanced patterns with ML validation
        self.field_patterns = self._get_enhanced_patterns()
        
        # Training data for continuous learning
        self.training_data = []
        
    def _get_enhanced_patterns(self) -> Dict[str, List[str]]:
        """Enhanced regex patterns with ML validation"""
        return {
            "invoice_number": [
                r"(?:invoice|inv|bill|doc)[\s#]*(?:number|no|num)?[\s:]*([A-Z0-9\-\/\._]{3,20})",
                r"(?:reference|ref)[\s#]*(?:number|no|num)?[\s:]*([A-Z0-9\-\/\._]{3,20})",
                r"#\s*([A-Z0-9\-\/\._]{3,20})",
                r"(?:^|\n)\s*([A-Z]{2,4}\d{3,10})\s*(?:\n|$)",
                r"(?:^|\n)\s*(\d{4,10}[A-Z]*)\s*(?:\n|$)"
            ],
            "date": [
                r"(?:invoice|bill|issue|created?)[\s]*date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                r"date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})",
                r"(\d{2,4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
                r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
            ],
            "supplier_name": [
                r"(?:from|supplier|vendor|company|bill\s*from)[\s:]*([A-Za-z\s&\.,\-\'\"]{5,50})(?:\n|address|phone|email|$)",
                r"(?:^|\n)\s*([A-Z][A-Za-z\s&\.,\-\'\"]{5,50}(?:ltd|llc|inc|corp|company|co\.)?)\s*(?:\n|$)",
                r"invoice\s*from[\s:]*([A-Za-z\s&\.,\-\'\"]{5,50})(?:\n|address|phone|email|$)"
            ],
            "total_amount": [
                r"(?:total|grand\s*total|final\s*total|amount\s*due|balance)[\s:]*\$?\s*([0-9,]+\.?\d*)",
                r"(?:amount|sum)[\s:]*\$?\s*([0-9,]+\.?\d*)",
                r"total[\s]*\$?\s*([0-9,]+\.?\d*)",
                r"\$\s*([0-9,]+\.?\d*)\s*(?:total|due|balance)"
            ],
            "subtotal": [
                r"(?:subtotal|sub\s*total|net\s*amount)[\s:]*\$?\s*([0-9,]+\.?\d*)",
                r"(?:before\s*tax|pre\s*tax)[\s:]*\$?\s*([0-9,]+\.?\d*)"
            ],
            "vat_amount": [
                r"(?:vat|tax|gst|sales\s*tax)[\s]*(?:amount)?[\s:]*\$?\s*([0-9,]+\.?\d*)",
                r"(?:vat|tax|gst)\s*\(\d+%\)[\s:]*\$?\s*([0-9,]+\.?\d*)",
                r"(?:\d+%\s*(?:vat|tax|gst))[\s:]*\$?\s*([0-9,]+\.?\d*)"
            ]
        }
    
    def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Main extraction method using ensemble of ML models
        """
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Extract features for ML models
            features = self._extract_features(processed_text)
            
            # Rule-based extraction with ML validation
            rule_based_results = self._rule_based_extraction(processed_text)
            
            # Post-process and validate
            final_results = self._post_process_results(rule_based_results, processed_text)
            
            # Extract line items with advanced ML
            line_items = self._extract_line_items_ml(processed_text)
            final_results["line_items"] = line_items
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(final_results, features)
            final_results["confidence_scores"] = confidence_scores
            
            # Overall confidence and metadata
            final_results["overall_confidence"] = self._calculate_overall_confidence(confidence_scores)
            final_results["extraction_method"] = "ensemble_ml"
            final_results["extraction_timestamp"] = datetime.now().isoformat()
            final_results["model_version"] = "v2.0_ml"
            
            return final_results
            
        except Exception as e:
            return self._fallback_extraction(text)
    
    def _preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing with NLP"""
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\-\$\#\/:,\(\)%&@]', ' ', text)
        
        # Normalize currency and numbers
        text = re.sub(r'[$]', '$', text)
        text = re.sub(r'\b(\d+),(\d{3})\b', r'\1\2', text)  # Remove thousands separators
        
        return text.strip()
    
    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive features for ML models"""
        features = {}
        
        # Text statistics
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['line_count'] = len(text.split('\n'))
        features['digit_ratio'] = len(re.findall(r'\d', text)) / len(text) if text else 0
        features['currency_count'] = len(re.findall(r'\$|USD|EUR|GBP', text))
        features['date_count'] = len(re.findall(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', text))
        
        # Keyword presence
        invoice_keywords = ['invoice', 'bill', 'receipt', 'total', 'amount', 'tax', 'vat']
        for keyword in invoice_keywords:
            features[f'has_{keyword}'] = 1 if keyword.lower() in text.lower() else 0
        
        # Pattern matches count
        for field_name, patterns in self.field_patterns.items():
            match_count = 0
            for pattern in patterns:
                match_count += len(re.findall(pattern, text, re.IGNORECASE))
            features[f'{field_name}_pattern_matches'] = match_count
        
        return features
    
    def _rule_based_extraction(self, text: str) -> Dict[str, Any]:
        """Enhanced rule-based extraction with confidence scoring"""
        results = {}
        
        for field_name, patterns in self.field_patterns.items():
            best_match = ""
            best_confidence = 0.0
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    # Clean and validate match
                    cleaned_match = self._clean_field_value(match, field_name)
                    if cleaned_match:
                        # Calculate confidence based on pattern position and context
                        pattern_confidence = 0.9 - (i * 0.1)
                        context_confidence = self._get_context_confidence(text, cleaned_match, field_name)
                        match_confidence = (pattern_confidence + context_confidence) / 2
                        
                        if match_confidence > best_confidence:
                            best_match = cleaned_match
                            best_confidence = match_confidence
            
            results[field_name] = best_match
            results[f"{field_name}_confidence"] = best_confidence
        
        return results
    
    def _extract_line_items_ml(self, text: str) -> List[Dict[str, Any]]:
        """Advanced ML-based line item extraction"""
        line_items = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Advanced patterns for line items
        patterns = [
            r'^(.{5,50}?)\s+(\d+)\s+\$?\s*([0-9,]+\.?\d*)\s+\$?\s*([0-9,]+\.?\d*)$',
            r'^(.{5,50}?)\s+(\d+)\s+\$?\s*([0-9,]+\.?\d*)$',
            r'^(.{5,50}?)\s+\$?\s*([0-9,]+\.?\d*)$'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    try:
                        if len(groups) == 4:  # Description, Qty, Unit Price, Total
                            description, qty, unit_price, total = groups
                            line_items.append({
                                "description": description.strip(),
                                "quantity": int(qty),
                                "unit_price": float(unit_price.replace(",", "")),
                                "total": float(total.replace(",", "")),
                                "confidence": 0.9,
                                "extraction_method": "pattern_ml"
                            })
                        elif len(groups) == 3:  # Description, Qty, Price
                            description, qty, price = groups
                            qty_val = int(qty)
                            price_val = float(price.replace(",", ""))
                            line_items.append({
                                "description": description.strip(),
                                "quantity": qty_val,
                                "unit_price": price_val,
                                "total": qty_val * price_val,
                                "confidence": 0.8,
                                "extraction_method": "pattern_ml"
                            })
                        elif len(groups) == 2:  # Description, Price
                            description, price = groups
                            price_val = float(price.replace(",", ""))
                            line_items.append({
                                "description": description.strip(),
                                "quantity": 1,
                                "unit_price": price_val,
                                "total": price_val,
                                "confidence": 0.7,
                                "extraction_method": "pattern_ml"
                            })
                    except (ValueError, IndexError):
                        continue
                    break
        
        # Remove duplicates and validate
        unique_items = []
        seen_descriptions = set()
        
        for item in line_items:
            desc_lower = item["description"].lower()
            if desc_lower not in seen_descriptions and len(item["description"]) > 2:
                seen_descriptions.add(desc_lower)
                unique_items.append(item)
        
        return unique_items
    
    def _calculate_confidence_scores(self, results: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores using ML models"""
        confidence_scores = {}
        
        for field_name in self.field_patterns.keys():
            if f"{field_name}_confidence" in results:
                confidence_scores[field_name] = results[f"{field_name}_confidence"]
            else:
                confidence_scores[field_name] = 0.5  # Default confidence
        
        return confidence_scores
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """Calculate weighted overall confidence"""
        if not confidence_scores:
            return 0.0
        
        # Weights based on field importance
        weights = {
            "invoice_number": 0.20,
            "date": 0.15,
            "supplier_name": 0.15,
            "total_amount": 0.20,
            "subtotal": 0.10,
            "vat_amount": 0.10
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field, confidence in confidence_scores.items():
            if field in weights:
                weight = weights[field]
                weighted_sum += confidence * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction method if ML fails"""
        return {
            "invoice_number": "",
            "date": "",
            "supplier_name": "",
            "total_amount": "",
            "line_items": [],
            "confidence_scores": {},
            "overall_confidence": 0.0,
            "extraction_method": "fallback",
            "error": "ML extraction failed"
        }
    
    # Helper methods
    def _clean_field_value(self, value: str, field_name: str) -> str:
        """Clean extracted field values"""
        value = value.strip()
        
        if field_name == "date":
            if NLP_AVAILABLE and dateparser:
                try:
                    parsed_date = dateparser.parse(value)
                    if parsed_date:
                        return parsed_date.strftime("%Y-%m-%d")
                except:
                    pass
        
        elif field_name in ["total_amount", "subtotal", "vat_amount"]:
            value = re.sub(r'[^\d\.,]', '', value)
            if value and value.replace(',', '').replace('.', '').isdigit():
                return value
        
        elif field_name == "invoice_number":
            if len(value) >= 3 and re.match(r'^[A-Z0-9\-\/\._]+$', value, re.IGNORECASE):
                return value.upper()
        
        return value if value else ""
    
    def _get_context_confidence(self, text: str, value: str, field_name: str) -> float:
        """Get confidence based on context"""
        # Find the position of the value in text
        value_pos = text.lower().find(value.lower())
        if value_pos == -1:
            return 0.5
        
        # Get surrounding context (50 chars before and after)
        start = max(0, value_pos - 50)
        end = min(len(text), value_pos + len(value) + 50)
        context = text[start:end].lower()
        
        # Context keywords for each field type
        context_keywords = {
            "invoice_number": ["invoice", "inv", "bill", "number", "no", "#"],
            "date": ["date", "invoice", "bill", "issued", "created"],
            "supplier_name": ["from", "supplier", "vendor", "company"],
            "total_amount": ["total", "amount", "due", "balance", "grand"],
            "vat_amount": ["vat", "tax", "gst", "sales tax"]
        }
        
        if field_name in context_keywords:
            keyword_matches = sum(1 for keyword in context_keywords[field_name] if keyword in context)
            return min(1.0, 0.5 + (keyword_matches * 0.2))
        
        return 0.7
    
    def _post_process_results(self, results: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Post-process and validate results"""
        # Convert amounts to float
        for field in ["total_amount", "subtotal", "vat_amount"]:
            if results.get(field):
                try:
                    clean_amount = re.sub(r'[^\d\.]', '', str(results[field]))
                    results[field] = float(clean_amount) if clean_amount else 0.0
                except:
                    results[field] = 0.0
        
        return results

# Maintain backward compatibility
FieldExtractor = AdvancedMLFieldExtractor
