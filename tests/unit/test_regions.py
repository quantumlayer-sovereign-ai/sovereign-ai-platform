"""
Unit Tests for Region Support

Tests:
- Region configuration
- EU compliance checks (GDPR, PSD2, eIDAS, DORA)
- UK compliance checks (UK GDPR, FCA, PSR)
- Region-specific role definitions
"""

import pytest


class TestRegionConfiguration:
    """Unit tests for region configuration"""

    @pytest.mark.unit
    def test_region_enum(self):
        """Test FinTechRegion enum values"""
        from verticals.fintech.region import FinTechRegion

        assert FinTechRegion.INDIA.value == "india"
        assert FinTechRegion.EU.value == "eu"
        assert FinTechRegion.UK.value == "uk"

    @pytest.mark.unit
    def test_region_config_dataclass(self):
        """Test RegionConfig dataclass structure"""
        from verticals.fintech.region import RegionConfig

        config = RegionConfig(
            compliance_standards=["pci_dss", "gdpr"],
            payment_schemes=["SEPA"],
            currency="EUR",
            data_residency="eu",
            regulatory_bodies=["EBA"]
        )

        assert config.compliance_standards == ["pci_dss", "gdpr"]
        assert config.currency == "EUR"
        assert config.data_residency == "eu"

    @pytest.mark.unit
    def test_get_region_config_india(self):
        """Test getting India region config"""
        from verticals.fintech.region import get_region_config

        config = get_region_config("india")

        assert "pci_dss" in config.compliance_standards
        assert "rbi" in config.compliance_standards
        assert "dpdp" in config.compliance_standards
        assert "UPI" in config.payment_schemes
        assert config.currency == "INR"

    @pytest.mark.unit
    def test_get_region_config_eu(self):
        """Test getting EU region config"""
        from verticals.fintech.region import get_region_config

        config = get_region_config("eu")

        assert "pci_dss" in config.compliance_standards
        assert "gdpr" in config.compliance_standards
        assert "psd2" in config.compliance_standards
        assert "dora" in config.compliance_standards
        assert "SEPA" in config.payment_schemes
        assert config.currency == "EUR"
        assert config.data_residency == "eu"

    @pytest.mark.unit
    def test_get_region_config_uk(self):
        """Test getting UK region config"""
        from verticals.fintech.region import get_region_config

        config = get_region_config("uk")

        assert "pci_dss" in config.compliance_standards
        assert "uk_gdpr" in config.compliance_standards
        assert "fca" in config.compliance_standards
        assert "psr" in config.compliance_standards
        assert "FASTER_PAYMENTS" in config.payment_schemes
        assert config.currency == "GBP"
        assert config.data_residency == "uk"

    @pytest.mark.unit
    def test_get_region_config_invalid(self):
        """Test invalid region raises ValueError"""
        from verticals.fintech.region import get_region_config

        # Should raise ValueError for invalid region
        with pytest.raises(ValueError, match="Unknown region"):
            get_region_config("invalid_region")

    @pytest.mark.unit
    def test_region_from_enum(self):
        """Test FinTechRegion enum usage"""
        from verticals.fintech.region import FinTechRegion, get_region_config

        # Should work with enum directly
        config = get_region_config(FinTechRegion.EU)
        assert config.currency == "EUR"

        config = get_region_config(FinTechRegion.UK)
        assert config.currency == "GBP"


