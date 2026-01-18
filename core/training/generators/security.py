"""
Security Generator - Vulnerability Detection Training Data

Generates training samples for the fintech_security role focusing on:
- PCI-DSS compliance scanning
- Vulnerability detection
- Security pattern recognition
"""

import re
from .base import BaseGenerator, TrainingSample


class SecurityGenerator(BaseGenerator):
    """Generator for fintech_security role"""

    def __init__(self):
        super().__init__()
        self.role_name = "fintech_security"
        self.focus_areas = ["vulnerability_detection", "pci_dss", "security_patterns"]
        self.compliance_tags = ["pci_dss", "rbi", "sebi"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security-focused training samples"""
        samples = []

        # Generate PCI-DSS requirement samples
        samples.extend(self._generate_pci_samples(content, source_file))

        # Generate vulnerability detection samples
        samples.extend(self._generate_vuln_detection_samples(content, source_file))

        # Generate security review samples
        samples.extend(self._generate_review_samples(content, source_file))

        # Generate synthetic vulnerability samples
        samples.extend(self.generate_vulnerability_samples())

        return samples

    def _generate_pci_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate PCI-DSS requirement samples"""
        samples = []
        requirements = self.extract_requirements(content)

        for req in requirements:
            req_id = req["id"]
            req_title = req["title"]
            req_content = " ".join(req["content"])

            if len(req_content) < 50:
                continue

            # Q&A style sample
            samples.append(self.create_sample(
                instruction=f"Explain PCI-DSS Requirement {req_id} and how to implement it",
                output=f"""## PCI-DSS Requirement {req_id}: {req_title}

{req_content}

### Implementation Checklist:
- Verify this requirement is addressed in the system
- Document compliance evidence
- Schedule periodic review
- Train relevant team members""",
                category="pci_dss_explanation",
                compliance_tags=[f"PCI-{req_id}"],
                source_file=source_file
            ))

            # Code review sample
            samples.append(self.create_sample(
                instruction=f"Review code for compliance with PCI-DSS Requirement {req_id}",
                input_text=f"Requirement: {req_title}",
                output=f"""## Security Review for PCI-DSS {req_id}

### Requirement Summary:
{req_content[:300]}

### Code Review Checklist:
1. Check for hardcoded credentials or secrets
2. Verify encryption is properly implemented
3. Ensure audit logging is in place
4. Validate input sanitization
5. Review access control mechanisms

### Common Violations:
- Missing encryption for sensitive data
- Insufficient logging
- Weak authentication
- Missing input validation

### Remediation Steps:
1. Implement required controls
2. Add automated security tests
3. Document compliance evidence
4. Schedule penetration testing""",
                category="pci_dss_review",
                compliance_tags=[f"PCI-{req_id}"],
                source_file=source_file
            ))

        return samples

    def _generate_vuln_detection_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate vulnerability detection samples from code examples"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        vuln_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*f['\"]",
                r"execute\s*\(\s*['\"].*?\%\s*",
                r"\.format\s*\(.*?\)\s*\)",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\s*\(",
                r"\.html\s*\([^)]*\$",
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
            ],
            "insecure_crypto": [
                r"MD5\s*\(",
                r"SHA1\s*\(",
                r"DES\s*\(",
            ],
        }

        for block in code_blocks:
            code = block["code"]

            # Check for vulnerability patterns (to demonstrate detection)
            for vuln_type, patterns in vuln_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        samples.append(self.create_sample(
                            instruction=f"Identify security vulnerabilities in this code, focusing on {vuln_type.replace('_', ' ')}",
                            input_text=code,
                            output=self._generate_vuln_report(vuln_type, code),
                            category="vulnerability_detection",
                            source_file=source_file
                        ))
                        break

        return samples

    def _generate_review_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security review samples"""
        samples = []
        sections = self.extract_sections(content)

        security_sections = [
            name for name in sections
            if any(kw in name for kw in ["security", "protect", "encrypt", "auth", "access"])
        ]

        for section_name in security_sections:
            section_content = sections[section_name]
            code_blocks = self.extract_code_blocks(section_content)

            for block in code_blocks:
                if block["language"] == "python":
                    samples.append(self.create_sample(
                        instruction="Perform a security review of this FinTech code",
                        input_text=block["code"],
                        output=self._generate_security_review(block["code"]),
                        category="security_review",
                        source_file=source_file
                    ))

        return samples

    def _generate_vuln_report(self, vuln_type: str, code: str) -> str:
        """Generate vulnerability report"""
        vuln_details = {
            "sql_injection": {
                "severity": "Critical",
                "pci": "PCI-DSS 6.5.1",
                "description": "SQL Injection vulnerability allows attackers to manipulate database queries",
                "fix": "Use parameterized queries or prepared statements"
            },
            "xss": {
                "severity": "High",
                "pci": "PCI-DSS 6.5.7",
                "description": "Cross-Site Scripting allows injection of malicious scripts",
                "fix": "Sanitize and escape all user input before rendering"
            },
            "hardcoded_secrets": {
                "severity": "Critical",
                "pci": "PCI-DSS 2.1, 6.5.3",
                "description": "Hardcoded credentials expose secrets in source code",
                "fix": "Use environment variables or secure secret management"
            },
            "insecure_crypto": {
                "severity": "High",
                "pci": "PCI-DSS 3.4, 4.1",
                "description": "Weak cryptographic algorithms provide insufficient protection",
                "fix": "Use AES-256 for encryption, SHA-256 or better for hashing"
            }
        }

        details = vuln_details.get(vuln_type, {
            "severity": "Medium",
            "pci": "PCI-DSS 6.5",
            "description": "Security vulnerability detected",
            "fix": "Review and apply security best practices"
        })

        return f"""## Security Vulnerability Report

