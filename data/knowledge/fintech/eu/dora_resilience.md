# DORA - Digital Operational Resilience Act

## Overview

The Digital Operational Resilience Act (DORA) - Regulation (EU) 2022/2554 establishes uniform requirements for the security of network and information systems in the financial sector. It applies from 17 January 2025.

## Scope

DORA applies to:
- Credit institutions
- Payment institutions
- E-money institutions
- Investment firms
- Crypto-asset service providers
- ICT third-party service providers (critical)

## ICT Risk Management Framework (Articles 5-16)

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ICTAsset:
    """ICT asset in the inventory"""
    asset_id: str
    name: str
    type: str  # hardware, software, network, data
    classification: RiskLevel
    owner: str
    dependencies: list[str] = field(default_factory=list)
    supports_critical_function: bool = False
    third_party_provider: Optional[str] = None

@dataclass
class ICTRisk:
    """ICT risk assessment"""
    risk_id: str
    description: str
    likelihood: RiskLevel
    impact: RiskLevel
    overall_level: RiskLevel
    affected_assets: list[str]
    mitigation_measures: list[str]
    residual_risk: RiskLevel
    reviewed_at: datetime

class ICTRiskManagement:
    """
    DORA ICT Risk Management Framework

    Articles 5-16 requirements
    """

    def __init__(self):
        self.assets: dict[str, ICTAsset] = {}
        self.risks: dict[str, ICTRisk] = {}

    def get_asset_inventory(self) -> list[ICTAsset]:
        """
        Article 8 - ICT asset inventory

        Must maintain inventory of all ICT assets with dependencies
        """
        return list(self.assets.values())

    def classify_asset(
        self,
        asset_id: str,
        supports_critical: bool,
        data_sensitivity: str
    ) -> RiskLevel:
        """
        Article 8 - Asset classification

        Classify based on criticality and sensitivity
        """
        if supports_critical:
            return RiskLevel.CRITICAL
        if data_sensitivity == "sensitive":
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    def track_dependencies(
        self,
        asset_id: str,
        dependencies: list[str]
    ) -> dict:
        """
        Article 8 - Dependency mapping

        Track all dependencies including third-party
        """
        asset = self.assets.get(asset_id)
        if asset:
            asset.dependencies = dependencies
            return {
                "asset_id": asset_id,
                "dependencies": dependencies,
                "third_party_count": sum(
                    1 for d in dependencies
                    if self.assets.get(d, {}).third_party_provider
                )
            }
        return {}

    def assess_risk(
        self,
        asset_id: str,
        threat_scenario: str
    ) -> ICTRisk:
        """
        Article 9 - ICT risk assessment

        Assess risks to ICT assets
        """
        asset = self.assets.get(asset_id)

        # Calculate risk levels
        likelihood = self._assess_likelihood(threat_scenario)
        impact = self._assess_impact(asset, threat_scenario)
        overall = self._calculate_overall_risk(likelihood, impact)

        risk = ICTRisk(
            risk_id=f"RISK-{asset_id}-{datetime.now().strftime('%Y%m%d')}",
            description=threat_scenario,
            likelihood=likelihood,
            impact=impact,
            overall_level=overall,
            affected_assets=[asset_id] + (asset.dependencies if asset else []),
            mitigation_measures=[],
            residual_risk=overall,
            reviewed_at=datetime.utcnow()
        )

        self.risks[risk.risk_id] = risk
        return risk
