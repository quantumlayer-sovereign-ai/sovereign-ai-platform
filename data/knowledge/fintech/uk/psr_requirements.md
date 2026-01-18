# PSR Requirements for UK FinTech

## Overview

The Payment Systems Regulator (PSR) regulates payment systems in the UK, focusing on competition, innovation, and protecting payment system users. Key requirements include APP fraud reimbursement, Confirmation of Payee, and access to payment systems.

## APP Fraud Reimbursement

Authorised Push Payment (APP) fraud is when customers are tricked into authorising payments to fraudsters. New PSR rules require mandatory reimbursement.

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
import structlog

logger = structlog.get_logger()

class APPFraudType(Enum):
    PURCHASE_SCAM = "purchase_scam"
    INVESTMENT_SCAM = "investment_scam"
    ROMANCE_SCAM = "romance_scam"
    IMPERSONATION = "impersonation"
    INVOICE_FRAUD = "invoice_fraud"
    CEO_FRAUD = "ceo_fraud"

@dataclass
class APPFraudClaim:
    """APP fraud reimbursement claim"""
    claim_id: str
    customer_id: str
    transaction_id: str
    amount: Decimal
    fraud_type: APPFraudType
    reported_at: datetime
    sending_psp: str
    receiving_psp: str
    reimbursement_status: str = "pending"

class APPFraudReimbursement:
    """
    PSR APP Fraud Reimbursement requirements

    Mandatory reimbursement with 50/50 split between sending and receiving PSPs
    """

    MAX_REIMBURSEMENT = Decimal("415000")  # Maximum claim limit
    REIMBURSEMENT_DEADLINE_DAYS = 5  # Must reimburse within 5 business days

    async def detect_app_fraud(
        self,
        transaction_id: str,
        customer_report: dict
    ) -> APPFraudClaim:
        """
        Detect and record APP fraud claim

        Start reimbursement process
        """
        transaction = await self._get_transaction(transaction_id)

        # Classify fraud type
        fraud_type = self._classify_fraud_type(customer_report)

        claim = APPFraudClaim(
            claim_id=self._generate_claim_id(),
            customer_id=transaction["customer_id"],
            transaction_id=transaction_id,
            amount=Decimal(str(transaction["amount"])),
            fraud_type=fraud_type,
            reported_at=datetime.utcnow(),
            sending_psp=self.psp_id,
            receiving_psp=transaction["receiving_psp"]
        )

        logger.info(
            "app_fraud_claim_created",
            claim_id=claim.claim_id,
            amount=str(claim.amount),
            fraud_type=fraud_type.value
        )

        return claim

    async def reimburse_fraud_victim(
        self,
        claim: APPFraudClaim
    ) -> dict:
        """
        Reimburse APP fraud victim

        Must reimburse within 5 business days unless exception applies
        """
        # Check for gross negligence exception
        exception = await self._check_exceptions(claim)
        if exception["applies"]:
            claim.reimbursement_status = "exception_applied"
            return {
                "claim_id": claim.claim_id,
                "reimbursed": False,
                "reason": exception["reason"],
                "customer_action": exception.get("customer_action")
            }

        # Calculate reimbursement amount
        reimbursement_amount = min(claim.amount, self.MAX_REIMBURSEMENT)

        # 50/50 split between sending and receiving PSP
        sending_share = reimbursement_amount / 2
        receiving_share = reimbursement_amount / 2

        # Process reimbursement
        await self._process_reimbursement(claim.customer_id, reimbursement_amount)

        # Claim from receiving PSP
        await self._claim_from_receiving_psp(
            claim.receiving_psp,
            receiving_share,
            claim.claim_id
        )

        claim.reimbursement_status = "completed"

        logger.info(
            "app_fraud_reimbursed",
            claim_id=claim.claim_id,
            amount=str(reimbursement_amount),
            sending_share=str(sending_share),
            receiving_share=str(receiving_share)
        )

        return {
            "claim_id": claim.claim_id,
            "reimbursed": True,
            "amount": str(reimbursement_amount),
            "reimbursed_at": datetime.utcnow().isoformat()
        }

    async def app_fraud_check(
        self,
        transaction: dict
    ) -> dict:
        """
        Check transaction for APP fraud indicators

        Pre-payment warning system
        """
        indicators = []

        # Check payee risk
        payee_risk = await self._check_payee_risk(transaction["payee_account"])
        if payee_risk["high_risk"]:
            indicators.append("high_risk_payee")

        # Check unusual patterns
        pattern_check = await self._check_unusual_patterns(
            transaction["customer_id"],
            transaction
        )
        if pattern_check["unusual"]:
            indicators.extend(pattern_check["indicators"])

        # Check for known fraud patterns
        fraud_patterns = await self._check_fraud_patterns(transaction)
        if fraud_patterns["matches"]:
            indicators.extend(fraud_patterns["patterns"])

        risk_score = len(indicators) / 10  # Simple scoring

        return {
            "transaction_id": transaction["id"],
            "risk_score": risk_score,
            "indicators": indicators,
            "warning_required": risk_score > 0.3,
            "block_recommended": risk_score > 0.7
        }


