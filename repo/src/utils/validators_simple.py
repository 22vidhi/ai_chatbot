"""
Simple Data Validation Module
Validates extracted invoice data for consistency and completeness
"""

import re
from datetime import datetime

class DataValidator:
    def __init__(self, config):
        self.config = config
    
    def validate_extraction(self, extracted_data):
        """Validate extracted invoice data"""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.config.required_fields:
            if field not in extracted_data or not extracted_data[field]:
                if field in ['invoice_number', 'total_amount']:
                    errors.append(f"Missing required field: {field}")
                else:
                    warnings.append(f"Missing optional field: {field}")
        
        # Validate specific fields
        if 'total_amount' in extracted_data and extracted_data['total_amount']:
            if not self._is_valid_amount(extracted_data['total_amount']):
                errors.append("Invalid total amount format")
        
        if 'vat_amount' in extracted_data and extracted_data['vat_amount']:
            if not self._is_valid_amount(extracted_data['vat_amount']):
                errors.append("Invalid VAT amount format")
        
        if 'date' in extracted_data and extracted_data['date']:
            if not self._is_valid_date(extracted_data['date']):
                warnings.append("Date format may be incorrect")
        
        if 'invoice_number' in extracted_data and extracted_data['invoice_number']:
            if len(extracted_data['invoice_number']) < 3:
                warnings.append("Invoice number seems too short")
        
        # Cross-field validation
        if ('total_amount' in extracted_data and 'vat_amount' in extracted_data and 
            extracted_data['total_amount'] and extracted_data['vat_amount']):
            try:
                total = float(extracted_data['total_amount'])
                vat = float(extracted_data['vat_amount'])
                if vat > total:
                    errors.append("VAT amount cannot be greater than total amount")
            except ValueError:
                pass  # Already caught in amount validation
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
    
    def _is_valid_amount(self, amount_str):
        """Check if amount string is valid"""
        try:
            # Remove common currency symbols and spaces
            cleaned = re.sub(r'[^\d\.]', '', str(amount_str))
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _is_valid_date(self, date_str):
        """Basic date validation"""
        date_patterns = [
            r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
            r'\d{2,4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{2,4}'
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, str(date_str)):
                return True
        return False