### Vulnerability Type: {vuln_type.replace('_', ' ').title()}

**Severity:** {details['severity']}
**Compliance:** {details['pci']}

### Description:
{details['description']}

### Affected Code:
```python
{code[:500]}
```

### Remediation:
{details['fix']}

### Action Items:
1. Fix the vulnerability immediately
2. Review similar code patterns in the codebase
3. Add security tests to prevent regression
4. Update security documentation
5. Notify the security team for review"""

    def _generate_security_review(self, code: str) -> str:
        """Generate comprehensive security review"""
        return f"""## Security Code Review

### Code Under Review:
```python
{code[:800]}
```

### Security Assessment:

#### 1. Authentication & Authorization
- [ ] Verify proper authentication mechanisms
- [ ] Check role-based access control implementation
- [ ] Validate session management

#### 2. Data Protection
- [ ] Sensitive data is encrypted at rest
- [ ] TLS used for data in transit
- [ ] PII properly masked in logs

#### 3. Input Validation
- [ ] All inputs validated and sanitized
- [ ] Parameterized queries used
- [ ] Output properly encoded

#### 4. Error Handling
- [ ] Errors logged without sensitive data
- [ ] Generic error messages to users
- [ ] No stack traces exposed

#### 5. PCI-DSS Compliance
- [ ] Card data handling per Requirement 3
- [ ] Transmission security per Requirement 4
- [ ] Access control per Requirement 7