class APPFraudPrevention:
    """
    APP fraud prevention measures

    Required controls to reduce fraud
    """

    async def fraud_warning(
        self,
        transaction: dict,
        risk_assessment: dict
    ) -> dict:
        """
        Display fraud warning to customer

        Effective warnings required by PSR
        """
        warning_level = self._determine_warning_level(risk_assessment)

        if warning_level == "none":
            return {"warning_shown": False}

        warning_content = self._generate_warning(
            warning_level,
            risk_assessment["indicators"]
        )

        return {
            "warning_shown": True,
            "warning_level": warning_level,
            "warning_content": warning_content,
            "confirmation_required": warning_level in ["high", "critical"],
            "cooling_off_seconds": 60 if warning_level == "critical" else 0
        }

    def transaction_monitoring(
        self,
        customer_id: str,
        transaction: dict
    ) -> dict:
        """
        Real-time transaction monitoring

        Behavioral analytics for fraud detection
        """
        # Check velocity
        velocity = self._check_velocity(customer_id)

        # Check amount patterns
        amount_check = self._check_amount_patterns(
            customer_id,
            transaction["amount"]
        )

        # Check payee patterns
        payee_check = self._check_payee_patterns(
            customer_id,
            transaction["payee_account"]
        )

        # Check device/session
        device_check = self._check_device_session(transaction)

        alerts = []
        if velocity["unusual"]:
            alerts.append("unusual_velocity")
        if amount_check["unusual"]:
            alerts.append("unusual_amount")
        if payee_check["new_payee"] and transaction["amount"] > 1000:
            alerts.append("high_value_new_payee")
        if device_check["new_device"]:
            alerts.append("new_device")

        return {
            "customer_id": customer_id,
            "alerts": alerts,
            "risk_level": "high" if len(alerts) >= 2 else "medium" if alerts else "low",
            "additional_auth_required": len(alerts) >= 2
        }
