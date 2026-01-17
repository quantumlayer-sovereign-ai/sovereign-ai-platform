# PCI-DSS v4.0 Key Requirements Summary

## Overview

The Payment Card Industry Data Security Standard (PCI DSS) is a set of security standards designed to ensure that all companies that accept, process, store, or transmit credit card information maintain a secure environment.

## Requirement 1: Install and Maintain Network Security Controls

### 1.1 Network Security Controls
- Define and implement firewall configurations
- Document network topology and data flows
- Restrict connections between untrusted networks and cardholder data environment (CDE)

### 1.2 Network Configuration Standards
- Deny all traffic by default
- Allow only necessary services and ports
- Review firewall rules every six months

### Implementation Guidelines for Developers
```python
# Example: Secure network configuration check
def validate_network_config(config):
    required_settings = [
        'deny_by_default',
        'allow_list_only',
        'logging_enabled'
    ]
    for setting in required_settings:
        if not config.get(setting):
            raise SecurityViolation(f"PCI 1.x: {setting} not configured")
```

## Requirement 2: Apply Secure Configurations to All System Components

### 2.1 Vendor Defaults
- Never use vendor-supplied default passwords
- Remove unnecessary default accounts
- Change default cryptographic keys

### 2.2 System Hardening
- Enable only necessary services
- Remove or disable unnecessary functionality
- Implement additional security for services that are inherently insecure

### Code Example: Configuration Validation
```python
BANNED_DEFAULT_PASSWORDS = ['admin', 'password', '123456', 'default']

def check_password_policy(password):
    if password.lower() in BANNED_DEFAULT_PASSWORDS:
        raise SecurityViolation("PCI 2.1: Default password detected")
    if len(password) < 12:
        raise SecurityViolation("PCI 2.1: Password too short (min 12 chars)")
```

## Requirement 3: Protect Stored Account Data

### 3.1 Data Storage Limitations
- Store cardholder data only if necessary
- Limit storage time to business requirements
- Securely delete data when no longer needed

### 3.2 Sensitive Authentication Data (SAD)
- Never store full track data after authorization
- Never store CVV/CVC after authorization
- Never store PIN or encrypted PIN block after authorization

### 3.3 Display Masking
- Mask PAN when displayed (show only first 6 and last 4 digits)
- Full PAN only for those with business need

### 3.4 Encryption at Rest
- Use strong cryptography to render PAN unreadable
- Minimum AES-256 or equivalent
- Secure key management procedures

### Implementation Example
```python
import hashlib
from cryptography.fernet import Fernet

class CardDataHandler:
    def __init__(self, encryption_key):
        self.cipher = Fernet(encryption_key)

    def mask_pan(self, pan: str) -> str:
        """PCI 3.3: Mask PAN for display"""
        if len(pan) < 13:
            raise ValueError("Invalid PAN length")
        return f"{pan[:6]}******{pan[-4:]}"

    def encrypt_pan(self, pan: str) -> bytes:
        """PCI 3.4: Encrypt PAN for storage"""
        return self.cipher.encrypt(pan.encode())

    def hash_pan(self, pan: str) -> str:
        """One-way hash for indexing (with salt)"""
        salt = os.urandom(32)
        return hashlib.pbkdf2_hmac('sha256', pan.encode(), salt, 100000).hex()
```

## Requirement 4: Protect Cardholder Data During Transmission

### 4.1 Strong Cryptography During Transmission
- Use TLS 1.2 or higher for all transmissions
- Never send PAN via end-user messaging (email, SMS)
- Secure all wireless networks transmitting cardholder data

### 4.2 Certificate Management
- Use trusted certificates
- Verify certificate validity before transmission
- Reject connections with invalid certificates

### Implementation Example
```python
import ssl
import requests

def secure_api_call(url, data):
    """PCI 4.1: Secure transmission with TLS 1.2+"""
    session = requests.Session()
    session.verify = True  # Verify SSL certificates

    # Enforce minimum TLS version
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
    )
    session.mount('https://', adapter)

    # Never use HTTP for cardholder data
    if not url.startswith('https://'):
        raise SecurityViolation("PCI 4.1: HTTPS required for cardholder data")

    return session.post(url, json=data)
```

## Requirement 5: Protect All Systems Against Malware

### 5.1 Anti-Malware Solutions
- Deploy anti-malware on all systems commonly affected
- Keep anti-malware solutions current
- Enable automatic updates

### 5.2 Code Security
- Scan code for malware indicators
- Validate file uploads and inputs
- Monitor for suspicious behavior

## Requirement 6: Develop and Maintain Secure Systems and Software

### 6.1 Secure Development Lifecycle
- Train developers on secure coding
- Review custom code before release
- Address vulnerabilities during development

