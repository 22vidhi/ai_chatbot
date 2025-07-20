"""
Simple Field Extraction Module
Basic rule-based field extraction for invoices
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any

class FieldExtractor:
    def __init__(self, config):
        self.config = config
        self.field_patterns = self._get_patterns()
    
    def _get_patterns(self) -> Dict[str, List[str]]:
        """Basic regex patterns for field extraction"""
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
        """Main extraction method"""
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Rule-based extraction
            results = self._rule_based_extraction(processed_text)
            
            # Extract line items
            line_items = self._extract_line_items(processed_text)
            results["line_items"] = line_items
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(results)
            results["confidence_scores"] = confidence_scores
            
            # Add metadata
            results["extraction_timestamp"] = datetime.now().isoformat()
            results["extraction_method"] = "rule_based"
            
            return results
            
        except Exception as e:
            return self._fallback_extraction(text)
    
    def _preprocess_text(self, text: str) -> str:
        """Basic text preprocessing"""
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\-\$\#\/:,\(\)%&@]', ' ', text)
        
        # Normalize currency and numbers
        text = re.sub(r'[$]', '$', text)
        text = re.sub(r'\b(\d+),(\d{3})\b', r'\1\2', text)  # Remove thousands separators
        
        return text.strip()
    
    def _rule_based_extraction(self, text: str) -> Dict[str, Any]:
        """Basic rule-based extraction"""
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
                        # Calculate confidence based on pattern position
                        pattern_confidence = 0.9 - (i * 0.1)
                        if pattern_confidence > best_confidence:
                            best_match = cleaned_match
                            best_confidence = pattern_confidence
            
            results[field_name] = best_match if best_match else ""
        
        return results
    
    def _clean_field_value(self, value: str, field_name: str) -> str:
        """Clean and validate field values"""
        if not value:
            return ""
        
        value = value.strip()
        
        if field_name in ['total_amount', 'subtotal', 'vat_amount']:
            # Clean monetary values
            value = re.sub(r'[^\d\.]', '', value)
            try:
                float(value)
                return value
            except ValueError:
                return ""
        
        elif field_name == 'date':
            # Basic date validation
            if re.match(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', value):
                return value
            return ""
        
        elif field_name in ['invoice_number', 'supplier_name']:
            # Basic text cleaning
            return re.sub(r'\s+', ' ', value).strip()
        
        return value
    
    def _extract_line_items(self, text: str) -> List[Dict[str, str]]:
        """Extract line items from invoice"""
        line_items = []
        
        # Look for table-like structures
        lines = text.split('\n')
        
        for line in lines:
            # Simple pattern for line items: description, quantity, price, total
            pattern = r'(.+?)\s+(\d+)\s+\$?([0-9,]+\.?\d*)\s+\$?([0-9,]+\.?\d*)'
            match = re.search(pattern, line)
            
            if match:
                description, qty, price, total = match.groups()
                line_items.append({
                    'description': description.strip(),
                    'quantity': qty,
                    'unit_price': price,
                    'total': total
                })
        
        return line_items
    
    def _calculate_confidence_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for extracted fields"""
        confidence_scores = {}
        
        for field, value in results.items():
            if field == 'line_items':
                confidence_scores[field] = 0.8 if value else 0.0
            elif value and value.strip():
                # Basic confidence based on field type and value quality
                if field in ['total_amount', 'subtotal', 'vat_amount']:
                    try:
                        float(value)
                        confidence_scores[field] = 0.85
                    except ValueError:
                        confidence_scores[field] = 0.3
                elif field == 'date':
                    confidence_scores[field] = 0.8 if re.match(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', value) else 0.4
                elif field == 'invoice_number':
                    confidence_scores[field] = 0.9 if len(value) >= 3 else 0.5
                elif field == 'supplier_name':
                    confidence_scores[field] = 0.7 if len(value) >= 5 else 0.4
                else:
                    confidence_scores[field] = 0.6
            else:
                confidence_scores[field] = 0.0
        
        return confidence_scores
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction when main method fails"""
        return {
            "invoice_number": "",
            "date": "",
            "supplier_name": "",
            "total_amount": "",
            "subtotal": "",
            "vat_amount": "",
            "line_items": [],
            "confidence_scores": {
                "invoice_number": 0.0,
                "date": 0.0,
                "supplier_name": 0.0,
                "total_amount": 0.0,
                "subtotal": 0.0,
                "vat_amount": 0.0,
                "line_items": 0.0
            },
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "fallback",
            "error": "Extraction failed, using fallback"
        }

# Alias for compatibility
AdvancedMLFieldExtractor = FieldExtractor