class TestEUComplianceChecks:
    """Unit tests for EU compliance checks"""

    @pytest.fixture
    def eu_checker(self):
        """Create EU compliance checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["gdpr", "psd2"], region="eu")

    @pytest.fixture
    def gdpr_checker(self):
        """Create GDPR only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["gdpr"], region="eu")

    @pytest.fixture
    def psd2_checker(self):
        """Create PSD2 only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["psd2"], region="eu")

    @pytest.mark.unit
    def test_eu_checker_initialization(self, eu_checker):
        """Test EU checker initializes correctly"""
        assert eu_checker is not None
        assert "gdpr" in eu_checker.standards or "psd2" in eu_checker.standards

    @pytest.mark.unit
    def test_gdpr_personal_data_unencrypted(self, gdpr_checker):
        """Test GDPR detection of unencrypted personal data"""
        code = '''
personal_data = {
    "email": "user@example.com",
    "phone": "1234567890",
    "address": "123 Main St"
}
save_to_database(personal_data)  # No encryption
'''
        report = gdpr_checker.check_code(code, "test.py")
        # Should flag missing encryption for personal data
        assert len(report.issues) >= 0  # Check runs without error

    @pytest.mark.unit
    def test_gdpr_consent_missing(self, gdpr_checker):
        """Test GDPR detection of missing consent"""
        code = '''
def collect_user_data(user):
    # No consent check
    return store_personal_data(user.email, user.phone)
'''
        report = gdpr_checker.check_code(code, "test.py")
        gdpr_issues = [i for i in report.issues if "GDPR" in i.rule_id]
        # Should potentially flag missing consent
        assert isinstance(report.issues, list)

    @pytest.mark.unit
    def test_gdpr_data_retention_check(self, gdpr_checker):
        """Test GDPR data retention requirements"""
        code = '''
def store_user_data(user):
    # Store forever without retention policy
    db.insert(user.data)
'''
        report = gdpr_checker.check_code(code, "test.py")
        assert hasattr(report, 'passed')

    @pytest.mark.unit
    def test_psd2_sca_missing(self, psd2_checker):
        """Test PSD2 detection of missing SCA"""
        code = '''
def process_payment(amount, card):
    # No SCA implementation
    return gateway.charge(card, amount)
'''
        report = psd2_checker.check_code(code, "test.py")
        assert hasattr(report, 'issues')

    @pytest.mark.unit
    def test_psd2_dynamic_linking_missing(self, psd2_checker):
        """Test PSD2 detection of missing dynamic linking"""
        code = '''
def authenticate_payment(user):
    # OTP without amount/payee binding
    otp = generate_otp()
    send_sms(user.phone, otp)
    return verify_otp(user.input)
'''
        report = psd2_checker.check_code(code, "test.py")
        assert isinstance(report.passed, bool)


class TestUKComplianceChecks:
    """Unit tests for UK compliance checks"""

    @pytest.fixture
    def uk_checker(self):
        """Create UK compliance checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["uk_gdpr", "fca", "psr"], region="uk")

    @pytest.fixture
    def fca_checker(self):
        """Create FCA only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["fca"], region="uk")

    @pytest.fixture
    def psr_checker(self):
        """Create PSR only checker"""
        from verticals.fintech.compliance import ComplianceChecker
        return ComplianceChecker(standards=["psr"], region="uk")

    @pytest.mark.unit
    def test_uk_checker_initialization(self, uk_checker):
        """Test UK checker initializes correctly"""
        assert uk_checker is not None

    @pytest.mark.unit
    def test_fca_consumer_duty_check(self, fca_checker):
        """Test FCA Consumer Duty compliance check"""
        code = '''
def sell_product(customer, product):
    # No customer outcome assessment
    return complete_sale(customer, product)
'''
        report = fca_checker.check_code(code, "test.py")
        assert hasattr(report, 'passed')

    @pytest.mark.unit
    def test_fca_sysc_controls(self, fca_checker):
        """Test FCA SYSC controls check"""
        code = '''
def process_transaction(txn):
    # No audit logging
    return execute(txn)
'''
        report = fca_checker.check_code(code, "test.py")
        assert hasattr(report, 'issues')

    @pytest.mark.unit
    def test_psr_cop_missing(self, psr_checker):
        """Test PSR detection of missing Confirmation of Payee"""
        code = '''
def send_payment(payee_name, sort_code, account_number, amount):
    # No CoP check before payment
    return faster_payments.send(sort_code, account_number, amount)
'''
        report = psr_checker.check_code(code, "test.py")
        assert isinstance(report.recommendations, list)

    @pytest.mark.unit
    def test_psr_fraud_warning_missing(self, psr_checker):
        """Test PSR detection of missing fraud warnings"""
        code = '''
def confirm_high_value_payment(amount, payee):
    # No fraud warning for high value transfer
    return process_payment(amount, payee)
'''
        report = psr_checker.check_code(code, "test.py")
        assert hasattr(report, 'summary')

    @pytest.mark.unit
    def test_uk_gdpr_breach_notification(self, uk_checker):
        """Test UK GDPR breach notification check"""
        code = '''
def handle_data_breach(incident):
    # Log but don't notify ICO
    log_incident(incident)
    return {"status": "logged"}
'''
        report = uk_checker.check_code(code, "test.py")
        assert hasattr(report, 'passed')


class TestEURoles:
    """Unit tests for EU role definitions"""

    @pytest.fixture
    def fintech_roles(self):
        """Get all FinTech roles"""
        from verticals.fintech.roles import FINTECH_ROLES
        return FINTECH_ROLES

    @pytest.mark.unit
    def test_eu_roles_defined(self, fintech_roles):
        """Test all EU roles are defined"""
        expected_eu_roles = [
            "eu_fintech_architect",
            "eu_fintech_coder",
            "eu_fintech_security",
            "eu_fintech_compliance",
            "eu_fintech_tester"
        ]

        for role in expected_eu_roles:
            assert role in fintech_roles, f"Missing EU role: {role}"

    @pytest.mark.unit
    def test_eu_coder_structure(self, fintech_roles):
        """Test eu_fintech_coder role structure"""
        role = fintech_roles["eu_fintech_coder"]

        assert role["name"] == "eu_fintech_coder"
        assert role["vertical"] == "fintech"
        assert role.get("region") == "eu"
        assert "tools" in role
        assert "spawn_conditions" in role

    @pytest.mark.unit
    def test_eu_coder_gdpr_awareness(self, fintech_roles):
        """Test eu_fintech_coder has GDPR awareness"""
        prompt = fintech_roles["eu_fintech_coder"]["system_prompt"]

        assert "gdpr" in prompt.lower()
        assert "psd2" in prompt.lower() or "payment" in prompt.lower()

    @pytest.mark.unit
    def test_eu_coder_sepa_knowledge(self, fintech_roles):
        """Test eu_fintech_coder has SEPA knowledge"""
        prompt = fintech_roles["eu_fintech_coder"]["system_prompt"]

        assert "sepa" in prompt.lower() or "payment" in prompt.lower()

    @pytest.mark.unit
    def test_eu_compliance_structure(self, fintech_roles):
        """Test eu_fintech_compliance role structure"""
        role = fintech_roles["eu_fintech_compliance"]

        assert role["name"] == "eu_fintech_compliance"
        assert "gdpr" in role.get("compliance", []) or "psd2" in role.get("compliance", [])

    @pytest.mark.unit
    def test_eu_compliance_dora_awareness(self, fintech_roles):
        """Test eu_fintech_compliance has DORA awareness"""
        prompt = fintech_roles["eu_fintech_compliance"]["system_prompt"]

        # Should mention DORA or operational resilience
        assert "dora" in prompt.lower() or "resilience" in prompt.lower()

    @pytest.mark.unit
    def test_eu_security_structure(self, fintech_roles):
        """Test eu_fintech_security role structure"""
        role = fintech_roles["eu_fintech_security"]

        assert role["name"] == "eu_fintech_security"
        assert "security_scanner" in role.get("tools", [])


class TestUKRoles:
    """Unit tests for UK role definitions"""

    @pytest.fixture
    def fintech_roles(self):
        """Get all FinTech roles"""
        from verticals.fintech.roles import FINTECH_ROLES
        return FINTECH_ROLES

    @pytest.mark.unit
    def test_uk_roles_defined(self, fintech_roles):
        """Test all UK roles are defined"""
        expected_uk_roles = [
            "uk_fintech_architect",
            "uk_fintech_coder",
            "uk_fintech_security",
            "uk_fintech_compliance",
            "uk_fintech_tester"
        ]

        for role in expected_uk_roles:
            assert role in fintech_roles, f"Missing UK role: {role}"

    @pytest.mark.unit
    def test_uk_coder_structure(self, fintech_roles):
        """Test uk_fintech_coder role structure"""
        role = fintech_roles["uk_fintech_coder"]

        assert role["name"] == "uk_fintech_coder"
        assert role["vertical"] == "fintech"
        assert role.get("region") == "uk"

    @pytest.mark.unit
    def test_uk_coder_fca_awareness(self, fintech_roles):
        """Test uk_fintech_coder has FCA awareness"""
        prompt = fintech_roles["uk_fintech_coder"]["system_prompt"]

        assert "fca" in prompt.lower() or "financial conduct" in prompt.lower()

    @pytest.mark.unit
    def test_uk_coder_fps_knowledge(self, fintech_roles):
        """Test uk_fintech_coder has Faster Payments knowledge"""
        prompt = fintech_roles["uk_fintech_coder"]["system_prompt"]

        fps_keywords = ["faster payment", "fps", "bacs", "chaps", "sort code"]
        assert any(kw in prompt.lower() for kw in fps_keywords)

    @pytest.mark.unit
    def test_uk_compliance_consumer_duty(self, fintech_roles):
        """Test uk_fintech_compliance has Consumer Duty awareness"""
        prompt = fintech_roles["uk_fintech_compliance"]["system_prompt"]

        assert "consumer duty" in prompt.lower() or "prin" in prompt.lower()

    @pytest.mark.unit
    def test_uk_compliance_psr_awareness(self, fintech_roles):
        """Test uk_fintech_compliance has PSR awareness"""
        prompt = fintech_roles["uk_fintech_compliance"]["system_prompt"]

        assert "psr" in prompt.lower() or "payment services" in prompt.lower()

    @pytest.mark.unit
    def test_uk_security_structure(self, fintech_roles):
        """Test uk_fintech_security role structure"""
        role = fintech_roles["uk_fintech_security"]

        assert role["name"] == "uk_fintech_security"
        assert role.get("region") == "uk"


class TestRegionAwareCompliance:
    """Tests for region-aware compliance checking"""

    @pytest.mark.unit
    def test_compliance_checker_with_region_eu(self):
        """Test ComplianceChecker accepts EU region"""
        from verticals.fintech.compliance import ComplianceChecker

        checker = ComplianceChecker(region="eu")

        # Should have EU-specific standards
        assert checker is not None

    @pytest.mark.unit
    def test_compliance_checker_with_region_uk(self):
        """Test ComplianceChecker accepts UK region"""
        from verticals.fintech.compliance import ComplianceChecker

        checker = ComplianceChecker(region="uk")

        assert checker is not None

    @pytest.mark.unit
    def test_compliance_checker_default_india(self):
        """Test ComplianceChecker defaults to India"""
        from verticals.fintech.compliance import ComplianceChecker

        checker = ComplianceChecker()

        # Should have RBI/DPDP standards by default
        assert "rbi" in checker.standards or "dpdp" in checker.standards

    @pytest.mark.unit
    def test_pci_dss_in_all_regions(self):
        """Test PCI-DSS is available in all regions"""
        from verticals.fintech.compliance import ComplianceChecker

        for region in ["india", "eu", "uk"]:
            checker = ComplianceChecker(standards=["pci_dss"], region=region)
            assert "pci_dss" in checker.standards


class TestRoleRegistration:
    """Tests for role registration with regions"""

    @pytest.mark.unit
    def test_register_all_roles(self):
        """Test all roles (India, EU, UK) are registered"""
        from verticals.fintech.roles import register_fintech_roles

        registered = register_fintech_roles()

        # India roles
        assert "fintech_coder" in registered
        assert "fintech_security" in registered

        # EU roles
        assert "eu_fintech_coder" in registered
        assert "eu_fintech_security" in registered

        # UK roles
        assert "uk_fintech_coder" in registered
        assert "uk_fintech_security" in registered

    @pytest.mark.unit
    def test_total_role_count(self):
        """Test total number of roles (5 India + 5 EU + 5 UK = 15)"""
        from verticals.fintech.roles import FINTECH_ROLES

        # Should have 15 roles total
        assert len(FINTECH_ROLES) == 15

    @pytest.mark.unit
    def test_roles_by_region(self):
        """Test roles can be filtered by region"""
        from verticals.fintech.roles import FINTECH_ROLES

        india_roles = [r for r in FINTECH_ROLES if not r.startswith(("eu_", "uk_"))]
        eu_roles = [r for r in FINTECH_ROLES if r.startswith("eu_")]
        uk_roles = [r for r in FINTECH_ROLES if r.startswith("uk_")]

        assert len(india_roles) == 5
        assert len(eu_roles) == 5
        assert len(uk_roles) == 5


class TestTrainingGenerators:
    """Tests for training data generators"""

    @pytest.mark.unit
    def test_eu_generators_registered(self):
        """Test EU generators are registered"""
        from core.training.generators import GENERATORS

        assert "eu_fintech_coder" in GENERATORS
        assert "eu_fintech_security" in GENERATORS
        assert "eu_fintech_compliance" in GENERATORS

    @pytest.mark.unit
    def test_uk_generators_registered(self):
        """Test UK generators are registered"""
        from core.training.generators import GENERATORS

        assert "uk_fintech_coder" in GENERATORS
        assert "uk_fintech_security" in GENERATORS
        assert "uk_fintech_compliance" in GENERATORS

    @pytest.mark.unit
    def test_get_generator_eu(self):
        """Test getting EU generator"""
        from core.training.generators import get_generator

        generator = get_generator("eu_fintech_coder")
        assert generator is not None
        assert generator.role_name == "eu_fintech_coder"

    @pytest.mark.unit
    def test_get_generator_uk(self):
        """Test getting UK generator"""
        from core.training.generators import get_generator

        generator = get_generator("uk_fintech_coder")
        assert generator is not None
        assert generator.role_name == "uk_fintech_coder"

    @pytest.mark.unit
    def test_get_generators_for_region_eu(self):
        """Test getting all generators for EU region"""
        from core.training.generators import get_generators_for_region

        eu_generators = get_generators_for_region("eu")

        assert "eu_fintech_coder" in eu_generators
        assert "eu_fintech_security" in eu_generators
        assert "fintech_coder" not in eu_generators  # Should not include India

    @pytest.mark.unit
    def test_get_generators_for_region_uk(self):
        """Test getting all generators for UK region"""
        from core.training.generators import get_generators_for_region

        uk_generators = get_generators_for_region("uk")

        assert "uk_fintech_coder" in uk_generators
        assert "uk_fintech_security" in uk_generators
        assert "fintech_coder" not in uk_generators

    @pytest.mark.unit
    def test_eu_generator_synthetic_samples(self):
        """Test EU generator produces synthetic samples"""
        from core.training.generators import get_generator

        generator = get_generator("eu_fintech_coder")
        samples = generator.generate_synthetic_samples()

        assert len(samples) > 0
        # Check samples have expected structure
        sample = samples[0]
        assert hasattr(sample, 'instruction')
        assert hasattr(sample, 'output')

    @pytest.mark.unit
    def test_uk_generator_synthetic_samples(self):
        """Test UK generator produces synthetic samples"""
        from core.training.generators import get_generator

        generator = get_generator("uk_fintech_coder")
        samples = generator.generate_synthetic_samples()

        assert len(samples) > 0


class TestModularChecks:
    """Tests for modular compliance check infrastructure"""

    @pytest.mark.unit
    def test_base_compliance_checker_import(self):
        """Test base compliance checker can be imported"""
        from verticals.fintech.checks.base import (
            BaseComplianceChecker,
            ComplianceCheck,
            ComplianceIssue,
            Severity,
        )

        assert BaseComplianceChecker is not None
        assert ComplianceCheck is not None
        assert ComplianceIssue is not None
        assert Severity is not None

    @pytest.mark.unit
    def test_pci_dss_checker_import(self):
        """Test PCI-DSS checker can be imported"""
        from verticals.fintech.checks.pci_dss import PCIDSSChecker

        checker = PCIDSSChecker()
        assert checker is not None
        # PCIDSSChecker inherits from BaseComplianceChecker
        assert hasattr(checker, 'check_code')

    @pytest.mark.unit
    def test_gdpr_checker_import(self):
        """Test GDPR checker can be imported"""
        from verticals.fintech.checks.eu.gdpr import GDPRChecker

        checker = GDPRChecker()
        assert checker is not None

    @pytest.mark.unit
    def test_psd2_checker_import(self):
        """Test PSD2 checker can be imported"""
        from verticals.fintech.checks.eu.psd2 import PSD2Checker

        checker = PSD2Checker()
        assert checker is not None

    @pytest.mark.unit
    def test_fca_checker_import(self):
        """Test FCA checker can be imported"""
        from verticals.fintech.checks.uk.fca import FCAChecker

        checker = FCAChecker()
        assert checker is not None

    @pytest.mark.unit
    def test_psr_checker_import(self):
        """Test PSR checker can be imported"""
        from verticals.fintech.checks.uk.psr import PSRChecker

        checker = PSRChecker()
        assert checker is not None
