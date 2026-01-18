# FCA Handbook Requirements for FinTech

## Overview

The Financial Conduct Authority (FCA) is the conduct regulator for financial services in the UK. FinTech firms must comply with FCA Handbook requirements including Consumer Duty, PRIN, SYSC, and COBS.

## Consumer Duty (PRIN 2A)

The Consumer Duty is the FCA's flagship initiative requiring firms to deliver good outcomes for retail customers.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import structlog

logger = structlog.get_logger()

class OutcomeType(Enum):
    PRODUCTS_SERVICES = "products_and_services"
    PRICE_VALUE = "price_and_value"
    CONSUMER_UNDERSTANDING = "consumer_understanding"
    CONSUMER_SUPPORT = "consumer_support"

@dataclass
class CustomerOutcome:
    """Record of customer outcome assessment"""
    outcome_id: str
    customer_id: str
    outcome_type: OutcomeType
    assessment: str
    score: float  # 0-1, higher is better
    issues_identified: list[str]
    assessed_at: datetime

class ConsumerDutyCompliance:
    """
    FCA Consumer Duty compliance

    PRIN 2A - Acting to deliver good outcomes for retail customers
    """

    def assess_customer_outcome(
        self,
        customer_id: str,
        product_id: str,
        interaction_type: str
    ) -> CustomerOutcome:
        """
        Assess customer outcome for Consumer Duty compliance

        Firms must act in good faith, avoid foreseeable harm,
        and enable customers to pursue their financial objectives
        """
        outcome_type = self._determine_outcome_type(interaction_type)

        # Collect outcome data
        outcome_data = self._collect_outcome_data(customer_id, product_id)

        # Assess against Consumer Duty requirements
        assessment = self._assess_outcome(outcome_data, outcome_type)

        return CustomerOutcome(
            outcome_id=self._generate_outcome_id(),
            customer_id=customer_id,
            outcome_type=outcome_type,
            assessment=assessment["summary"],
            score=assessment["score"],
            issues_identified=assessment.get("issues", []),
            assessed_at=datetime.utcnow()
        )

    def monitor_outcomes(
        self,
        product_id: str,
        period_days: int = 30
    ) -> dict:
        """
        Monitor customer outcomes at product level

        PRIN 2A.4 - Products and services
        """
        outcomes = self._get_product_outcomes(product_id, period_days)

        # Aggregate analysis
        average_score = sum(o.score for o in outcomes) / len(outcomes) if outcomes else 0
        issues = [issue for o in outcomes for issue in o.issues_identified]
        issue_counts = self._count_issues(issues)

        # Check for Consumer Duty failures
        failures = [o for o in outcomes if o.score < 0.5]
        failure_rate = len(failures) / len(outcomes) if outcomes else 0

        result = {
            "product_id": product_id,
            "period_days": period_days,
            "total_outcomes": len(outcomes),
            "average_score": average_score,
            "failure_rate": failure_rate,
            "common_issues": issue_counts,
            "requires_action": failure_rate > 0.1 or average_score < 0.7
        }

        if result["requires_action"]:
            logger.warning(
                "consumer_duty_action_required",
                product_id=product_id,
                failure_rate=failure_rate
            )

        return result

    def customer_impact(
        self,
        decision_type: str,
        affected_customers: int
    ) -> dict:
        """
        Assess customer impact of business decisions

        Cross-cutting rule: Act in good faith
        """
        impact_assessment = {
            "decision_type": decision_type,
            "affected_customers": affected_customers,
            "foreseeable_harm": self._assess_foreseeable_harm(decision_type),
            "mitigating_actions": self._identify_mitigations(decision_type),
            "assessed_at": datetime.utcnow().isoformat()
        }

        if impact_assessment["foreseeable_harm"]["level"] == "high":
            impact_assessment["requires_senior_approval"] = True

        return impact_assessment


class FairValueAssessment:
    """
    Fair Value Assessment for Consumer Duty

    PRIN 2A.4 - Price and value outcome
    """

    def assess_fair_value(
        self,
        product_id: str,
        price: float,
        target_market: str
    ) -> dict:
        """
        Assess whether product provides fair value

        Consider benefits vs costs for target market
        """
        # Identify all costs
        costs = self._identify_all_costs(product_id)

        # Identify benefits
        benefits = self._identify_benefits(product_id, target_market)

        # Compare to market
        market_comparison = self._compare_to_market(product_id, price)

        # Assess fair value
        fair_value_score = self._calculate_fair_value(
            costs, benefits, market_comparison
        )

        return {
            "product_id": product_id,
            "price": price,
            "total_costs": sum(costs.values()),
            "identified_benefits": benefits,
            "market_comparison": market_comparison,
            "fair_value_score": fair_value_score,
            "is_fair_value": fair_value_score >= 0.6,
            "assessed_at": datetime.utcnow().isoformat()
        }
