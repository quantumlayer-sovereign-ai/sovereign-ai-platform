"""
UK Compliance Generator - UK Regulatory Compliance Training Data

Generates training samples for uk_fintech_compliance role focusing on:
- FCA Handbook requirements
- Consumer Duty
- UK GDPR
- PSR regulations
"""

from ..base import BaseGenerator, TrainingSample


class UKComplianceGenerator(BaseGenerator):
    """Generator for uk_fintech_compliance role"""

    def __init__(self):
        super().__init__()
        self.role_name = "uk_fintech_compliance"
        self.focus_areas = ["fca_handbook", "consumer_duty", "uk_gdpr", "psr_requirements"]
        self.compliance_tags = ["fca", "uk_gdpr", "psr"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate UK compliance training samples"""
        samples = []

        sections = self.extract_sections(content)

        for section_name, section_content in sections.items():
            # FCA-related sections
            if any(kw in section_name for kw in ["fca", "prin", "sysc", "cobs", "consumer_duty"]):
                samples.extend(self._generate_fca_qa(section_name, section_content, source_file))

            # PSR-related sections
            if any(kw in section_name for kw in ["psr", "app_fraud", "cop", "payment_system"]):
                samples.extend(self._generate_psr_qa(section_name, section_content, source_file))

            # UK GDPR sections
            if any(kw in section_name for kw in ["uk_gdpr", "ico", "data_protection"]):
                samples.extend(self._generate_ukgdpr_qa(section_name, section_content, source_file))

        return samples

    def _generate_fca_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate FCA Q&A samples"""
        samples = []

        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"What are the FCA requirements for {section_name.replace('_', ' ')}?",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="fca_handbook",
                compliance_tags=["fca"],
                source_file=source_file
            ))

        return samples

    def _generate_psr_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate PSR Q&A samples"""
        samples = []

        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"Explain the PSR requirements for {section_name.replace('_', ' ')}",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="psr_requirements",
                compliance_tags=["psr"],
                source_file=source_file
            ))

        return samples

    def _generate_ukgdpr_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate UK GDPR Q&A samples"""
        samples = []

        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"What are the UK GDPR requirements for {section_name.replace('_', ' ')}?",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="uk_gdpr",
                compliance_tags=["uk_gdpr"],
                source_file=source_file
            ))

        return samples

    def generate_synthetic_samples(self) -> list[TrainingSample]:
        """Generate synthetic UK compliance samples"""
        samples = []

        # Consumer Duty
        samples.append(self.create_sample(
            instruction="What are the FCA Consumer Duty requirements?",
            output="""FCA Consumer Duty (PRIN 2A) Requirements:

**Core Principle:**
Act to deliver good outcomes for retail customers.

**Cross-Cutting Rules:**
1. **Act in good faith** - Honest and fair dealing
2. **Avoid foreseeable harm** - Prevent harm to customers
3. **Enable pursuit of financial objectives** - Support customers

**Four Outcomes:**

1. **Products and Services (PRIN 2A.3)**
   - Products designed to meet target market needs
   - Distribution strategy appropriate
   - Regular review of product performance

2. **Price and Value (PRIN 2A.4)**
   - Fair value for price charged
   - Consider all elements of value
   - Document fair value assessment

3. **Consumer Understanding (PRIN 2A.5)**
   - Clear and understandable communications
   - Tailored to target market
   - Test communications effectiveness

4. **Consumer Support (PRIN 2A.6)**
   - Appropriate support throughout relationship
   - Easy to contact and get help
   - Identify and support vulnerable customers

**Implementation:**
- Board-level accountability
- Ongoing monitoring of outcomes
- Annual review and reporting
- Evidence of compliance""",
            category="consumer_duty",
            compliance_tags=["fca"]
        ))

        # APP Fraud Reimbursement
        samples.append(self.create_sample(
            instruction="What are the PSR APP fraud reimbursement requirements?",
            output="""PSR APP Fraud Reimbursement Requirements:

**Scope:**
Authorised Push Payment (APP) fraud where customer is tricked into making payment to fraudster.

**Mandatory Reimbursement:**
- Victims must be reimbursed unless exception applies
- 50/50 split between sending and receiving PSP
- Maximum claim: £415,000

**Timeline:**
- Reimbursement within 5 business days of claim
- Investigation can continue after reimbursement

**Exceptions (Consumer Standard of Caution):**
- Gross negligence by customer
- Customer ignored effective warnings
- First-party fraud (customer is fraudster)

**PSP Obligations:**

1. **Sending PSP:**
   - Implement effective fraud warnings
   - Confirmation of Payee checks
   - Transaction monitoring
   - Process claims promptly

2. **Receiving PSP:**
   - Account onboarding due diligence
   - Transaction monitoring
   - Mule account detection
   - Contribute to reimbursement

**Prevention Measures:**
- Effective scam warnings
- Confirmation of Payee
- Behavioral analytics
- Customer education""",
            category="psr_requirements",
            compliance_tags=["psr"]
        ))

        # UK GDPR ICO breach notification
        samples.append(self.create_sample(
            instruction="What are the UK GDPR ICO breach notification requirements?",
            output="""UK GDPR ICO Breach Notification Requirements:

**When to Notify ICO:**
Personal data breach that is likely to result in a risk to individuals' rights and freedoms.

**Timeline:**
- Within 72 hours of becoming aware
- If delayed, must explain reasons

**Information Required:**
1. Nature of the breach
2. Categories and approximate number of individuals
3. Categories and approximate number of records
4. Name and contact of DPO or other contact
5. Likely consequences
6. Measures taken or proposed

**How to Report:**
- ICO online reporting form
- Call ICO helpline for urgent breaches
- Keep detailed records

**When NOT Required:**
- Breach unlikely to result in risk to individuals
- Must still document internally

**Individual Notification (Article 34):**
Required when breach likely to result in HIGH risk:
- Direct communication to affected individuals
- Clear, plain language
- Include same information as ICO notification
- Advice on protective measures

**Exemptions from Individual Notification:**
- Appropriate safeguards render data unintelligible
- Subsequent measures eliminate high risk
- Disproportionate effort (use public communication)

**Documentation:**
Document ALL breaches regardless of notification:
- Facts of the breach
- Effects
- Remedial action taken""",
            category="uk_gdpr",
            compliance_tags=["uk_gdpr"]
        ))

        return samples
