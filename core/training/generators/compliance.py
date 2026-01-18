"""
Compliance Generator - Regulatory Q&A Training Data

Generates training samples for the fintech_compliance role focusing on:
- RBI guidelines
- SEBI regulations
- PCI-DSS requirements
- DPDP Act compliance
"""

import re
from .base import BaseGenerator, TrainingSample


class ComplianceGenerator(BaseGenerator):
    """Generator for fintech_compliance role"""

    def __init__(self):
        super().__init__()
        self.role_name = "fintech_compliance"
        self.focus_areas = ["rbi_guidelines", "sebi_regulations", "dpdp_act", "pci_dss"]
        self.compliance_tags = ["pci_dss", "rbi", "sebi", "dpdp", "pmla"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate compliance-focused training samples"""
        samples = []

        # Generate regulatory Q&A samples
        samples.extend(self._generate_qa_samples(content, source_file))

        # Generate compliance checklist samples
        samples.extend(self._generate_checklist_samples(content, source_file))

        # Generate gap analysis samples
        samples.extend(self._generate_gap_analysis_samples(content, source_file))

        # Add synthetic regulatory samples
        samples.extend(self.generate_rbi_samples())
        samples.extend(self.generate_dpdp_samples())

        return samples

    def _generate_qa_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate Q&A style samples from document sections"""
        samples = []
        sections = self.extract_sections(content)

        for section_name, section_content in sections.items():
            if len(section_content) < 100:
                continue

            # Clean section name
            topic = section_name.replace("_", " ").title()

            # Q&A about the requirement
            samples.append(self.create_sample(
                instruction=f"What are the compliance requirements for {topic}?",
                output=self._format_compliance_answer(topic, section_content),
                category="regulatory_qa",
                source_file=source_file
            ))

            # Implementation guidance
            samples.append(self.create_sample(
                instruction=f"How should we implement {topic} to meet regulatory requirements?",
                output=self._format_implementation_guidance(topic, section_content),
                category="implementation_guidance",
                source_file=source_file
            ))

        return samples

    def _generate_checklist_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate compliance checklist samples"""
        samples = []
        requirements = self.extract_requirements(content)

        if requirements:
            # Create comprehensive checklist
            checklist_items = []
            for req in requirements:
                checklist_items.append(f"- [ ] Requirement {req['id']}: {req['title']}")

            samples.append(self.create_sample(
                instruction="Generate a compliance checklist for this regulatory framework",
                input_text=content[:500],
                output=f"""## Compliance Checklist

### Requirements Overview:

{chr(10).join(checklist_items)}

### Verification Steps:

1. **Documentation Review**
   - Policy documents updated
   - Procedures documented
   - Evidence collected

2. **Technical Controls**
   - Security measures implemented
   - Monitoring in place
   - Audit logging enabled

3. **Process Verification**
   - Staff training completed
   - Incident response tested
   - Business continuity planned

### Sign-off Requirements:
- [ ] Compliance Officer review
- [ ] Technical lead verification
- [ ] Management approval""",
                category="compliance_checklist",
                source_file=source_file
            ))

        return samples

    def _generate_gap_analysis_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate compliance gap analysis samples"""
        samples = []
        bullet_points = self.extract_bullet_points(content)

        if len(bullet_points) >= 3:
            requirements_text = "\n".join([f"- {bp}" for bp in bullet_points[:10]])

            samples.append(self.create_sample(
                instruction="Perform a compliance gap analysis for our FinTech platform",
                input_text=requirements_text,
                output=self._generate_gap_analysis_template(bullet_points),
                category="gap_analysis",
                source_file=source_file
            ))

        return samples

    def _format_compliance_answer(self, topic: str, content: str) -> str:
        """Format compliance Q&A answer"""
        # Extract key points
        bullet_points = self.extract_bullet_points(content)
        key_points = bullet_points[:5] if bullet_points else []

        points_text = ""
        if key_points:
            points_text = "\n### Key Requirements:\n" + "\n".join([f"- {p}" for p in key_points])

        return f"""## {topic} - Compliance Requirements

{content[:600]}

{points_text}

### Compliance Considerations:

1. **Documentation**: Maintain records of compliance activities
2. **Monitoring**: Implement continuous monitoring
3. **Training**: Ensure staff awareness
4. **Audit**: Schedule regular compliance audits

### Related Regulations:
- PCI-DSS for payment data
- RBI guidelines for banking operations
- DPDP Act for personal data protection"""

    def _format_implementation_guidance(self, topic: str, content: str) -> str:
        """Format implementation guidance"""
        return f"""## Implementation Guidance: {topic}

### Overview:
{content[:400]}

### Implementation Steps:

#### Phase 1: Assessment
1. Review current state against requirements
2. Identify gaps and risks
3. Document findings

#### Phase 2: Design
1. Define target architecture
2. Select appropriate controls
3. Plan implementation timeline

#### Phase 3: Implementation
1. Deploy technical controls
2. Update policies and procedures
3. Train personnel

#### Phase 4: Validation
1. Test implemented controls
2. Verify compliance
3. Document evidence

### Success Criteria:
- All requirements addressed
- Evidence documented
- Stakeholder sign-off obtained
- Ongoing monitoring established"""

    def _generate_gap_analysis_template(self, requirements: list[str]) -> str:
        """Generate gap analysis template"""
        req_analysis = []
        for i, req in enumerate(requirements[:5], 1):
            req_analysis.append(f"""
### Requirement {i}: {req[:80]}
| Aspect | Current State | Gap | Priority | Remediation |
|--------|--------------|-----|----------|-------------|
| Technical | Partial | Medium | High | Implement controls |
| Process | Missing | High | Critical | Define procedures |
| Documentation | Outdated | Low | Medium | Update docs |""")

        return f"""## Compliance Gap Analysis Report

### Executive Summary:
This gap analysis identifies areas where the current implementation does not meet regulatory requirements.

### Scope:
- Regulatory framework review
- Technical controls assessment
- Process and procedure evaluation

### Findings:
{"".join(req_analysis)}

### Summary:

| Category | Compliant | Partial | Non-Compliant |
|----------|-----------|---------|---------------|
| Technical Controls | 60% | 25% | 15% |
| Processes | 40% | 35% | 25% |
| Documentation | 50% | 30% | 20% |

### Recommendations:
1. **Critical**: Address non-compliant items within 30 days
2. **High**: Complete partial implementations within 60 days
3. **Medium**: Update documentation within 90 days

### Next Steps:
1. Prioritize critical gaps
2. Allocate resources
3. Create remediation timeline
4. Schedule follow-up assessment"""

    def generate_rbi_samples(self) -> list[TrainingSample]:
        """Generate RBI-specific compliance samples"""
        samples = []

        # Payment Aggregator guidelines
        samples.append(self.create_sample(
            instruction="Explain the RBI Payment Aggregator guidelines and their key requirements",
            output="""## RBI Payment Aggregator Guidelines (2020)

### Overview:
RBI introduced comprehensive guidelines for Payment Aggregators (PAs) and Payment Gateways to regulate entities facilitating digital payments.

### Key Requirements:

#### 1. Registration & Authorization
- All PAs must obtain RBI authorization
- Minimum net worth of ₹15 crore (for existing) / ₹25 crore (for new)
- Apply within stipulated timeline

#### 2. Governance
- Board-approved policy framework
- Independent compliance function
- Risk management framework

#### 3. Settlement & Escrow
- Funds in escrow account (Schedule Bank)
- Settlement to merchants within T+1 (domestic)
- No interchange of funds between PA and PG activities

#### 4. Data Localization
- All payment data stored in India
- Cross-border data transfer restrictions
- Audit trail for data access

#### 5. Security Requirements
- PCI-DSS compliance mandatory
- Annual security audit
- Cyber security framework implementation

#### 6. Merchant Onboarding
- KYC for all merchants
- Due diligence process
- Ongoing monitoring

### Compliance Timeline:
- Existing entities: 2 years from guidelines
- New entities: Authorization before commencement

### Penalties:
- Non-compliance can result in:
  - Monetary penalties
  - Authorization cancellation
  - Regulatory action

### Documentation Required:
1. Board resolutions
2. Policy documents
3. KYC records
4. Audit reports
5. Compliance certificates""",
            category="rbi_guidelines",
            compliance_tags=["RBI-PA"]
        ))

        # Data localization
        samples.append(self.create_sample(
            instruction="What are the RBI data localization requirements for payment systems?",
            output="""## RBI Data Localization Requirements

### Mandate:
RBI mandates that all payment system data must be stored only in India.

### Scope:
- Full end-to-end transaction details
- Customer data
- Payment credentials
- Authentication data

### Covered Entities:
1. Payment System Operators (PSOs)
2. Banks
3. Payment Aggregators
4. Card Networks
5. Wallet providers

### Requirements:

#### Data Storage:
- Primary data centers in India
- DR sites in India
- No mirroring abroad

#### Data Retention:
- Minimum retention as per regulations
- Secure deletion procedures
- Audit trail for data handling

#### Cross-Border Transactions:
- Transaction processing can occur abroad
- Data must be deleted from foreign systems after processing
- Copy must be stored in India within 24 hours

### Compliance Steps:

1. **Audit Current State**
   - Identify all payment data locations
   - Map data flows
   - Document cross-border transfers

2. **Migrate Data**
   - Set up India data centers
   - Migrate existing data
   - Update backup procedures

3. **Update Systems**
   - Modify applications for India-only storage
   - Implement data routing
   - Enable audit logging

4. **Verify Compliance**
   - Conduct internal audit
   - External assessment
   - Submit compliance report

### Evidence Requirements:
- System architecture diagrams
- Data center certifications
- Audit reports
- Compliance declarations""",
            category="data_localization",
            compliance_tags=["RBI-DL"]
        ))

        return samples

    def generate_dpdp_samples(self) -> list[TrainingSample]:
        """Generate DPDP Act compliance samples"""
        samples = []

        samples.append(self.create_sample(
            instruction="Explain the key provisions of the Digital Personal Data Protection (DPDP) Act for FinTech companies",
            output="""## DPDP Act - Key Provisions for FinTech

### Overview:
The Digital Personal Data Protection Act, 2023 establishes a framework for processing digital personal data in India.

### Key Definitions:

- **Data Principal**: Individual whose data is being processed
- **Data Fiduciary**: Entity determining purpose of processing
- **Significant Data Fiduciary**: Entities with high volume/sensitivity

### Principles:

#### 1. Lawful Processing
- Consent-based processing
- Legitimate uses defined

#### 2. Purpose Limitation
- Data used only for stated purpose
- New purposes require fresh consent

#### 3. Data Minimization
- Collect only necessary data
- Limit retention period

#### 4. Accuracy
- Ensure data is accurate
- Update mechanisms required

### FinTech Specific Requirements:

#### Consent Management:
```
- Clear, specific consent requests
- Granular consent options
- Easy withdrawal mechanism
- Consent records maintained
```

#### Data Principal Rights:
1. Right to access data
2. Right to correction
3. Right to erasure
4. Right to grievance redressal

#### Security Measures:
- Reasonable security safeguards
- Breach notification within 72 hours
- Security audit requirements

### Cross-Border Transfer:
- Allowed to notified countries
- Restricted to others
- Contractual safeguards required

### Penalties:
| Violation | Maximum Penalty |
|-----------|----------------|
| Non-compliance | ₹50 crore |
| Child data breach | ₹200 crore |
| Repeated violations | ₹250 crore |

### Implementation Checklist:
- [ ] Appoint Data Protection Officer
- [ ] Implement consent mechanism
- [ ] Update privacy policy
- [ ] Set up grievance redressal
- [ ] Establish breach response
- [ ] Train employees""",
            category="dpdp_act",
            compliance_tags=["DPDP"]
        ))

        return samples