```

## Confirmation of Payee (CoP)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CoPResult(Enum):
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    NOT_AVAILABLE = "not_available"
    OPTED_OUT = "opted_out"

@dataclass
class CoPCheck:
    """Confirmation of Payee check result"""
    check_id: str
    account_name_provided: str
    account_number: str
    sort_code: str
    result: CoPResult
    actual_name: Optional[str] = None
    match_score: float = 0.0

class ConfirmationOfPayee:
    """
    PSR Confirmation of Payee requirements

    Specific Direction 10 - Check payee name before payment
    """

    MATCH_THRESHOLD = 0.95
    PARTIAL_MATCH_THRESHOLD = 0.70

    async def confirm_payee(
        self,
        account_name: str,
        account_number: str,
        sort_code: str
    ) -> CoPCheck:
        """
        Check if payee name matches account holder

        Returns match, partial match, or no match
        """
        check_id = self._generate_check_id()

        # Query receiving bank
        response = await self._query_receiving_bank(
            account_number,
            sort_code,
            account_name
        )

        if response["status"] == "opted_out":
            return CoPCheck(
                check_id=check_id,
                account_name_provided=account_name,
                account_number=account_number,
                sort_code=sort_code,
                result=CoPResult.OPTED_OUT
            )

        if response["status"] == "not_available":
            return CoPCheck(
                check_id=check_id,
                account_name_provided=account_name,
                account_number=account_number,
                sort_code=sort_code,
                result=CoPResult.NOT_AVAILABLE
            )

        # Calculate match score
        match_score = self._calculate_name_match(
            account_name,
            response["actual_name"]
        )

        if match_score >= self.MATCH_THRESHOLD:
            result = CoPResult.MATCH
        elif match_score >= self.PARTIAL_MATCH_THRESHOLD:
            result = CoPResult.PARTIAL_MATCH
        else:
            result = CoPResult.NO_MATCH

        return CoPCheck(
            check_id=check_id,
            account_name_provided=account_name,
            account_number=account_number,
            sort_code=sort_code,
            result=result,
            actual_name=response["actual_name"] if result != CoPResult.MATCH else None,
            match_score=match_score
        )

    async def verify_account_name(
        self,
        account_name: str,
        account_number: str,
        sort_code: str
    ) -> dict:
        """
        Verify account name before payment

        Main entry point for CoP check
        """
        cop_check = await self.confirm_payee(
            account_name,
            account_number,
            sort_code
        )

        return {
            "check_id": cop_check.check_id,
            "result": cop_check.result.value,
            "match_score": cop_check.match_score,
            "actual_name": cop_check.actual_name,
            "proceed_allowed": cop_check.result in [
                CoPResult.MATCH,
                CoPResult.PARTIAL_MATCH,
                CoPResult.NOT_AVAILABLE
            ],
            "warning_required": cop_check.result in [
                CoPResult.PARTIAL_MATCH,
                CoPResult.NO_MATCH
            ]
        }

    def cop_check(
        self,
        cop_result: CoPCheck
    ) -> dict:
        """
        Process CoP check result for payment flow
        """
        if cop_result.result == CoPResult.MATCH:
            return {
                "action": "proceed",
                "message": "Name matches account holder"
            }
        elif cop_result.result == CoPResult.PARTIAL_MATCH:
            return {
                "action": "warn",
                "message": f"The name is similar to the account holder name. Did you mean: {cop_result.actual_name}?",
                "confirmation_required": True
            }
        elif cop_result.result == CoPResult.NO_MATCH:
            return {
                "action": "warn_strong",
                "message": f"The name does not match. The account holder name is: {cop_result.actual_name}",
                "confirmation_required": True,
                "fraud_warning": True
            }
        elif cop_result.result == CoPResult.NOT_AVAILABLE:
            return {
                "action": "proceed_with_caution",
                "message": "We couldn't verify the name. Please make sure the details are correct.",
                "confirmation_required": True
            }
        else:
            return {
                "action": "proceed",
                "message": "Account holder has opted out of name checking"
            }

    async def handle_cop_result(
        self,
        cop_check: CoPCheck,
        user_action: str
    ) -> dict:
        """
        Handle user action after CoP warning

        Log user override decisions
        """
        if cop_check.result == CoPResult.MATCH:
            return {"proceed": True, "logged": False}

        # Log the decision for fraud analysis
        await self._log_cop_decision(
            check_id=cop_check.check_id,
            result=cop_check.result.value,
            user_action=user_action,
            actual_name=cop_check.actual_name
        )

        return {
            "proceed": user_action == "continue",
            "logged": True,
            "liability_acknowledged": user_action == "continue"
        }

    def show_cop_warning(
        self,
        cop_result: CoPCheck
    ) -> dict:
        """
        Generate user-facing CoP warning

        Clear, effective warnings as required by PSR
        """
        if cop_result.result == CoPResult.PARTIAL_MATCH:
            return {
                "title": "The name doesn't quite match",
                "message": f"You entered: {cop_result.account_name_provided}\nThe account holder's name is: {cop_result.actual_name}",
                "severity": "warning",
                "options": [
                    {"action": "amend", "label": "Edit payee details"},
                    {"action": "continue", "label": "Continue anyway"}
                ]
            }
        elif cop_result.result == CoPResult.NO_MATCH:
            return {
                "title": "Warning: Name does not match",
                "message": f"The name you entered ({cop_result.account_name_provided}) is different from the account holder's name ({cop_result.actual_name}). This could be a sign of fraud.",
                "severity": "critical",
                "options": [
                    {"action": "cancel", "label": "Cancel payment"},
                    {"action": "amend", "label": "Edit payee details"},
                    {"action": "continue", "label": "I'm sure, continue"}
                ]
            }
        return {"title": None, "message": None, "severity": None, "options": []}

    async def cop_override(
        self,
        check_id: str,
        reason: str
    ) -> dict:
        """
        Record user override of CoP warning

        For fraud analysis and liability
        """
        await self._record_override(check_id, reason)
        return {
            "check_id": check_id,
            "override_recorded": True,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Payment System Access

```python
class PaymentSystemAccess:
    """
    PSR Access to Payment Systems

    Fair and open access requirements
    """

    PAYMENT_SCHEMES = ["faster_payments", "bacs", "chaps"]

    async def apply_for_access(
        self,
        scheme: str,
        applicant_info: dict
    ) -> dict:
        """
        Apply for direct access to payment scheme

        PSR promotes direct access for PSPs
        """
        if scheme not in self.PAYMENT_SCHEMES:
            raise ValueError(f"Unknown scheme: {scheme}")

        # Check eligibility
        eligibility = await self._check_eligibility(scheme, applicant_info)

        if not eligibility["eligible"]:
            return {
                "status": "ineligible",
                "reason": eligibility["reason"],
                "alternative": "indirect_access"
            }

        # Submit application
        application = await self._submit_application(scheme, applicant_info)

        return {
            "status": "submitted",
            "application_id": application["id"],
            "scheme": scheme,
            "estimated_timeline": application["timeline"]
        }

    async def check_discrimination(
        self,
        decision: dict,
        applicant_type: str
    ) -> dict:
        """
        Check for discriminatory access decisions

        PSR monitors for unfair treatment
        """
        # Check if similar applicants treated differently
        comparators = await self._find_similar_applicants(applicant_type)

        analysis = {
            "decision": decision,
            "applicant_type": applicant_type,
            "comparator_decisions": comparators,
            "potential_discrimination": False,
            "factors_analyzed": ["size", "business_model", "risk_profile"]
        }

        # Check for disparate treatment
        if self._detect_disparate_treatment(decision, comparators):
            analysis["potential_discrimination"] = True
            analysis["escalate_to_psr"] = True

        return analysis
