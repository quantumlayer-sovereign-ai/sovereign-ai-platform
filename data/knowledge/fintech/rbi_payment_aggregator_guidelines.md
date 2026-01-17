# RBI Payment Aggregator Guidelines Summary

## Overview

The Reserve Bank of India (RBI) issued guidelines for Payment Aggregators (PAs) and Payment Gateways (PGs) to regulate entities facilitating e-commerce transactions. These guidelines ensure security, consumer protection, and financial system stability.

## Authorization Requirements

### Eligibility Criteria
- Minimum net worth of ₹15 crore at the time of application
- Net worth of ₹25 crore by March 31, 2023
- Only companies incorporated in India under Companies Act
- Payment Aggregators handling funds must be authorized by RBI

### Application Process
1. Submit application to RBI with required documents
2. Demonstrate technology capabilities
3. Show compliance infrastructure
4. Provide audited financial statements
5. Submit background verification of directors

## Capital Requirements

### Net Worth Requirements
```python
from datetime import date

class NetWorthCompliance:
    REQUIREMENTS = {
        'initial': 15_00_00_000,    # ₹15 crore at application
        'march_2023': 25_00_00_000,  # ₹25 crore by March 2023
    }

    def check_compliance(self, current_net_worth: int, check_date: date):
        if check_date < date(2023, 3, 31):
            required = self.REQUIREMENTS['initial']
        else:
            required = self.REQUIREMENTS['march_2023']

        if current_net_worth < required:
            raise RegulatoryViolation(
                f"Net worth ₹{current_net_worth/1e7:.2f} Cr below "
                f"required ₹{required/1e7:.2f} Cr"
            )
```

## Escrow Account Requirements

### Mandatory Escrow
- All PAs must maintain escrow account with scheduled commercial bank
- Merchant payments must be processed through escrow
- Settlement to merchants within T+1 business day
- No co-mingling of funds

### Escrow Management
```python
from decimal import Decimal
from datetime import datetime, timedelta

class EscrowManager:
    def __init__(self, escrow_account_id):
        self.escrow_account_id = escrow_account_id
        self.balance = Decimal('0')
        self.pending_settlements = []

    def credit_from_customer(self, transaction_id: str, amount: Decimal):
        """Credit customer payment to escrow"""
        self.balance += amount
        self.pending_settlements.append({
            'transaction_id': transaction_id,
            'amount': amount,
            'credited_at': datetime.now(),
            'settlement_due': datetime.now() + timedelta(days=1)  # T+1
        })
        return True

    def settle_to_merchant(self, merchant_id: str, amount: Decimal):
        """Settle funds to merchant - must be within T+1"""
        if amount > self.balance:
            raise InsufficientFunds("Escrow balance insufficient")

        self.balance -= amount
        return {
            'status': 'settled',
            'merchant_id': merchant_id,
            'amount': amount,
            'timestamp': datetime.now()
        }

    def check_settlement_compliance(self):
        """Check for any overdue settlements"""
        overdue = []
        for settlement in self.pending_settlements:
            if datetime.now() > settlement['settlement_due']:
                overdue.append(settlement)

        if overdue:
            raise RegulatoryViolation(
                f"RBI T+1 Violation: {len(overdue)} settlements overdue"
            )
```

## KYC Requirements

### Merchant Onboarding
- Verify legal entity status
- Obtain KYC documents (PAN, GST, Bank details)
- Background verification
- Website/app review for prohibited items
- Board resolution for authorized signatories

### Customer Verification
- For transactions above threshold, customer verification required
- Link to verified bank accounts
- OTP-based verification for sensitive operations