```

## ICT Incident Management (Articles 17-23)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()

class IncidentClassification(Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

@dataclass
class ICTIncident:
    """ICT-related incident"""
    incident_id: str
    description: str
    classification: IncidentClassification
    detection_time: datetime
    affected_services: list[str]
    root_cause: Optional[str] = None
    resolution_time: Optional[datetime] = None
    reported_to_authority: bool = False

class ICTIncidentManagement:
    """
    DORA ICT Incident Management

    Articles 17-23 requirements
    """

    # Major incident criteria (Article 18)
    MAJOR_INCIDENT_THRESHOLDS = {
        "affected_clients_percent": 10,
        "affected_transactions_percent": 10,
        "service_downtime_hours": 2,
        "economic_impact_eur": 100000,
        "data_integrity_affected": True,
        "cross_border_impact": True,
    }

    async def detect_incident(
        self,
        event_type: str,
        affected_services: list[str],
        details: dict
    ) -> ICTIncident:
        """
        Article 17 - Incident detection

        Detect and create incident record
        """
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Classify incident
        classification = self.classify_incident(
            affected_services=affected_services,
            details=details
        )

        incident = ICTIncident(
            incident_id=incident_id,
            description=f"{event_type}: {details.get('summary', '')}",
            classification=classification,
            detection_time=datetime.utcnow(),
            affected_services=affected_services
        )

        logger.critical(
            "ict_incident_detected",
            incident_id=incident_id,
            classification=classification.value,
            affected_services=affected_services
        )

        return incident

    def classify_incident(
        self,
        affected_services: list[str],
        details: dict
    ) -> IncidentClassification:
        """
        Article 18 - Incident classification

        Classify as minor, major, or critical based on impact
        """
        # Check major incident criteria
        is_major = any([
            details.get("affected_clients_percent", 0) >= self.MAJOR_INCIDENT_THRESHOLDS["affected_clients_percent"],
            details.get("service_downtime_hours", 0) >= self.MAJOR_INCIDENT_THRESHOLDS["service_downtime_hours"],
            details.get("data_integrity_affected", False),
            details.get("cross_border_impact", False),
        ])

        if is_major:
            if details.get("critical_function_affected", False):
                return IncidentClassification.CRITICAL
            return IncidentClassification.MAJOR

        return IncidentClassification.MINOR

    def assess_impact(
        self,
        incident: ICTIncident
    ) -> dict:
        """
        Article 18 - Impact assessment

        Assess incident impact for reporting
        """
        return {
            "incident_id": incident.incident_id,
            "classification": incident.classification.value,
            "duration_hours": self._calculate_duration(incident),
            "affected_services_count": len(incident.affected_services),
            "requires_authority_notification": incident.classification in [
                IncidentClassification.MAJOR,
                IncidentClassification.CRITICAL
            ]
        }

    async def report_incident(
        self,
        incident: ICTIncident
    ) -> dict:
        """
        Article 19 - Incident reporting

        Report major incidents to competent authority
        """
        if incident.classification not in [
            IncidentClassification.MAJOR,
            IncidentClassification.CRITICAL
        ]:
            return {"reported": False, "reason": "Not a major incident"}

        # Prepare initial notification (within required timeframe)
        notification = {
            "incident_id": incident.incident_id,
            "entity_name": self.entity_name,
            "entity_lei": self.entity_lei,
            "detection_time": incident.detection_time.isoformat(),
            "classification": incident.classification.value,
            "affected_services": incident.affected_services,
            "preliminary_root_cause": incident.root_cause,
            "actions_taken": "Investigation ongoing",
        }

        # Submit to authority
        response = await self._submit_to_authority(notification)

        incident.reported_to_authority = True

        logger.info(
            "incident_reported_to_authority",
            incident_id=incident.incident_id,
            authority_reference=response.get("reference")
        )

        return {
            "reported": True,
            "authority_reference": response.get("reference"),
            "next_report_due": response.get("next_report_deadline")
        }

    async def notify_authority(
        self,
        incident: ICTIncident,
        notification_type: str  # initial, intermediate, final
    ) -> dict:
        """
        Submit incident notification to competent authority

        Initial: Within 4 hours of classification as major
        Intermediate: Within 72 hours
        Final: Within 1 month of resolution
        """
        return await self._submit_notification(incident, notification_type)

    def determine_severity(
        self,
        incident: ICTIncident
    ) -> str:
        """Helper to determine severity for logging"""
        return incident.classification.value
```

## Business Continuity (Article 11)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BusinessContinuityPlan:
    """ICT business continuity plan"""
    plan_id: str
    critical_function: str
    rto_hours: int  # Recovery Time Objective
    rpo_hours: int  # Recovery Point Objective
    backup_strategy: str
    failover_procedure: str
    last_tested: Optional[datetime] = None
    test_result: Optional[str] = None

class BusinessContinuity:
    """
    DORA Business Continuity Management

    Article 11 requirements
    """

    async def backup_data(
        self,
        data_category: str,
        critical: bool = False
    ) -> dict:
        """
        Article 11 - Data backup

        Ensure regular backups of critical data
        """
        backup_id = f"BKP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Determine backup frequency based on criticality
        if critical:
            # Critical data: real-time replication
            backup_type = "realtime_replication"
        else:
            # Standard: daily incremental, weekly full
            backup_type = "incremental"

        result = await self._execute_backup(data_category, backup_type)

        return {
            "backup_id": backup_id,
            "data_category": data_category,
            "backup_type": backup_type,
            "completed_at": datetime.utcnow().isoformat(),
            "size_bytes": result["size"],
            "location": result["location"]
        }

    async def disaster_recovery(
        self,
        scenario: str,
        affected_systems: list[str]
    ) -> dict:
        """
        Article 11 - Disaster recovery

        Execute disaster recovery procedures
        """
        # Initiate failover
        failover_result = await self._initiate_failover(affected_systems)

        # Restore from backups if needed
        if failover_result["requires_restore"]:
            restore_result = await self._restore_from_backup(affected_systems)
        else:
            restore_result = {"status": "not_required"}

        return {
            "scenario": scenario,
            "failover_status": failover_result["status"],
            "restore_status": restore_result["status"],
            "recovered_at": datetime.utcnow().isoformat(),
            "rto_met": failover_result.get("rto_met", True)
        }

    async def failover(
        self,
        primary_system: str,
        secondary_system: str
    ) -> dict:
        """
        Execute failover to secondary system
        """
        # Check secondary readiness
        ready = await self._check_secondary_ready(secondary_system)
        if not ready:
            raise FailoverError("Secondary system not ready")

        # Execute failover
        await self._switch_traffic(primary_system, secondary_system)

        return {
            "status": "completed",
            "active_system": secondary_system,
            "failover_time": datetime.utcnow().isoformat()
        }

    async def test_bcp(
        self,
        plan: BusinessContinuityPlan
    ) -> dict:
        """
        Article 11 - BCP testing

        Test business continuity plans regularly
        """
        test_id = f"TEST-{plan.plan_id}-{datetime.now().strftime('%Y%m%d')}"

        # Simulate failure scenario
        test_result = await self._simulate_failure(plan.critical_function)

        # Measure recovery time
        recovery_started = datetime.utcnow()
        recovery_result = await self._execute_recovery(plan)
        recovery_completed = datetime.utcnow()

        recovery_time_hours = (
            recovery_completed - recovery_started
        ).total_seconds() / 3600

        # Update plan with test results
        plan.last_tested = datetime.utcnow()
        plan.test_result = "passed" if recovery_time_hours <= plan.rto_hours else "failed"

        return {
            "test_id": test_id,
            "plan_id": plan.plan_id,
            "rto_target_hours": plan.rto_hours,
            "actual_recovery_hours": recovery_time_hours,
            "rto_met": recovery_time_hours <= plan.rto_hours,
            "result": plan.test_result
        }