```

## PSR Reporting

```python
class PSRReporting:
    """
    PSR Reporting Requirements
    """

    async def generate_psr_report(
        self,
        report_type: str,
        period: str
    ) -> dict:
        """
        Generate report for PSR

        Fraud data, service metrics, complaints
        """
        if report_type == "fraud_data":
            return await self._generate_fraud_report(period)
        elif report_type == "service_metrics":
            return await self._generate_service_report(period)
        elif report_type == "complaints":
            return await self._generate_complaints_report(period)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    async def submit_fraud_data(
        self,
        period: str
    ) -> dict:
        """
        Submit fraud data to PSR

        Required for APP fraud monitoring
        """
        fraud_data = {
            "period": period,
            "app_fraud_cases": await self._get_app_fraud_count(period),
            "app_fraud_value": str(await self._get_app_fraud_value(period)),
            "reimbursements_made": await self._get_reimbursement_count(period),
            "reimbursement_value": str(await self._get_reimbursement_value(period)),
            "exceptions_applied": await self._get_exception_count(period),
            "cop_checks_performed": await self._get_cop_count(period),
            "cop_warnings_shown": await self._get_cop_warning_count(period),
            "cop_overrides": await self._get_cop_override_count(period)
        }

        # Submit to PSR
        submission = await self._submit_to_psr(fraud_data)

        return {
            "submitted": True,
            "reference": submission["reference"],
            "submitted_at": datetime.utcnow().isoformat()
        }

    async def service_metrics(
        self,
        period: str
    ) -> dict:
        """
        Generate service metrics

        Availability, performance, incidents
        """
        return {
            "period": period,
            "availability_percent": await self._calculate_availability(period),
            "avg_processing_time_ms": await self._calculate_avg_processing(period),
            "transaction_volume": await self._get_transaction_volume(period),
            "incidents": await self._get_incident_count(period),
            "outages": await self._get_outage_minutes(period)
        }
```