```

## Principles for Businesses (PRIN)

```python
class FCAprinciples:
    """
    FCA Principles for Businesses (PRIN 2.1)

    11 core principles that firms must follow
    """

    PRINCIPLES = {
        1: "Integrity - conduct business with integrity",
        2: "Skill, care and diligence",
        3: "Management and control - adequate risk management",
        4: "Financial prudence",
        5: "Market conduct - proper standards of market conduct",
        6: "Customers' interests - due regard to customer interests",
        7: "Communications - clear, fair and not misleading",
        8: "Conflicts of interest - manage fairly",
        9: "Customers: relationships of trust - suitable advice",
        10: "Clients' assets - adequate protection",
        11: "Relations with regulators - open and cooperative"
    }

    def check_principle_compliance(
        self,
        principle_number: int,
        activity: str,
        evidence: dict
    ) -> dict:
        """
        Check compliance with FCA Principle

        Returns assessment with any issues
        """
        principle = self.PRINCIPLES.get(principle_number)
        if not principle:
            raise ValueError(f"Invalid principle: {principle_number}")

        # Assess against principle
        compliance = self._assess_against_principle(
            principle_number, activity, evidence
        )

        return {
            "principle": principle_number,
            "description": principle,
            "activity": activity,
            "compliant": compliance["compliant"],
            "issues": compliance.get("issues", []),
            "evidence_reviewed": list(evidence.keys()),
            "assessed_at": datetime.utcnow().isoformat()
        }
```

## Systems and Controls (SYSC)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ControlTest:
    """Record of control testing"""
    control_id: str
    control_name: str
    test_type: str
    result: str  # passed, failed, partial
    issues: list[str]
    tested_at: datetime

class SYSCCompliance:
    """
    FCA Systems and Controls requirements (SYSC)

    Governance, risk management, and operational resilience
    """

    def compliance_check(
        self,
        area: str
    ) -> dict:
        """
        Perform compliance check for SYSC requirements

        SYSC 4 - General organisational requirements
        """
        checks = {
            "governance": self._check_governance(),
            "risk_management": self._check_risk_management(),
            "internal_controls": self._check_internal_controls(),
            "compliance_function": self._check_compliance_function(),
            "internal_audit": self._check_internal_audit()
        }

        if area in checks:
            return checks[area]
        return checks

    def risk_assessment(
        self,
        risk_category: str,
        business_area: str
    ) -> dict:
        """
        Conduct risk assessment

        SYSC 4.1.1R - Robust governance arrangements
        """
        # Identify risks
        risks = self._identify_risks(risk_category, business_area)

        # Assess each risk
        assessed_risks = []
        for risk in risks:
            assessment = {
                "risk_id": risk["id"],
                "description": risk["description"],
                "likelihood": self._assess_likelihood(risk),
                "impact": self._assess_impact(risk),
                "controls": self._identify_controls(risk),
                "residual_risk": self._calculate_residual(risk)
            }
            assessed_risks.append(assessment)

        return {
            "risk_category": risk_category,
            "business_area": business_area,
            "risks_identified": len(assessed_risks),
            "high_risks": len([r for r in assessed_risks if r["residual_risk"] == "high"]),
            "risks": assessed_risks,
            "assessed_at": datetime.utcnow().isoformat()
        }

    def control_testing(
        self,
        control_id: str
    ) -> ControlTest:
        """
        Test effectiveness of control

        SYSC 4.1.1R - Effective processes
        """
        control = self._get_control(control_id)

        # Perform test
        test_result = self._execute_control_test(control)

        return ControlTest(
            control_id=control_id,
            control_name=control["name"],
            test_type=test_result["test_type"],
            result=test_result["result"],
            issues=test_result.get("issues", []),
            tested_at=datetime.utcnow()
        )

    def audit_log(
        self,
        event_type: str,
        details: dict,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create audit log entry

        SYSC 9 - Record-keeping requirements
        """
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "user_id": user_id,
            "system": "fintech_platform"
        }

        # Store audit log
        self._store_audit_log(log_entry)

        return log_entry

    def record_transaction(
        self,
        transaction_id: str,
        transaction_type: str,
        details: dict
    ) -> dict:
        """
        Record transaction for audit purposes

        SYSC 9.1 - 5-year minimum retention
        """
        record = {
            "record_id": self._generate_record_id(),
            "transaction_id": transaction_id,
            "transaction_type": transaction_type,
            "details": details,
            "recorded_at": datetime.utcnow().isoformat(),
            "retention_until": self._calculate_retention_date(5)  # 5 years
        }

        self._store_transaction_record(record)

        return record

    def create_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None
    ) -> dict:
        """
        Create comprehensive audit trail

        For regulatory inquiries and investigations
        """
        audit_entry = {
            "audit_id": self._generate_audit_id(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "before_state": before_state,
            "after_state": after_state,
            "timestamp": datetime.utcnow().isoformat(),
            "user": self._get_current_user(),
            "ip_address": self._get_client_ip()
        }

        self._store_audit_trail(audit_entry)

        return audit_entry
```

## Conduct of Business (COBS)