### KYC Implementation
```python
from enum import Enum
from dataclasses import dataclass

class KYCStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class MerchantKYC:
    merchant_id: str
    business_name: str
    pan_number: str
    gst_number: str
    bank_account: str
    ifsc_code: str
    status: KYCStatus = KYCStatus.PENDING
    verified_at: datetime = None

    def validate_pan(self):
        """Validate PAN format"""
        import re
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', self.pan_number):
            raise ValidationError("Invalid PAN format")

    def validate_gst(self):
        """Validate GST format"""
        import re
        if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9]{1}Z[0-9A-Z]{1}$',
                       self.gst_number):
            raise ValidationError("Invalid GST format")

    def validate_bank_account(self):
        """Validate bank account with IFSC"""
        # Call bank verification API
        pass

    def complete_kyc(self):
        self.validate_pan()
        self.validate_gst()
        self.validate_bank_account()
        self.status = KYCStatus.VERIFIED
        self.verified_at = datetime.now()
```

## Data Security Requirements

### Card Data Handling
- PAs must not store actual card data
- Use tokenization for recurring payments
- Comply with PCI-DSS standards
- Implement data localization (store data in India)

### Data Localization
```python
class DataLocalizationChecker:
    """Ensure all payment data is stored in India"""

    INDIAN_REGIONS = ['ap-south-1', 'ap-south-2']  # AWS regions

    def validate_storage_location(self, storage_config):
        region = storage_config.get('region')
        if region not in self.INDIAN_REGIONS:
            raise RegulatoryViolation(
                f"RBI Data Localization: Data must be stored in India. "
                f"Current region: {region}"
            )

    def validate_database_connection(self, db_host):
        """Check database is hosted in India"""
        # Resolve IP and check geolocation
        pass
```

### Security Standards
```python
class SecurityStandards:
    REQUIRED_STANDARDS = [
        'PCI-DSS',
        'PA-DSS',  # For payment applications
        'ISO-27001'
    ]

    def __init__(self):
        self.certifications = {}

    def add_certification(self, standard: str, expiry: date, certificate_id: str):
        self.certifications[standard] = {
            'expiry': expiry,
            'certificate_id': certificate_id,
            'valid': expiry > date.today()
        }

    def check_compliance(self):
        missing = []
        expired = []

        for standard in self.REQUIRED_STANDARDS:
            if standard not in self.certifications:
                missing.append(standard)
            elif not self.certifications[standard]['valid']:
                expired.append(standard)

        if missing or expired:
            raise RegulatoryViolation(
                f"Missing certifications: {missing}, "
                f"Expired certifications: {expired}"
            )
```

## Transaction Monitoring

### Mandatory Reporting
- Report suspicious transactions to FIU-IND
- Maintain transaction records for 10 years
- Real-time fraud monitoring

### Transaction Limits
```python
class TransactionLimits:
    """RBI mandated transaction limits"""

    LIMITS = {
        'wallet_monthly': 1_00_000,      # ₹1 lakh per month for wallets
        'wallet_balance': 2_00_000,       # ₹2 lakh max balance
        'upi_per_transaction': 1_00_000,  # ₹1 lakh per UPI transaction
        'card_without_otp': 5_000,        # ₹5000 for contactless without OTP
    }

    def check_transaction(self, payment_method: str, amount: int,
                         monthly_total: int = 0, current_balance: int = 0):

        if payment_method == 'wallet':
            if monthly_total + amount > self.LIMITS['wallet_monthly']:
                raise TransactionBlocked(
                    f"RBI: Monthly wallet limit exceeded"
                )
            if current_balance + amount > self.LIMITS['wallet_balance']:
                raise TransactionBlocked(
                    f"RBI: Wallet balance limit exceeded"
                )

        if payment_method == 'upi':
            if amount > self.LIMITS['upi_per_transaction']:
                raise TransactionBlocked(
                    f"RBI: UPI transaction limit ₹1 lakh exceeded"
                )

        return True
```

## Grievance Redressal

### Customer Support Requirements
- Dedicated customer support helpline
- Complaint resolution within 30 days
- Escalation matrix
- Nodal officer appointment

