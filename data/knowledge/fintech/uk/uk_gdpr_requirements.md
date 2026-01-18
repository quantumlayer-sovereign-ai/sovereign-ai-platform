# UK GDPR Requirements for FinTech

## Overview

The UK GDPR (incorporated via Data Protection Act 2018) applies to processing of personal data in the UK post-Brexit. While largely similar to EU GDPR, there are key differences particularly around international transfers.

## Key Differences from EU GDPR

1. **Supervisory Authority**: ICO (Information Commissioner's Office) instead of EU DPAs
2. **International Transfers**: UK adequacy decisions, IDTA instead of SCCs
3. **Derogations**: Some UK-specific exemptions
4. **Enforcement**: ICO fines (same maximum as EU GDPR)

## ICO Breach Notification

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import structlog

logger = structlog.get_logger()

class BreachRiskLevel(Enum):
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    HIGH = "high"

@dataclass
class UKPersonalDataBreach:
    """UK GDPR personal data breach record"""
    breach_id: str
    description: str
    data_categories: list[str]
    affected_count: int
    detection_time: datetime
    risk_level: BreachRiskLevel
    notified_ico: bool = False
    notified_individuals: bool = False

class UKGDPRBreachHandler:
    """
    Handle UK GDPR breach notification requirements

    Report to ICO within 72 hours if risk to individuals
    """

    ICO_NOTIFICATION_HOURS = 72
    ICO_BREACH_REPORT_URL = "https://ico.org.uk/make-a-complaint/data-protection-complaints/personal-data-breach/"

    async def notify_ico(
        self,
        breach: UKPersonalDataBreach
    ) -> dict:
        """
        Notify ICO of personal data breach

        Required within 72 hours unless no risk to individuals
        """
        # Check if notification required
        if breach.risk_level == BreachRiskLevel.UNLIKELY:
            logger.info(
                "breach_notification_not_required",
                breach_id=breach.breach_id,
                reason="Unlikely to result in risk to individuals"
            )
            return {
                "notified": False,
                "reason": "Risk assessment: unlikely to affect individuals"
            }

        # Calculate deadline
        deadline = breach.detection_time + timedelta(hours=self.ICO_NOTIFICATION_HOURS)

        # Prepare notification
        notification = {
            "organization_name": self.organization_name,
            "ico_registration_number": self.ico_registration,
            "contact_name": self.dpo_name,
            "contact_email": self.dpo_email,
            "breach_date": breach.detection_time.isoformat(),
            "description": breach.description,
            "data_categories": breach.data_categories,
            "approximate_affected": breach.affected_count,
            "consequences": self._assess_consequences(breach),
            "measures_taken": self._document_measures(breach),
        }

        # Submit to ICO
        response = await self._submit_to_ico(notification)

        breach.notified_ico = True

        logger.info(
            "breach_reported_to_ico",
            breach_id=breach.breach_id,
            ico_reference=response.get("reference")
        )

        return {
            "notified": True,
            "ico_reference": response.get("reference"),
            "notification_time": datetime.utcnow().isoformat(),
            "deadline_met": datetime.utcnow() < deadline
        }

    async def notify_affected_individuals(
        self,
        breach: UKPersonalDataBreach
    ) -> dict:
        """
        Notify affected individuals

        Required when high risk to rights and freedoms
        """
        if breach.risk_level not in [BreachRiskLevel.LIKELY, BreachRiskLevel.HIGH]:
            return {
                "notified": False,
                "reason": "Risk level does not require individual notification"
            }

        # Prepare communication
        notification_content = self._prepare_individual_notification(breach)

        # Send notifications
        sent_count = await self._send_notifications(
            breach.breach_id,
            notification_content
        )

        breach.notified_individuals = True

        return {
            "notified": True,
            "individuals_notified": sent_count,
            "notification_time": datetime.utcnow().isoformat()
        }

    def report_breach(
        self,
        description: str,
        data_categories: list[str],
        affected_count: int
    ) -> UKPersonalDataBreach:
        """
        Create breach record for reporting

        Assesses risk level for notification requirements
        """
        risk_level = self._assess_risk_level(
            data_categories,
            affected_count
        )

        breach = UKPersonalDataBreach(
            breach_id=self._generate_breach_id(),
            description=description,
            data_categories=data_categories,
            affected_count=affected_count,
            detection_time=datetime.utcnow(),
            risk_level=risk_level
        )

        logger.critical(
            "personal_data_breach_detected",
            breach_id=breach.breach_id,
            risk_level=risk_level.value,
            affected_count=affected_count
        )

        return breach

    def _assess_risk_level(
        self,
        data_categories: list[str],
        affected_count: int
    ) -> BreachRiskLevel:
        """Assess risk level for breach notification decision"""
        high_risk_categories = [
            "financial_data", "health_data", "biometric",
            "credentials", "national_id"
        ]

        if any(cat in high_risk_categories for cat in data_categories):
            if affected_count > 1000:
                return BreachRiskLevel.HIGH
            return BreachRiskLevel.LIKELY

        if affected_count > 10000:
            return BreachRiskLevel.LIKELY
        elif affected_count > 100:
            return BreachRiskLevel.POSSIBLE

        return BreachRiskLevel.UNLIKELY
```

## International Data Transfers

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class UKTransferMechanism(Enum):
    UK_ADEQUACY = "uk_adequacy"
    IDTA = "international_data_transfer_agreement"
    UK_ADDENDUM = "uk_addendum_to_eu_sccs"
    BCR = "binding_corporate_rules"
    DEROGATION = "derogation"

# Countries with UK adequacy decisions
UK_ADEQUATE_COUNTRIES = [
    "EU/EEA",  # EU has adequacy for UK
    "Switzerland",
    "Japan",
    "South Korea",
    "Canada",
    "Argentina",
    "Israel",
    "New Zealand",
    "US",  # UK-US Data Bridge
]

@dataclass
class InternationalTransfer:
    """Record of international data transfer"""
    transfer_id: str
    destination_country: str
    data_categories: list[str]
    transfer_mechanism: UKTransferMechanism
    tia_completed: bool = False  # Transfer Impact Assessment
    documented: bool = False

class UKInternationalTransferValidator:
    """
    Validate UK GDPR international data transfers

    Post-Brexit requirements
    """

    def validate_transfer(
        self,
        destination_country: str,
        data_categories: list[str],
        proposed_mechanism: Optional[UKTransferMechanism] = None
    ) -> dict:
        """
        Validate international data transfer compliance

        Returns required mechanism and TIA requirements
        """
        # Check UK adequacy decisions
        if destination_country in UK_ADEQUATE_COUNTRIES:
            return {
                "valid": True,
                "mechanism": UKTransferMechanism.UK_ADEQUACY.value,
                "tia_required": False,
                "additional_safeguards": None
            }

        # Require appropriate safeguards
        if proposed_mechanism is None:
            return {
                "valid": False,
                "reason": "No transfer mechanism for non-adequate country",
                "recommended_mechanisms": [
                    UKTransferMechanism.IDTA.value,
                    UKTransferMechanism.UK_ADDENDUM.value
                ]
            }

        # IDTA or UK Addendum
        if proposed_mechanism in [
            UKTransferMechanism.IDTA,
            UKTransferMechanism.UK_ADDENDUM
        ]:
            return {
                "valid": True,
                "mechanism": proposed_mechanism.value,
                "tia_required": True,
                "additional_safeguards": self._recommend_safeguards(
                    destination_country
                )
            }

        return {
            "valid": False,
            "reason": "Invalid transfer mechanism"
        }

    def conduct_tia(
        self,
        destination_country: str,
        data_categories: list[str],
        transfer_mechanism: UKTransferMechanism
    ) -> dict:
        """
        Conduct Transfer Impact Assessment

        Required for IDTA/UK Addendum transfers
        """
        # Assess destination country laws
        country_assessment = self._assess_destination_laws(destination_country)

        # Identify risks
        risks = self._identify_transfer_risks(
            destination_country,
            data_categories
        )

        # Determine supplementary measures
        supplementary_measures = []
        if risks["surveillance_risk"] == "high":
            supplementary_measures.append("End-to-end encryption")
            supplementary_measures.append("Pseudonymization before transfer")

        return {
            "destination_country": destination_country,
            "country_assessment": country_assessment,
            "identified_risks": risks,
            "supplementary_measures": supplementary_measures,
            "conclusion": "proceed" if len(risks) < 3 else "review_required",
            "assessed_date": datetime.utcnow().isoformat()
        }
```

## Data Subject Rights (UK Specific)

```python
from datetime import datetime, timedelta
from typing import Optional

class UKDataSubjectRights:
    """
    UK GDPR Data Subject Rights

    Similar to EU GDPR with some UK-specific provisions
    """

    RESPONSE_DEADLINE_DAYS = 30
    EXTENSION_MONTHS = 2

    async def handle_sar(
        self,
        user_id: str,
        request_type: str,
        request_details: Optional[dict] = None
    ) -> dict:
        """
        Handle Subject Access Request (SAR)

        Must respond within 1 calendar month (extendable by 2 months)
        """
        request_id = self._generate_request_id()
        received_at = datetime.utcnow()
        deadline = received_at + timedelta(days=self.RESPONSE_DEADLINE_DAYS)

        if request_type == "access":
            return await self._handle_access(user_id, request_id, deadline)
        elif request_type == "erasure":
            return await self._handle_erasure(user_id, request_id, deadline)
        elif request_type == "portability":
            return await self._handle_portability(user_id, request_id, deadline)
        elif request_type == "rectification":
            return await self._handle_rectification(
                user_id, request_id, deadline, request_details
            )
        else:
            raise ValueError(f"Unknown request type: {request_type}")

    async def _handle_access(
        self,
        user_id: str,
        request_id: str,
        deadline: datetime
    ) -> dict:
        """
        Handle access request

        Provide copy of personal data being processed
        """
        # Collect all personal data
        personal_data = await self._collect_user_data(user_id)

        # Include processing information
        processing_info = {
            "purposes": await self._get_processing_purposes(user_id),
            "categories": await self._get_data_categories(user_id),
            "recipients": await self._get_recipients(user_id),
            "retention_period": await self._get_retention_period(user_id),
            "source": await self._get_data_source(user_id),
            "automated_decisions": await self._get_automated_decisions(user_id)
        }

        return {
            "request_id": request_id,
            "personal_data": personal_data,
            "processing_information": processing_info,
            "deadline": deadline.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }

    async def delete_personal_data(
        self,
        user_id: str
    ) -> dict:
        """
        Handle erasure request (right to be forgotten)

        Delete unless legal retention applies
        """
        # Check legal holds
        legal_holds = await self._check_legal_retention(user_id)

        if legal_holds:
            # Partial deletion - retain legally required data
            deleted_categories = await self._delete_non_retained_data(user_id)
            return {
                "status": "partial",
                "deleted": deleted_categories,
                "retained_reason": "Legal retention requirements",
                "retained_until": legal_holds["retention_end"]
            }

        # Full deletion
        await self._delete_all_user_data(user_id)

        return {
            "status": "completed",
            "deleted_at": datetime.utcnow().isoformat()
        }

    async def export_user_data(
        self,
        user_id: str,
        format: str = "json"
    ) -> bytes:
        """
        Handle data portability request

        Provide data in commonly used, machine-readable format
        """
        data = await self._collect_portable_data(user_id)

        if format == "json":
            import json
            return json.dumps(data, indent=2).encode()
        elif format == "csv":
            return self._convert_to_csv(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
```

## UK-Specific Exemptions

```python
class UKGDPRExemptions:
    """
    UK GDPR specific exemptions

    From Schedule 2 of Data Protection Act 2018
    """

    def check_crime_prevention_exemption(
        self,
        processing_purpose: str
    ) -> bool:
        """
        Crime prevention and detection exemption

        Can restrict rights to prevent prejudice to crime prevention
        """
        crime_prevention_purposes = [
            "fraud_prevention",
            "aml_check",
            "sanctions_screening",
            "suspicious_activity_report"
        ]
        return processing_purpose in crime_prevention_purposes

    def check_legal_proceedings_exemption(
        self,
        processing_purpose: str
    ) -> bool:
        """
        Legal proceedings exemption

        Can restrict rights for legal claims
        """
        legal_purposes = [
            "legal_proceedings",
            "legal_advice",
            "establishing_rights",
            "defending_claims"
        ]
        return processing_purpose in legal_purposes

    def check_regulatory_exemption(
        self,
        processing_purpose: str,
        regulator: str
    ) -> bool:
        """
        Regulatory functions exemption

        For FCA, PRA, ICO regulatory activities
        """
        regulators = ["FCA", "PRA", "ICO", "HMRC"]
        regulatory_purposes = [
            "regulatory_compliance",
            "supervisory_activity",
            "enforcement"
        ]
        return (
            regulator in regulators and
            processing_purpose in regulatory_purposes
        )
```