```python
class COBSCompliance:
    """
    FCA Conduct of Business Sourcebook (COBS)

    Requirements for conduct with customers
    """

    def check_communication_compliance(
        self,
        communication: str,
        communication_type: str,
        target_audience: str
    ) -> dict:
        """
        Check communication compliance

        COBS 4.2 - Fair, clear and not misleading
        """
        issues = []

        # Check for clarity
        readability_score = self._assess_readability(communication)
        if readability_score < 60:  # Flesch reading ease
            issues.append("Communication may be too complex for target audience")

        # Check for misleading content
        misleading_check = self._check_misleading(communication)
        if misleading_check["potentially_misleading"]:
            issues.extend(misleading_check["concerns"])

        # Check required disclosures
        disclosures = self._check_required_disclosures(
            communication_type, communication
        )
        if disclosures["missing"]:
            issues.append(f"Missing required disclosures: {disclosures['missing']}")

        return {
            "communication_type": communication_type,
            "target_audience": target_audience,
            "readability_score": readability_score,
            "compliant": len(issues) == 0,
            "issues": issues,
            "assessed_at": datetime.utcnow().isoformat()
        }

    def assess_appropriateness(
        self,
        customer_id: str,
        product_id: str
    ) -> dict:
        """
        Assess product appropriateness for customer

        COBS 10 - Appropriateness for non-advised services
        """
        # Get customer knowledge and experience
        customer_profile = self._get_customer_profile(customer_id)

        # Get product complexity
        product_info = self._get_product_info(product_id)

        # Assess appropriateness
        is_appropriate = self._assess_appropriateness_match(
            customer_profile, product_info
        )

        return {
            "customer_id": customer_id,
            "product_id": product_id,
            "customer_experience_level": customer_profile["experience_level"],
            "product_complexity": product_info["complexity"],
            "is_appropriate": is_appropriate,
            "warnings_required": not is_appropriate,
            "assessed_at": datetime.utcnow().isoformat()
        }

    def suitability_check(
        self,
        customer_id: str,
        recommendation: dict
    ) -> dict:
        """
        Check suitability of recommendation

        COBS 9 - Suitability for advised services
        """
        # Get customer objectives and circumstances
        customer_data = self._get_customer_suitability_data(customer_id)

        # Assess suitability
        suitability = self._assess_suitability(
            customer_data, recommendation
        )

        return {
            "customer_id": customer_id,
            "recommendation": recommendation,
            "financial_objectives_met": suitability["objectives"],
            "risk_appropriate": suitability["risk"],
            "affordable": suitability["affordability"],
            "is_suitable": all([
                suitability["objectives"],
                suitability["risk"],
                suitability["affordability"]
            ]),
            "assessed_at": datetime.utcnow().isoformat()
        }

    def customer_assessment(
        self,
        customer_id: str,
        assessment_type: str = "full"
    ) -> dict:
        """
        Conduct customer assessment

        For appropriateness or suitability determinations
        """
        assessment = {
            "customer_id": customer_id,
            "assessment_type": assessment_type,
            "knowledge_experience": self._assess_knowledge(customer_id),
            "financial_situation": self._assess_financial(customer_id),
            "investment_objectives": self._assess_objectives(customer_id),
            "risk_tolerance": self._assess_risk_tolerance(customer_id),
            "assessed_at": datetime.utcnow().isoformat()
        }

        return assessment
```

## Regulatory Reporting (SUP 16)

```python
class FCAReporting:
    """
    FCA Regulatory Reporting requirements (SUP 16)
    """

    def generate_reg_report(
        self,
        report_type: str,
        period_end: datetime
    ) -> dict:
        """
        Generate regulatory report for FCA

        SUP 16 - Reporting requirements
        """
        if report_type == "financial_return":
            data = self._generate_financial_return(period_end)
        elif report_type == "complaints_return":
            data = self._generate_complaints_return(period_end)
        elif report_type == "transaction_reporting":
            data = self._generate_transaction_report(period_end)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        return {
            "report_type": report_type,
            "period_end": period_end.isoformat(),
            "data": data,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "ready_for_submission"
        }

    def submit_regulatory(
        self,
        report_type: str,
        report_data: dict
    ) -> dict:
        """
        Submit regulatory return to FCA

        Via RegData or Gabriel system
        """
        # Validate report
        validation = self._validate_report(report_type, report_data)
        if not validation["valid"]:
            raise ValueError(f"Report validation failed: {validation['errors']}")

        # Submit to FCA
        submission = self._submit_to_fca(report_type, report_data)

        return {
            "report_type": report_type,
            "submission_reference": submission["reference"],
            "submitted_at": datetime.utcnow().isoformat(),
            "status": submission["status"]
        }

    def compliance_return(
        self,
        period: str
    ) -> dict:
        """
        Generate compliance monitoring return

        Annual or as requested
        """
        return {
            "period": period,
            "breaches": self._get_compliance_breaches(period),
            "complaints": self._get_complaint_summary(period),
            "training_completion": self._get_training_stats(period),
            "policy_reviews": self._get_policy_review_status(period),
            "generated_at": datetime.utcnow().isoformat()
        }
```
