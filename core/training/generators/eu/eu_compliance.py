"""
EU Compliance Generator - EU Regulatory Compliance Training Data

Generates training samples for eu_fintech_compliance role focusing on:
- GDPR requirements and articles
- PSD2 compliance
- DORA framework
- eIDAS regulations
"""

from ..base import BaseGenerator, TrainingSample


class EUComplianceGenerator(BaseGenerator):
    """Generator for eu_fintech_compliance role"""

    def __init__(self):
        super().__init__()
        self.role_name = "eu_fintech_compliance"
        self.focus_areas = ["gdpr_articles", "psd2_requirements", "dora_framework", "eidas"]
        self.compliance_tags = ["gdpr", "psd2", "dora", "eidas"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate EU compliance training samples"""
        samples = []

        # Extract sections and requirements
        sections = self.extract_sections(content)

        for section_name, section_content in sections.items():
            # GDPR-related sections
            if any(kw in section_name for kw in ["gdpr", "article", "data_protection"]):
                samples.extend(self._generate_gdpr_qa(section_name, section_content, source_file))

            # PSD2-related sections
            if any(kw in section_name for kw in ["psd2", "sca", "payment_services"]):
                samples.extend(self._generate_psd2_qa(section_name, section_content, source_file))

            # DORA-related sections
            if any(kw in section_name for kw in ["dora", "resilience", "ict_risk"]):
                samples.extend(self._generate_dora_qa(section_name, section_content, source_file))

        return samples

    def _generate_gdpr_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate GDPR Q&A samples"""
        samples = []

        # Extract bullet points as key requirements
        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"Explain the GDPR requirements for {section_name.replace('_', ' ')}",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="gdpr_requirements",
                compliance_tags=["gdpr"],
                source_file=source_file
            ))

        return samples

    def _generate_psd2_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate PSD2 Q&A samples"""
        samples = []

        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"What are the PSD2 requirements for {section_name.replace('_', ' ')}?",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="psd2_requirements",
                compliance_tags=["psd2"],
                source_file=source_file
            ))

        return samples

    def _generate_dora_qa(self, section_name: str, content: str, source_file: str) -> list[TrainingSample]:
        """Generate DORA Q&A samples"""
        samples = []

        requirements = self.extract_bullet_points(content)

        if requirements:
            samples.append(self.create_sample(
                instruction=f"Explain DORA requirements for {section_name.replace('_', ' ')}",
                output="\n".join(f"- {req}" for req in requirements[:10]),
                category="dora_framework",
                compliance_tags=["dora"],
                source_file=source_file
            ))

        return samples

    def generate_synthetic_samples(self) -> list[TrainingSample]:
        """Generate synthetic EU compliance samples"""
        samples = []

        # GDPR breach notification
        samples.append(self.create_sample(
            instruction="What are the GDPR Article 33 breach notification requirements?",
            output="""GDPR Article 33 requires notification of personal data breaches to the supervisory authority:

**Timeline:**
- Must notify within 72 hours of becoming aware of the breach
- If notification is delayed beyond 72 hours, must provide reasons

**Content of notification:**
1. Nature of the breach including categories and number of data subjects affected
2. Name and contact details of the DPO or other contact point
3. Likely consequences of the breach
4. Measures taken or proposed to address the breach

**Exception:**
- No notification required if the breach is unlikely to result in a risk to rights and freedoms of individuals

**Documentation:**
- All breaches must be documented regardless of notification requirement
- Documentation must include facts, effects, and remedial action taken""",
            category="gdpr_requirements",
            compliance_tags=["gdpr"]
        ))

        # PSD2 SCA requirements
        samples.append(self.create_sample(
            instruction="What are the PSD2 Strong Customer Authentication requirements?",
            output="""PSD2 Strong Customer Authentication (SCA) requirements:

**When SCA is required:**
- Customer-initiated electronic payments
- Access to payment account online
- Any action through remote channel with risk of payment fraud

**Authentication elements (2 of 3 required):**
1. **Knowledge** - Something only the user knows (password, PIN)
2. **Possession** - Something only the user has (phone, token)
3. **Inherence** - Something the user is (biometrics)

**Dynamic linking (Article 97(2)):**
- Authentication code must be linked to specific amount and payee
- Any change to amount or payee invalidates the code

**Independence requirement:**
- Elements must be independent - breach of one doesn't compromise others
- Different channels for different factors

**SCA Exemptions (RTS):**
- Low value (<€30, cumulative €100)
- Recurring transactions (same amount, same payee)
- Trusted beneficiaries (added with SCA)
- Transaction Risk Analysis (based on fraud rates)""",
            category="psd2_requirements",
            compliance_tags=["psd2"]
        ))

        # DORA ICT risk
        samples.append(self.create_sample(
            instruction="What are the DORA ICT risk management requirements?",
            output="""DORA (Digital Operational Resilience Act) ICT risk management requirements:

**ICT Risk Management Framework (Articles 5-16):**
1. Establish comprehensive ICT risk management framework
2. Define clear roles and responsibilities
3. Regular review and updates

**Key Requirements:**

1. **Asset Management (Article 8)**
   - Maintain inventory of all ICT assets
   - Map dependencies including third-party
   - Classify by criticality

2. **Access Control (Article 9)**
   - Implement least privilege principle
   - Multi-factor authentication for critical systems
   - Regular access reviews

3. **Incident Management (Articles 17-23)**
   - Detection mechanisms for ICT incidents
   - Classification (major vs minor)
   - Reporting to authorities (initial, intermediate, final)

4. **Business Continuity (Article 11)**
   - ICT business continuity policy
   - Defined RTO/RPO
   - Regular testing

5. **Third-Party Risk (Articles 28-44)**
   - Due diligence before engagement
   - Ongoing monitoring
   - Exit strategies for critical providers

**Applicability:** From 17 January 2025""",
            category="dora_framework",
            compliance_tags=["dora"]
        ))

        return samples
