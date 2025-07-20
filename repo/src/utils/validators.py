"""
Validation Module
Validates extracted invoice data for consistency and completeness
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

class InvoiceValidator:
    def __init__(self):
        self.validation_rules = {
            "invoice_number": self._validate_invoice_number,
            "date": self._validate_date,
            "supplier_name": self._validate_supplier_name,
            "total_amount": self._validate_amount,
            "vat_amount": self._validate_amount,
            "line_items": self._validate_line_items
        }
    
    def validate_invoice(self, extracted_data):
        """Validate complete invoice data"""
        issues = []
        is_valid = True
        
        for field, validator in self.validation_rules.items():
            if field in extracted_data:
                field_issues = validator(extracted_data[field])
                if field_issues:
                    issues.extend([f"{field}: {issue}" for issue in field_issues])
                    is_valid = False
        
        # Cross-field validations
        cross_field_issues = self._validate_cross_fields(extracted_data)
        if cross_field_issues:
            issues.extend(cross_field_issues)
            is_valid = False
        
        return {
            "is_valid": is_valid,
            "issues": issues
        }
    
    def _validate_invoice_number(self, value):
        """Validate invoice number"""
        issues = []
        
        if not value or not str(value).strip():
            issues.append("Invoice number is required")
        elif len(str(value)) < 3:
            issues.append("Invoice number too short")
        elif not re.match(r"^[A-Za-z0-9\-_]+$", str(value)):
            issues.append("Invoice number contains invalid characters")
        
        return issues
    
    def _validate_date(self, value):
        """Validate date"""
        issues = []
        
        if not value or not str(value).strip():
            issues.append("Date is required")
        else:
            # Try to parse date
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]
            parsed = False
            
            for fmt in date_formats:
                try:
                    datetime.strptime(str(value), fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            
            if not parsed:
                issues.append("Invalid date format")
        
        return issues
    
    def _validate_supplier_name(self, value):
        """Validate supplier name"""
        issues = []
        
        if not value or not str(value).strip():
            issues.append("Supplier name is required")
        elif len(str(value).strip()) < 2:
            issues.append("Supplier name too short")
        
        return issues
    
    def _validate_amount(self, value):
        """Validate monetary amount"""
        issues = []
        
        if not value:
            return issues  # Amount can be empty for some fields
        
        try:
            # Clean the value
            cleaned_value = str(value).replace(",", "").replace("$", "").strip()
            amount = Decimal(cleaned_value)
            
            if amount < 0:
                issues.append("Amount cannot be negative")
            elif amount > Decimal("999999.99"):
                issues.append("Amount seems unusually large")
                
        except (InvalidOperation, ValueError):
            issues.append("Invalid amount format")
        
        return issues
    
    def _validate_line_items(self, value):
        """Validate line items"""
        issues = []
        
        if not value:
            issues.append("No line items found")
            return issues
        
        if not isinstance(value, list):
            issues.append("Line items should be a list")
            return issues
        
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                issues.append(f"Line item {i+1} should be a dictionary")
                continue
            
            # Validate required fields in line item
            if "description" not in item or not item["description"]:
                issues.append(f"Line item {i+1} missing description")
            
            if "quantity" not in item:
                issues.append(f"Line item {i+1} missing quantity")
            else:
                try:
                    qty = int(item["quantity"])
                    if qty <= 0:
                        issues.append(f"Line item {i+1} quantity must be positive")
                except (ValueError, TypeError):
                    issues.append(f"Line item {i+1} invalid quantity")
            
            if "price" not in item:
                issues.append(f"Line item {i+1} missing price")
            else:
                try:
                    price = float(item["price"])
                    if price < 0:
                        issues.append(f"Line item {i+1} price cannot be negative")
                except (ValueError, TypeError):
                    issues.append(f"Line item {i+1} invalid price")
        
        return issues
    
    def _validate_cross_fields(self, extracted_data):
        """Validate relationships between fields"""
        issues = []
        
        # Check if total amount matches line items
        if "line_items" in extracted_data and "total_amount" in extracted_data:
            line_items = extracted_data["line_items"]
            total_amount = extracted_data["total_amount"]
            
            if line_items and total_amount:
                try:
                    calculated_total = sum(
                        float(item.get("quantity", 0)) * float(item.get("price", 0))
                        for item in line_items
                        if isinstance(item, dict)
                    )
                    
                    declared_total = float(str(total_amount).replace(",", "").replace("$", ""))
                    
                    # Allow 5% tolerance for rounding differences
                    tolerance = declared_total * 0.05
                    if abs(calculated_total - declared_total) > tolerance:
                        issues.append(f"Total amount mismatch: calculated ${calculated_total:.2f}, declared ${declared_total:.2f}")
                        
                except (ValueError, TypeError):
                    pass  # Skip validation if amounts cannot be parsed
        
        # Check VAT calculation
        if "vat_amount" in extracted_data and "total_amount" in extracted_data:
            vat_amount = extracted_data["vat_amount"]
            total_amount = extracted_data["total_amount"]
            
            if vat_amount and total_amount:
                try:
                    vat = float(str(vat_amount).replace(",", "").replace("$", ""))
                    total = float(str(total_amount).replace(",", "").replace("$", ""))
                    
                    # Check if VAT is reasonable (0-30% of total)
                    vat_percentage = (vat / total) * 100 if total > 0 else 0
                    
                    if vat_percentage > 30:
                        issues.append(f"VAT amount seems too high: {vat_percentage:.1f}% of total")
                    elif vat_percentage < 0:
                        issues.append("VAT amount cannot be negative")
                        
                except (ValueError, TypeError):
                    pass
        
        return issues
