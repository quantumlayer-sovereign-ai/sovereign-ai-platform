"""
Tester Generator - Payment Testing Training Data

Generates training samples for the fintech_tester role focusing on:
- Payment flow testing
- Security testing
- Integration testing
"""

import re
from .base import BaseGenerator, TrainingSample


class TesterGenerator(BaseGenerator):
    """Generator for fintech_tester role"""

    def __init__(self):
        super().__init__()
        self.role_name = "fintech_tester"
        self.focus_areas = ["test_generation", "payment_testing", "security_testing"]
        self.compliance_tags = ["pci_dss"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate testing-focused training samples"""
        samples = []

        # Generate test case samples from code
        samples.extend(self._generate_test_samples(content, source_file))

        # Generate security test samples
        samples.extend(self._generate_security_test_samples(content, source_file))

        # Add synthetic testing samples
        samples.extend(self.generate_payment_test_samples())

        return samples

    def _generate_test_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate test case samples from code examples"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code = block["code"]

            # Extract function definitions
            func_matches = re.findall(r"def\s+(\w+)\s*\([^)]*\)", code)

            for func_name in func_matches:
                if func_name.startswith("_"):
                    continue

                samples.append(self.create_sample(
                    instruction=f"Write comprehensive test cases for the function `{func_name}`",
                    input_text=code[:500],
                    output=self._generate_test_suite(func_name, code),
                    category="unit_test",
                    source_file=source_file
                ))

        return samples

    def _generate_security_test_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate security test samples"""
        samples = []
        sections = self.extract_sections(content)

        security_sections = [
            name for name in sections
            if any(kw in name for kw in ["security", "auth", "encrypt", "access"])
        ]

        for section_name in security_sections:
            section_content = sections[section_name]

            samples.append(self.create_sample(
                instruction=f"Create security test cases for {section_name.replace('_', ' ')}",
                input_text=section_content[:300],
                output=self._generate_security_tests(section_name),
                category="security_test",
                source_file=source_file
            ))

        return samples

    def _generate_test_suite(self, func_name: str, code: str) -> str:
        """Generate test suite for a function"""
        return f"""## Test Suite for `{func_name}`

```python
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

class Test{func_name.title().replace('_', '')}:
    \"\"\"Test cases for {func_name}\"\"\"

    @pytest.fixture
    def mock_dependencies(self):
        \"\"\"Set up mock dependencies\"\"\"
        return {{
            'db': Mock(),
            'logger': Mock(),
            'external_api': AsyncMock()
        }}

    @pytest.mark.asyncio
    async def test_{func_name}_success(self, mock_dependencies):
        \"\"\"Test successful execution\"\"\"
        # Arrange
        input_data = {{
            'amount': Decimal('100.00'),
            'currency': 'INR'
        }}

        # Act
        result = await {func_name}(**input_data)

        # Assert
        assert result is not None
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_{func_name}_invalid_input(self):
        \"\"\"Test with invalid input\"\"\"
        # Arrange
        invalid_data = {{'amount': -100}}

        # Act & Assert
        with pytest.raises(ValidationError):
            await {func_name}(**invalid_data)

    @pytest.mark.asyncio
    async def test_{func_name}_external_failure(self, mock_dependencies):
        \"\"\"Test handling of external service failure\"\"\"
        # Arrange
        mock_dependencies['external_api'].side_effect = ServiceUnavailable()

        # Act & Assert
        with pytest.raises(ExternalServiceError):
            await {func_name}(external_api=mock_dependencies['external_api'])

    @pytest.mark.asyncio
    async def test_{func_name}_idempotency(self):
        \"\"\"Test idempotency of operation\"\"\"
        # Arrange
        idempotency_key = 'unique-key-123'

        # Act
        result1 = await {func_name}(idempotency_key=idempotency_key)
        result2 = await {func_name}(idempotency_key=idempotency_key)

        # Assert
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_{func_name}_concurrent_calls(self):
        \"\"\"Test concurrent execution\"\"\"
        import asyncio

        # Arrange
        tasks = [
            {func_name}(id=i) for i in range(10)
        ]

        # Act
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 10
        assert all(r['status'] == 'success' for r in results)

    def test_{func_name}_audit_logging(self, mock_dependencies, caplog):
        \"\"\"Verify audit logging\"\"\"
        # Act
        {func_name}()

        # Assert
        assert 'audit' in caplog.text
        assert 'sensitive_data' not in caplog.text  # No PII in logs
```

### Test Coverage Requirements:
- Line coverage: > 80%
- Branch coverage: > 70%
- All error paths tested
- Integration tests included"""

    def _generate_security_tests(self, area: str) -> str:
        """Generate security-focused tests"""
        return f"""## Security Test Cases for {area.replace('_', ' ').title()}

```python
import pytest
from unittest.mock import patch

class TestSecurity{area.title().replace('_', '')}:
    \"\"\"Security test cases\"\"\"

    @pytest.mark.security
    def test_sql_injection_prevention(self):
        \"\"\"Test SQL injection is prevented\"\"\"
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "1; DELETE FROM payments; --"
        ]

        for payload in malicious_inputs:
            # Should not raise SQL error
            # Should sanitize or reject input
            with pytest.raises(ValidationError):
                process_input(payload)

    @pytest.mark.security
    def test_xss_prevention(self):
        \"\"\"Test XSS is prevented\"\"\"
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src='x' onerror='alert(1)'>"
        ]

        for payload in xss_payloads:
            result = sanitize_input(payload)
            assert '<script>' not in result
            assert 'javascript:' not in result

    @pytest.mark.security
    def test_authentication_required(self):
        \"\"\"Test endpoints require authentication\"\"\"
        response = client.get('/api/payments')
        assert response.status_code == 401

    @pytest.mark.security
    def test_authorization_enforced(self):
        \"\"\"Test authorization is enforced\"\"\"
        # User A should not access User B's data
        user_a_token = get_token('user_a')
        response = client.get(
            '/api/payments/user_b_payment_id',
            headers={{'Authorization': f'Bearer {{user_a_token}}'}}
        )
        assert response.status_code == 403

    @pytest.mark.security
    def test_rate_limiting(self):
        \"\"\"Test rate limiting is enforced\"\"\"
        # Make requests until rate limited
        for i in range(100):
            response = client.post('/api/payments')
            if response.status_code == 429:
                break

        assert response.status_code == 429
        assert 'Retry-After' in response.headers

    @pytest.mark.security
    def test_sensitive_data_not_logged(self, caplog):
        \"\"\"Test sensitive data is not in logs\"\"\"
        process_payment(
            card_number='4111111111111111',
            cvv='123'
        )

        log_output = caplog.text
        assert '4111111111111111' not in log_output
        assert '123' not in log_output  # CVV

    @pytest.mark.security
    def test_encryption_at_rest(self):
        \"\"\"Test data is encrypted in database\"\"\"
        # Store sensitive data
        store_card_data('4111111111111111')

        # Read raw from database
        raw_data = db.execute('SELECT card_data FROM cards').fetchone()

        # Should be encrypted (not plaintext)
        assert '4111111111111111' not in str(raw_data)

    @pytest.mark.security
    def test_tls_required(self):
        \"\"\"Test TLS is required for API\"\"\"
        # HTTP should be rejected
        response = http_client.get('http://api.example.com/payments')
        assert response.status_code in [301, 302, 403]

    @pytest.mark.security
    def test_password_hashing(self):
        \"\"\"Test passwords are properly hashed\"\"\"
        password = 'secure_password_123'
        hashed = hash_password(password)

        # Should not be plaintext
        assert password not in hashed
        # Should be valid bcrypt hash
        assert hashed.startswith('$2b$')

    @pytest.mark.security
    def test_session_timeout(self):
        \"\"\"Test session expires after timeout\"\"\"
        token = create_session('user_id')

        # Fast-forward time
        with freeze_time('+16 minutes'):
            response = client.get(
                '/api/profile',
                headers={{'Authorization': f'Bearer {{token}}'}}
            )
            assert response.status_code == 401
```

### PCI-DSS Security Tests:
- [ ] Card data masking verified
- [ ] CVV not stored after authorization
- [ ] Encryption algorithms meet standards
- [ ] Access controls tested
- [ ] Audit logging verified"""

    def generate_payment_test_samples(self) -> list[TrainingSample]:
        """Generate synthetic payment testing samples"""
        samples = []

        # Integration test sample
        samples.append(self.create_sample(
            instruction="Write integration tests for a payment flow including success, failure, and refund scenarios",
            output="""## Payment Flow Integration Tests

```python
import pytest
from decimal import Decimal
from datetime import datetime
import asyncio

class TestPaymentFlow:
    \"\"\"End-to-end payment flow tests\"\"\"

    @pytest.fixture
    async def test_merchant(self, db):
        \"\"\"Create test merchant\"\"\"
        merchant = await create_merchant(
            name='Test Merchant',
            email='test@merchant.com',
            api_key='test_api_key'
        )
        yield merchant
        await cleanup_merchant(merchant.id)

    @pytest.fixture
    def test_card(self):
        \"\"\"Test card details (Razorpay test cards)\"\"\"
        return {
            'number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123',
            'name': 'Test User'
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_successful_payment_flow(self, test_merchant, test_card):
        \"\"\"Test complete successful payment flow\"\"\"
        # Step 1: Create order
        order = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('1000.00'),
            currency='INR',
            customer_email='customer@test.com'
        )
        assert order.status == 'created'
        assert order.amount == Decimal('1000.00')

        # Step 2: Authorize payment
        payment = await authorize_payment(
            order_id=order.id,
            card=test_card
        )
        assert payment.status == 'authorized'
        assert payment.order_id == order.id

        # Step 3: Capture payment
        captured = await capture_payment(payment.id)
        assert captured.status == 'captured'

        # Step 4: Verify order status
        updated_order = await get_order(order.id)
        assert updated_order.status == 'paid'

        # Step 5: Verify audit trail
        audit_logs = await get_audit_logs(order_id=order.id)
        assert len(audit_logs) >= 3  # create, authorize, capture

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_failed_payment_insufficient_funds(self, test_merchant):
        \"\"\"Test payment failure due to insufficient funds\"\"\"
        # Use test card that simulates insufficient funds
        declined_card = {
            'number': '4000000000000002',  # Decline card
            'expiry': '12/25',
            'cvv': '123'
        }

        order = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('1000.00'),
            currency='INR'
        )

        payment = await authorize_payment(
            order_id=order.id,
            card=declined_card
        )

        assert payment.status == 'failed'
        assert payment.failure_reason == 'insufficient_funds'

        # Order should remain unpaid
        order = await get_order(order.id)
        assert order.status == 'pending'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refund_flow(self, test_merchant, test_card):
        \"\"\"Test complete refund flow\"\"\"
        # Create and complete payment
        order = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('500.00'),
            currency='INR'
        )

        payment = await authorize_payment(order_id=order.id, card=test_card)
        await capture_payment(payment.id)

        # Full refund
        refund = await create_refund(
            payment_id=payment.id,
            amount=Decimal('500.00'),
            reason='customer_request'
        )

        assert refund.status == 'processed'
        assert refund.amount == Decimal('500.00')

        # Verify payment status
        payment = await get_payment(payment.id)
        assert payment.refund_status == 'full'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_partial_refund(self, test_merchant, test_card):
        \"\"\"Test partial refund\"\"\"
        order = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('1000.00'),
            currency='INR'
        )

        payment = await authorize_payment(order_id=order.id, card=test_card)
        await capture_payment(payment.id)

        # Partial refund
        refund1 = await create_refund(
            payment_id=payment.id,
            amount=Decimal('300.00')
        )
        assert refund1.status == 'processed'

        # Another partial refund
        refund2 = await create_refund(
            payment_id=payment.id,
            amount=Decimal('200.00')
        )
        assert refund2.status == 'processed'

        # Verify total refunded
        payment = await get_payment(payment.id)
        assert payment.amount_refunded == Decimal('500.00')
        assert payment.refund_status == 'partial'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_idempotency(self, test_merchant, test_card):
        \"\"\"Test payment idempotency\"\"\"
        idempotency_key = 'unique-key-123'

        # First request
        order1 = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('100.00'),
            currency='INR',
            idempotency_key=idempotency_key
        )

        # Duplicate request with same key
        order2 = await create_order(
            merchant_id=test_merchant.id,
            amount=Decimal('100.00'),
            currency='INR',
            idempotency_key=idempotency_key
        )

        # Should return same order
        assert order1.id == order2.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_webhook_delivery(self, test_merchant, test_card):
        \"\"\"Test webhook is delivered on payment completion\"\"\"
        webhook_received = asyncio.Event()

        async def webhook_handler(payload):
            if payload['event'] == 'payment.captured':
                webhook_received.set()

        # Register webhook handler
        with mock_webhook_endpoint(webhook_handler):
            order = await create_order(
                merchant_id=test_merchant.id,
                amount=Decimal('100.00'),
                currency='INR'
            )
            payment = await authorize_payment(order_id=order.id, card=test_card)
            await capture_payment(payment.id)

            # Wait for webhook
            await asyncio.wait_for(webhook_received.wait(), timeout=10)

        assert webhook_received.is_set()
```

### Test Data Reference:

| Card Number | Behavior |
|-------------|----------|
| 4111111111111111 | Success |
| 4000000000000002 | Decline |
| 4000000000000069 | Expired card |
| 4100000000000019 | 3DS required |

### Test Coverage Targets:
- Happy path: 100%
- Error scenarios: > 90%
- Edge cases: > 80%
- Concurrent operations: Tested""",
            category="integration_test",
            compliance_tags=["PCI-DSS"]
        ))

        return samples
