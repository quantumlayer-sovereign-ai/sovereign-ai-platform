"""
EU Security Generator - EU FinTech Security Training Data

Generates training samples for eu_fintech_security role focusing on:
- GDPR security requirements (Article 32)
- PSD2 security
- DORA resilience
- eIDAS certificate security
"""

from ..base import BaseGenerator, TrainingSample


class EUSecurityGenerator(BaseGenerator):
    """Generator for eu_fintech_security role"""

    def __init__(self):
        super().__init__()
        self.role_name = "eu_fintech_security"
        self.focus_areas = ["gdpr_security", "psd2_security", "dora_compliance"]
        self.compliance_tags = ["gdpr", "psd2", "dora"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate EU security training samples"""
        samples = []

        # Security-focused code samples
        samples.extend(self._generate_security_code_samples(content, source_file))

        # Security assessment samples
        samples.extend(self._generate_security_assessment_samples(content, source_file))

        return samples

    def _generate_security_code_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security code pattern samples"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        security_patterns = [
            ("encryption", "GDPR Article 32"),
            ("pseudonymiz", "GDPR Article 32"),
            ("breach", "GDPR Article 33"),
            ("sca", "PSD2"),
            ("qwac", "eIDAS"),
            ("incident", "DORA"),
        ]

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code_lower = block["code"].lower()

            for pattern, standard in security_patterns:
                if pattern in code_lower:
                    samples.append(self.create_sample(
                        instruction=f"Write secure Python code for {pattern.replace('_', ' ')} handling",
                        input_text=f"Ensure compliance with {standard}",
                        output=block["code"],
                        category="security_code",
                        compliance_tags=[standard.lower().replace(" ", "_")],
                        source_file=source_file
                    ))
                    break

        return samples

    def _generate_security_assessment_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security assessment samples"""
        samples = []
        sections = self.extract_sections(content)

        for section_name, section_content in sections.items():
            if any(kw in section_name for kw in ["security", "encryption", "access", "authentication"]):
                requirements = self.extract_bullet_points(section_content)
                if requirements:
                    samples.append(self.create_sample(
                        instruction=f"Perform security assessment for {section_name.replace('_', ' ')}",
                        output="\n".join(f"- Check: {req}" for req in requirements[:8]),
                        category="security_assessment",
                        source_file=source_file
                    ))

        return samples

    def generate_synthetic_samples(self) -> list[TrainingSample]:
        """Generate synthetic EU security samples"""
        samples = []

        # GDPR Article 32 security
        samples.append(self.create_sample(
            instruction="What security measures are required under GDPR Article 32?",
            output="""GDPR Article 32 - Security of Processing requires appropriate technical and organizational measures:

**Technical Measures:**
1. **Encryption**
   - Data at rest: AES-256 or equivalent
   - Data in transit: TLS 1.2+ mandatory
   - Key management procedures

2. **Pseudonymization**
   - Separate storage of identifiers
   - Tokenization of sensitive data
   - Cannot be attributed without additional information

3. **Access Controls**
   - Role-based access control (RBAC)
   - Multi-factor authentication
   - Principle of least privilege

4. **Resilience**
   - Backup and recovery procedures
   - Redundancy for critical systems
   - Disaster recovery planning

**Organizational Measures:**
1. Security policies and procedures
2. Staff training and awareness
3. Regular security testing (penetration testing, vulnerability scans)
4. Incident response procedures
5. Third-party security assessment

**Ongoing Requirements:**
- Regular testing and evaluation
- Risk-based approach to security
- Documentation of security measures""",
            category="gdpr_security",
            compliance_tags=["gdpr"]
        ))

        # PSD2 security assessment
        samples.append(self.create_sample(
            instruction="Conduct a PSD2 SCA security assessment checklist",
            output="""PSD2 Strong Customer Authentication Security Assessment:

**1. Authentication Factor Security**
- [ ] Knowledge factor stored with strong hashing (bcrypt/Argon2)
- [ ] Possession factor uses secure channel (push notification/SMS)
- [ ] Inherence factor uses certified biometric (FIDO2/WebAuthn)
- [ ] Factors are truly independent (different channels)

**2. Dynamic Linking Verification**
- [ ] Auth code cryptographically bound to amount
- [ ] Auth code cryptographically bound to payee
- [ ] Code invalidated if amount/payee changes
- [ ] One-time use enforced

**3. Session Security**
- [ ] Session timeout after 5 minutes inactivity
- [ ] Secure session tokens (random, sufficient entropy)
- [ ] Session bound to device/browser
- [ ] Re-authentication for sensitive operations

**4. Communication Security**
- [ ] TLS 1.2+ for all API calls
- [ ] Certificate pinning for mobile apps
- [ ] QWAC validation for TPP access
- [ ] No sensitive data in URLs

**5. Exemption Controls**
- [ ] Transaction Risk Analysis documented
- [ ] Fraud rate monitoring in place
- [ ] Exemption audit trail
- [ ] Cumulative limits enforced (low value)

**6. Incident Response**
- [ ] SCA bypass detection
- [ ] Authentication failure monitoring
- [ ] Fraud detection integration
- [ ] Incident reporting procedures""",
            category="psd2_security",
            compliance_tags=["psd2"]
        ))

        # DORA security
        samples.append(self.create_sample(
            instruction="What are the DORA incident detection requirements?",
            output="""DORA Incident Detection Requirements (Articles 17-23):

**Detection Mechanisms:**
1. Real-time monitoring of ICT systems
2. Anomaly detection for unusual patterns
3. Security Information and Event Management (SIEM)
4. Intrusion detection systems
5. Log analysis and correlation

**Classification Criteria (Major Incident):**
- Affects >10% of clients
- Service downtime >2 hours
- Economic impact >€100,000
- Data integrity compromised
- Cross-border impact

**Incident Response:**
1. **Immediate Actions**
   - Contain the incident
   - Assess scope and impact
   - Activate response team

2. **Communication**
   - Internal escalation
   - Authority notification (if major)
   - Customer communication (if needed)

3. **Documentation**
   - Incident timeline
   - Actions taken
   - Root cause analysis
   - Lessons learned

**Reporting Timeline:**
- Initial notification: Within 4 hours of classification
- Intermediate report: Within 72 hours
- Final report: Within 1 month of resolution""",
            category="dora_compliance",
            compliance_tags=["dora"]
        ))

        return samples