### 6.2 Common Vulnerabilities
- SQL Injection prevention
- XSS prevention
- CSRF protection
- Input validation
- Output encoding

### 6.3 Secure Coding Practices
```python
# SQL Injection Prevention
def safe_query(user_id):
    # NEVER do this:
    # cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

    # Always use parameterized queries:
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# XSS Prevention
from markupsafe import escape

def display_user_input(user_data):
    return escape(user_data)

# Input Validation
import re

def validate_card_number(card_number):
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s-]', '', card_number)

    # Validate format
    if not re.match(r'^\d{13,19}$', cleaned):
        raise ValueError("Invalid card number format")

    # Luhn algorithm check
    if not luhn_check(cleaned):
        raise ValueError("Invalid card number checksum")

    return cleaned
```

### 6.4 Change Control
- Document all changes
- Test security impact of changes
- Separate development and production environments

## Requirement 7: Restrict Access to System Components

### 7.1 Need-to-Know Principle
- Limit access to cardholder data to only those who need it
- Implement role-based access control (RBAC)
- Document access rights

### Implementation Example
```python
from enum import Enum
from functools import wraps

class Role(Enum):
    CUSTOMER_SERVICE = "customer_service"
    PAYMENT_PROCESSOR = "payment_processor"
    ADMIN = "admin"
    AUDITOR = "auditor"

ROLE_PERMISSIONS = {
    Role.CUSTOMER_SERVICE: ["view_masked_pan", "view_transaction_history"],
    Role.PAYMENT_PROCESSOR: ["process_payment", "view_full_pan", "refund"],
    Role.ADMIN: ["all"],
    Role.AUDITOR: ["view_logs", "view_masked_pan", "generate_reports"]
}

def requires_permission(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            user_perms = ROLE_PERMISSIONS.get(user.role, [])
            if permission not in user_perms and "all" not in user_perms:
                raise PermissionDenied(f"PCI 7.1: Access denied for {permission}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator
```

## Requirement 8: Identify Users and Authenticate Access

### 8.1 User Identification
- Unique ID for each user
- No shared or group accounts
- Remove inactive accounts

### 8.2 Strong Authentication
- Multi-factor authentication for all access to CDE
- Password complexity requirements (12+ characters)
- Password history (last 4 passwords)
- Account lockout after 10 failed attempts

### 8.3 Session Management
```python
import secrets
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_timeout = timedelta(minutes=15)  # PCI 8.1.8

    def create_session(self, user_id):
        """PCI 8.3: Create secure session"""
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        return token

    def validate_session(self, token):
        """Check session validity and timeout"""
        session = self.sessions.get(token)
        if not session:
            raise SessionExpired("Invalid session")

        if datetime.now() - session['last_activity'] > self.session_timeout:
            del self.sessions[token]
            raise SessionExpired("PCI 8.1.8: Session timed out")

        session['last_activity'] = datetime.now()
        return session['user_id']
```

## Requirement 9: Restrict Physical Access to Cardholder Data

### 9.1 Physical Security
- Control access to data centers
- Visitor management procedures
- Media destruction procedures

## Requirement 10: Log and Monitor All Access

### 10.1 Audit Trail
- Log all access to cardholder data
- Log all actions by privileged users
- Secure audit trails from modification

### 10.2 Logging Requirements
```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

class AuditLogger:
    @staticmethod
    def log_data_access(user_id, action, resource, success=True):
        """PCI 10.1: Log all access to cardholder data"""
        logger.info(
            "cardholder_data_access",
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            timestamp=datetime.utcnow().isoformat(),
            source_ip=get_client_ip()
        )

    @staticmethod
    def log_auth_event(user_id, event_type, success=True):
        """PCI 10.2: Log authentication events"""
        logger.info(
            "auth_event",
            user_id=user_id,
            event_type=event_type,
            success=success,
            timestamp=datetime.utcnow().isoformat()
        )
```

### 10.3 Time Synchronization
- Synchronize clocks using NTP
- Ensure consistent timestamps across systems
- Log timezone information

## Requirement 11: Test Security Systems and Processes

### 11.1 Vulnerability Scanning
- Quarterly external vulnerability scans
- Internal scans after significant changes
- Address critical vulnerabilities within 30 days

### 11.2 Penetration Testing
- Annual penetration testing
- Test both application and network layers
- Remediate findings and re-test

### 11.3 Change Detection
- Monitor critical files for changes
- Alert on unauthorized modifications

## Requirement 12: Support Information Security with Policies

### 12.1 Security Policy
- Document information security policy
- Annual review and updates
- Employee acknowledgment

### 12.2 Risk Assessment
- Annual formal risk assessment
- Identify threats and vulnerabilities
- Implement risk mitigation measures

### 12.3 Incident Response
- Documented incident response plan
- Annual testing of response procedures
- Designated response team
