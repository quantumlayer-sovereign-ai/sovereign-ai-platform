"""
UK Security Generator - UK FinTech Security Training Data

Generates training samples for uk_fintech_security role focusing on:
- FCA security requirements (SYSC)
- UK GDPR security controls
- PSR fraud prevention
- Open Banking UK security
"""

from ..base import BaseGenerator, TrainingSample


class UKSecurityGenerator(BaseGenerator):
    """Generator for uk_fintech_security role"""

    def __init__(self):
        super().__init__()
        self.role_name = "uk_fintech_security"
        self.focus_areas = ["fca_security", "uk_gdpr_security", "psr_fraud_prevention"]
        self.compliance_tags = ["fca", "uk_gdpr", "psr"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate UK security training samples"""
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
            ("encryption", "UK GDPR"),
            ("breach", "UK GDPR/ICO"),
            ("fraud", "PSR"),
            ("cop", "PSR"),
            ("app_fraud", "PSR"),
            ("sysc", "FCA"),
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
                        compliance_tags=[standard.lower().replace(" ", "_").replace("/", "_")],
                        source_file=source_file
                    ))
                    break

        return samples

    def _generate_security_assessment_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security assessment samples"""
        samples = []
        sections = self.extract_sections(content)

        for section_name, section_content in sections.items():
            if any(kw in section_name for kw in ["security", "fraud", "control", "authentication"]):
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
        """Generate synthetic UK security samples"""
        samples = []

        # FCA SYSC security
        samples.append(self.create_sample(
            instruction="What are the FCA SYSC security requirements?",
            output="""FCA SYSC Security Requirements:

**SYSC 4.1 - General Requirements:**
- Robust governance arrangements
- Clear organizational structure
- Effective processes to identify, manage, monitor risk

**SYSC 7 - Risk Control:**
- Risk management framework
- Internal controls
- Compliance function
- Internal audit

**Information Security Requirements:**

1. **Access Control**
   - Role-based access control
   - Principle of least privilege
   - Regular access reviews
   - Privileged access management

2. **System Security**
   - Vulnerability management
   - Patch management
   - Secure configuration
   - Network security

3. **Data Protection**
   - Encryption of sensitive data
   - Secure data handling
   - Data classification
   - Retention and destruction

4. **Incident Management**
   - Incident detection
   - Response procedures
   - Escalation paths
   - Lessons learned

5. **Business Continuity**
   - BCP documentation
   - Regular testing
   - Recovery procedures
   - Third-party dependencies

**Outsourcing (SYSC 8):**
- Due diligence on providers
- Contractual requirements
- Ongoing monitoring
- Exit plans""",
            category="fca_security",
            compliance_tags=["fca"]
        ))

        # PSR fraud prevention
        samples.append(self.create_sample(
            instruction="What are the PSR fraud prevention security requirements?",
            output="""PSR Fraud Prevention Security Requirements:

**Confirmation of Payee (CoP):**

1. **Implementation Requirements**
   - Check payee name before payment
   - Return match/partial/no match result
   - Display clear warnings for mismatches
   - Allow user override with confirmation

2. **Security Considerations**
   - Secure API communication
   - Response authentication
   - Audit trail of checks
   - Rate limiting

**APP Fraud Detection:**

1. **Transaction Monitoring**
   - Real-time analysis
   - Behavioral analytics
   - Velocity checks
   - Amount pattern detection

2. **Risk Indicators**
   - New payee + high value
   - Changed device/location
   - Unusual timing
   - Social engineering patterns

3. **Warning Systems**
   - Effective scam warnings
   - Cooling-off periods
   - Additional authentication
   - Customer education

**Mule Account Detection:**

1. **Onboarding**
   - KYC verification
   - Sanctions screening
   - PEP checks

2. **Monitoring**
   - Transaction patterns
   - Account behavior
   - Rapid funds movement
   - Network analysis

**Reporting:**
- Fraud data to PSR
- Suspicious Activity Reports
- Internal MI
- Pattern sharing""",
            category="psr_fraud_prevention",
            compliance_tags=["psr"]
        ))

        # UK GDPR security assessment
        samples.append(self.create_sample(
            instruction="Conduct a UK GDPR security assessment checklist",
            output="""UK GDPR Security Assessment Checklist:

**1. Data Protection Measures**
- [ ] Personal data encrypted at rest (AES-256)
- [ ] Personal data encrypted in transit (TLS 1.2+)
- [ ] Pseudonymization implemented where appropriate
- [ ] Access controls based on role and need

**2. Access Control**
- [ ] Authentication mechanism in place (MFA recommended)
- [ ] Access rights reviewed regularly
- [ ] Privileged access monitored
- [ ] Access logs retained

**3. Data Minimization**
- [ ] Only necessary data collected
- [ ] Retention periods defined
- [ ] Automatic purging implemented
- [ ] Data deletion verified

**4. Breach Detection**
- [ ] Monitoring systems in place
- [ ] Anomaly detection active
- [ ] Incident response plan documented
- [ ] 72-hour notification capability

**5. Third-Party Security**
- [ ] Processor agreements in place
- [ ] Security requirements defined
- [ ] Regular assessments conducted
- [ ] Sub-processor controls

**6. International Transfers**
- [ ] Transfer mechanisms documented
- [ ] IDTA/UK Addendum where needed
- [ ] Transfer impact assessment completed
- [ ] Supplementary measures if required

**7. Documentation**
- [ ] ROPA maintained
- [ ] Privacy notices up to date
- [ ] DPIA where required
- [ ] Security policies documented

**8. Testing**
- [ ] Penetration testing annual
- [ ] Vulnerability scanning regular
- [ ] DR/BCP testing
- [ ] Security awareness training""",
            category="uk_gdpr_security",
            compliance_tags=["uk_gdpr"]
        ))

        return samples