```

## Third-Party Risk Management (Articles 28-44)

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class TPPCriticality(Enum):
    NON_CRITICAL = "non_critical"
    IMPORTANT = "important"
    CRITICAL = "critical"

@dataclass
class ICTThirdParty:
    """ICT third-party service provider"""
    provider_id: str
    name: str
    services: list[str]
    criticality: TPPCriticality
    contract_end_date: datetime
    exit_strategy: Optional[str] = None
    last_assessment: Optional[datetime] = None

class ThirdPartyRiskManagement:
    """
    DORA Third-Party ICT Risk Management

    Articles 28-44 requirements
    """

    def assess_vendor_risk(
        self,
        provider: ICTThirdParty
    ) -> dict:
        """
        Article 28 - Third-party risk assessment

        Assess risks from ICT third-party providers
        """
        risk_factors = {
            "concentration_risk": self._assess_concentration(provider),
            "substitutability": self._assess_substitutability(provider),
            "compliance_risk": self._assess_compliance(provider),
            "security_posture": self._assess_security(provider),
            "financial_stability": self._assess_financial_health(provider)
        }

        overall_risk = self._calculate_overall_risk(risk_factors)

        return {
            "provider_id": provider.provider_id,
            "criticality": provider.criticality.value,
            "risk_factors": risk_factors,
            "overall_risk": overall_risk,
            "assessed_at": datetime.utcnow().isoformat()
        }

    def monitor_tpp(
        self,
        provider: ICTThirdParty
    ) -> dict:
        """
        Article 28 - Ongoing monitoring

        Continuously monitor third-party providers
        """
        # Check service levels
        sla_compliance = self._check_sla_compliance(provider.provider_id)

        # Check security incidents
        security_incidents = self._check_provider_incidents(provider.provider_id)

        # Check concentration
        concentration = self._check_concentration_level(provider.provider_id)

        return {
            "provider_id": provider.provider_id,
            "sla_compliance_percent": sla_compliance,
            "security_incidents_30d": len(security_incidents),
            "concentration_level": concentration,
            "monitored_at": datetime.utcnow().isoformat()
        }

    def vendor_due_diligence(
        self,
        provider: ICTThirdParty
    ) -> dict:
        """
        Article 28 - Due diligence

        Conduct due diligence before and during relationship
        """
        due_diligence = {
            "financial_check": self._verify_financial_stability(provider),
            "security_certification": self._verify_certifications(provider),
            "compliance_check": self._verify_regulatory_compliance(provider),
            "bcp_assessment": self._assess_bcp_capabilities(provider),
            "exit_plan_review": self._review_exit_strategy(provider)
        }

        provider.last_assessment = datetime.utcnow()

        return {
            "provider_id": provider.provider_id,
            "due_diligence_results": due_diligence,
            "overall_status": "approved" if all(
                v.get("status") == "passed" for v in due_diligence.values()
            ) else "requires_review",
            "assessed_at": datetime.utcnow().isoformat()
        }

    def create_exit_strategy(
        self,
        provider: ICTThirdParty
    ) -> str:
        """
        Article 28 - Exit strategy

        Define exit strategy for critical providers
        """
        if provider.criticality != TPPCriticality.CRITICAL:
            return "Standard contract termination procedures apply"

        exit_strategy = f"""
        Exit Strategy for {provider.name}

        1. Alternative Providers:
           - {self._identify_alternatives(provider.services)}

        2. Data Migration:
           - Data export format: JSON/CSV
           - Migration timeline: 90 days
           - Data validation procedures

        3. Service Continuity:
           - Transition period: 6 months
           - Parallel running: 3 months
           - Fallback procedures

        4. Knowledge Transfer:
           - Documentation requirements
           - Training for internal teams
           - Support during transition

        5. Contract Provisions:
           - Data deletion confirmation
           - Post-termination support
           - Dispute resolution
        """

        provider.exit_strategy = exit_strategy
        return exit_strategy
```