### Implementation
```python
from datetime import datetime, timedelta
from enum import Enum

class ComplaintStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"

class GrievanceHandler:
    RESOLUTION_SLA = timedelta(days=30)
    ESCALATION_LEVELS = ['L1', 'L2', 'NODAL_OFFICER', 'RBI_OMBUDSMAN']

    def __init__(self):
        self.complaints = {}

    def register_complaint(self, customer_id: str, description: str):
        complaint_id = generate_complaint_id()
        self.complaints[complaint_id] = {
            'customer_id': customer_id,
            'description': description,
            'status': ComplaintStatus.OPEN,
            'created_at': datetime.now(),
            'sla_deadline': datetime.now() + self.RESOLUTION_SLA,
            'escalation_level': 'L1'
        }
        return complaint_id

    def check_sla_breach(self, complaint_id: str):
        complaint = self.complaints.get(complaint_id)
        if complaint and datetime.now() > complaint['sla_deadline']:
            if complaint['status'] not in [ComplaintStatus.RESOLVED,
                                           ComplaintStatus.CLOSED]:
                # Auto-escalate
                self.escalate(complaint_id)
                raise SLABreach(
                    f"RBI: 30-day SLA breached for complaint {complaint_id}"
                )
```

## Audit and Reporting

### Annual Audit Requirements
- System audit by CERT-IN empaneled auditor
- PCI-DSS audit
- Compliance certificate to RBI

### Reporting to RBI
```python
class RBIReporting:
    """Generate mandatory reports for RBI"""

    def generate_quarterly_report(self, quarter: str, year: int):
        return {
            'period': f"{quarter} {year}",
            'total_transactions': self.get_transaction_count(quarter, year),
            'total_value': self.get_transaction_value(quarter, year),
            'merchant_count': self.get_active_merchants(),
            'complaints_received': self.get_complaints_count(quarter, year),
            'complaints_resolved': self.get_resolved_complaints(quarter, year),
            'fraud_cases': self.get_fraud_cases(quarter, year),
            'refunds_processed': self.get_refunds(quarter, year)
        }

    def generate_annual_compliance_report(self, year: int):
        return {
            'year': year,
            'net_worth': self.get_audited_net_worth(year),
            'pci_dss_status': self.get_pci_compliance(),
            'system_audit': self.get_system_audit_report(),
            'data_localization_compliance': True,
            'escrow_reconciliation': self.get_escrow_audit(),
            'kyc_compliance_rate': self.get_kyc_stats()
        }
```

## Prohibited Activities

### Restricted Business Categories
- Gambling/betting websites
- Cryptocurrency exchanges (specific restrictions)
- Adult content
- Weapons and ammunition
- Illegal pharmaceuticals

### Merchant Screening
```python
PROHIBITED_MCCS = [
    7995,  # Gambling
    5816,  # Digital goods - games
    6051,  # Cryptocurrency
]

RESTRICTED_KEYWORDS = [
    'casino', 'betting', 'gambling', 'crypto', 'bitcoin'
]

def screen_merchant(merchant_data):
    """Screen merchant for prohibited activities"""

    if merchant_data.get('mcc') in PROHIBITED_MCCS:
        raise MerchantRejected(
            f"RBI: Prohibited MCC {merchant_data['mcc']}"
        )

    website = merchant_data.get('website', '').lower()
    business_name = merchant_data.get('name', '').lower()

    for keyword in RESTRICTED_KEYWORDS:
        if keyword in website or keyword in business_name:
            raise MerchantReviewRequired(
                f"RBI: Restricted keyword '{keyword}' detected"
            )
```

## Recent Updates (2024)

### Tokenization Mandate
- All card-on-file transactions must use tokens
- No merchant can store actual card numbers
- Token requestor must be registered with card networks

### Account Aggregator Framework
- Consent-based data sharing
- Integration with AA ecosystem for credit assessment
- Financial Information Providers (FIP) registration

### UPI Changes
- UPI Lite for small value transactions
- UPI 123 for feature phones
- Credit line on UPI