### Recommendations:
1. Review for hardcoded credentials
2. Implement comprehensive audit logging
3. Add input validation on all entry points
4. Ensure proper error handling
5. Schedule penetration testing"""

    def generate_vulnerability_samples(self) -> list[TrainingSample]:
        """Generate synthetic vulnerability detection samples"""
        samples = []

        # SQL Injection detection
        samples.append(self.create_sample(
            instruction="Identify the security vulnerability in this code and provide the fix",
            input_text='''def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)''',
            output='''## Vulnerability: SQL Injection

**Severity:** Critical
**CWE:** CWE-89
**PCI-DSS:** Requirement 6.5.1

### Issue:
The code uses f-string formatting to construct SQL queries, making it vulnerable to SQL injection attacks.

### Vulnerable Code:
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
```

### Attack Example:
If `user_id = "1 OR 1=1"`, the query becomes:
```sql
SELECT * FROM users WHERE id = 1 OR 1=1
```
This returns all users, bypassing authentication.

### Fixed Code:
```python
def get_user(user_id: int):
    """Safely query user by ID using parameterized query"""
    query = "SELECT * FROM users WHERE id = %s"
    return db.execute(query, (user_id,))
```

### Additional Recommendations:
1. Use an ORM (SQLAlchemy, Django ORM)
2. Implement input validation
3. Apply principle of least privilege to database users
4. Enable query logging for monitoring''',
            category="vuln_detection",
            compliance_tags=["PCI-6.5.1"]
        ))

        # Sensitive data exposure
        samples.append(self.create_sample(
            instruction="Review this logging code for PCI-DSS compliance issues",
            input_text='''def log_payment(card_number, amount, customer_name):
    logger.info(f"Processing payment: card={card_number}, amount={amount}, customer={customer_name}")
    # Process payment...''',
            output='''## Vulnerability: Sensitive Data Exposure in Logs

**Severity:** Critical
**CWE:** CWE-532
**PCI-DSS:** Requirement 3.4, 10.3

### Issue:
Full card number (PAN) is being logged, violating PCI-DSS Requirement 3.4 which requires cardholder data to be rendered unreadable.

### Violations:
1. **PCI-DSS 3.4:** PAN must be masked or encrypted when stored
2. **PCI-DSS 3.3:** PAN display must show only first 6 and last 4 digits
3. **PCI-DSS 10.3:** Logs must not contain sensitive authentication data

### Fixed Code:
```python
def mask_card(card_number: str) -> str:
    """Mask card number showing only first 6 and last 4 digits"""
    if len(card_number) < 13:
        return "****"
    return f"{card_number[:6]}******{card_number[-4:]}"

def log_payment(card_number: str, amount: Decimal, customer_id: str):
    """Log payment with masked sensitive data"""
    logger.info(
        "payment_processing",
        card_masked=mask_card(card_number),
        amount=str(amount),
        customer_id=customer_id  # Use ID, not name
    )
    # Process payment...
```

### Recommendations:
1. Never log full PAN, CVV, or PIN
2. Use customer ID instead of name in logs
3. Implement centralized logging with automatic PII masking
4. Review all existing logs for sensitive data exposure''',
            category="vuln_detection",
            compliance_tags=["PCI-3.3", "PCI-3.4", "PCI-10.3"]
        ))

        # Weak cryptography
        samples.append(self.create_sample(
            instruction="Assess the cryptographic security of this code",
            input_text='''import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def encrypt_data(data, key):
    from Crypto.Cipher import DES
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)''',
            output='''## Vulnerability: Weak Cryptography

**Severity:** High
**CWE:** CWE-327, CWE-328
**PCI-DSS:** Requirement 3.4, 4.1

### Issues Found:

#### 1. MD5 for Password Hashing
- MD5 is cryptographically broken
- Vulnerable to rainbow table attacks
- No salt used

#### 2. DES Encryption
- DES uses only 56-bit keys (insecure)
- ECB mode reveals patterns in data
- PCI-DSS requires AES-256 minimum

### Fixed Code:
```python
import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets

def hash_password(password: str) -> bytes:
    """Hash password using bcrypt with salt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(password: str, hash: bytes) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hash)

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES-256-GCM"""
    if len(key) != 32:  # 256 bits
        raise ValueError("Key must be 32 bytes for AES-256")

    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext

def decrypt_data(encrypted: bytes, key: bytes) -> bytes:
    """Decrypt AES-256-GCM encrypted data"""
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
```

### PCI-DSS Compliance:
- Use AES-256 or stronger for encryption
- Use bcrypt, scrypt, or Argon2 for passwords
- Implement proper key management
- Never use ECB mode''',
            category="crypto_review",
            compliance_tags=["PCI-3.4", "PCI-4.1"]
        ))

        return samples
