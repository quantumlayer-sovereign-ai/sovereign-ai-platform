# Payment System Design Patterns

## Overview

This document covers architectural patterns for building robust, scalable, and compliant payment systems. These patterns are derived from industry best practices and regulatory requirements.

## 1. Transaction State Machine

### Payment Lifecycle States

```
┌──────────┐     ┌──────────┐     ┌───────────┐
│ CREATED  │────▶│ PENDING  │────▶│ AUTHORIZED│
└──────────┘     └──────────┘     └───────────┘
                      │                  │
                      ▼                  ▼
                 ┌─────────┐       ┌──────────┐
                 │ FAILED  │       │ CAPTURED │
                 └─────────┘       └──────────┘
                                        │
                      ┌─────────────────┼─────────────────┐
                      ▼                 ▼                 ▼
                ┌──────────┐     ┌───────────┐     ┌───────────┐
                │ REFUNDED │     │ PARTIALLY │     │ DISPUTED  │
                └──────────┘     │ REFUNDED  │     └───────────┘
                                 └───────────┘
```

### Implementation

```python
from enum import Enum
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

class PaymentStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

class TransactionType(Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    REVERSAL = "reversal"

@dataclass
class PaymentStateTransition:
    from_status: PaymentStatus
    to_status: PaymentStatus
    timestamp: datetime
    actor: str
    reason: Optional[str] = None
    metadata: dict = field(default_factory=dict)

class PaymentStateMachine:
    """
    State machine for payment lifecycle management

    Enforces valid state transitions and maintains audit trail
    """

    VALID_TRANSITIONS = {
        PaymentStatus.CREATED: [PaymentStatus.PENDING, PaymentStatus.CANCELLED],
        PaymentStatus.PENDING: [PaymentStatus.AUTHORIZED, PaymentStatus.FAILED, PaymentStatus.CANCELLED],
        PaymentStatus.AUTHORIZED: [PaymentStatus.CAPTURED, PaymentStatus.CANCELLED, PaymentStatus.FAILED],
        PaymentStatus.CAPTURED: [PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED, PaymentStatus.DISPUTED],
        PaymentStatus.PARTIALLY_REFUNDED: [PaymentStatus.REFUNDED, PaymentStatus.DISPUTED],
        PaymentStatus.DISPUTED: [PaymentStatus.REFUNDED, PaymentStatus.CAPTURED],  # After dispute resolution
    }

    def __init__(self, payment_id: str, initial_status: PaymentStatus = PaymentStatus.CREATED):
        self.payment_id = payment_id
        self.current_status = initial_status
        self.history: List[PaymentStateTransition] = []

    def can_transition(self, to_status: PaymentStatus) -> bool:
        allowed = self.VALID_TRANSITIONS.get(self.current_status, [])
        return to_status in allowed

    def transition(self, to_status: PaymentStatus, actor: str,
                   reason: Optional[str] = None) -> bool:
        if not self.can_transition(to_status):
            raise InvalidStateTransition(
                f"Cannot transition from {self.current_status.value} to {to_status.value}"
            )

        transition = PaymentStateTransition(
            from_status=self.current_status,
            to_status=to_status,
            timestamp=datetime.utcnow(),
            actor=actor,
            reason=reason
        )

        self.history.append(transition)
        self.current_status = to_status
        return True

    def get_audit_trail(self) -> List[dict]:
        return [
            {
                'from': t.from_status.value,
                'to': t.to_status.value,
                'timestamp': t.timestamp.isoformat(),
                'actor': t.actor,
                'reason': t.reason
            }
            for t in self.history
        ]
```

## 2. Payment Orchestration Pattern

### Multi-Gateway Orchestration

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass
import asyncio

@dataclass
class PaymentGatewayConfig:
    name: str
    priority: int
    max_amount: Decimal
    supported_currencies: List[str]
    supported_methods: List[str]
    is_active: bool
    failover_enabled: bool

class PaymentGateway(ABC):
    @abstractmethod
    async def process(self, request: 'PaymentRequest') -> 'PaymentResponse':
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        pass

class PaymentOrchestrator:
    """
    Orchestrates payment routing across multiple gateways

    Features:
    - Intelligent routing based on rules
    - Automatic failover
    - Load balancing
    - Cost optimization
    """

    def __init__(self):
        self.gateways: Dict[str, PaymentGateway] = {}
        self.configs: Dict[str, PaymentGatewayConfig] = {}
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}

    def register_gateway(self, gateway: PaymentGateway, config: PaymentGatewayConfig):
        self.gateways[config.name] = gateway
        self.configs[config.name] = config
        self.circuit_breakers[config.name] = CircuitBreaker(config.name)

    async def route_payment(self, request: 'PaymentRequest') -> 'PaymentResponse':
        """Route payment to appropriate gateway"""

        # Get eligible gateways
        eligible = self._get_eligible_gateways(request)

        if not eligible:
            raise NoEligibleGateway("No gateway available for this payment")

        # Sort by priority
        eligible.sort(key=lambda g: self.configs[g].priority)

        # Try each gateway with failover
        last_error = None
        for gateway_name in eligible:
            if not self.circuit_breakers[gateway_name].is_available():
                continue

            try:
                response = await self._process_with_gateway(gateway_name, request)
                if response.success:
                    return response

                # Non-critical failure, try next
                last_error = response.error

            except GatewayTimeout:
                self.circuit_breakers[gateway_name].record_failure()
                last_error = "Gateway timeout"

            except GatewayError as e:
                self.circuit_breakers[gateway_name].record_failure()
                last_error = str(e)

        raise PaymentFailed(f"All gateways failed. Last error: {last_error}")

    def _get_eligible_gateways(self, request: 'PaymentRequest') -> List[str]:
        eligible = []

        for name, config in self.configs.items():
            if not config.is_active:
                continue
            if request.amount > config.max_amount:
                continue
            if request.currency not in config.supported_currencies:
                continue
            if request.payment_method not in config.supported_methods:
                continue

            eligible.append(name)

        return eligible

    async def _process_with_gateway(self, name: str, request: 'PaymentRequest') -> 'PaymentResponse':
        gateway = self.gateways[name]

        try:
            response = await asyncio.wait_for(
                gateway.process(request),
                timeout=30.0  # 30 second timeout
            )
            self.circuit_breakers[name].record_success()
            return response

        except asyncio.TimeoutError:
            raise GatewayTimeout(f"Gateway {name} timed out")

class CircuitBreaker:
    """
    Circuit breaker pattern for gateway failure handling

    States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    """

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def is_available(self) -> bool:
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if self._recovery_period_elapsed():
                self.state = "HALF_OPEN"
                return True
            return False

        return True  # HALF_OPEN

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.utcnow()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def _recovery_period_elapsed(self) -> bool:
        if not self.last_failure_time:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
```

## 3. Saga Pattern for Distributed Transactions

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime

class SagaStepStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

class SagaStep(ABC):
    """Base class for saga steps"""

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the step's main action"""
        pass

    @abstractmethod
    async def compensate(self, context: Dict[str, Any]) -> bool:
        """Undo the step's action (compensation)"""
        pass

class PaymentSaga:
    """
    Saga pattern for complex payment workflows

    Example: E-commerce payment with inventory reservation

    Steps:
    1. Reserve inventory
    2. Process payment
    3. Create order
    4. Notify customer

    If any step fails, execute compensations in reverse order
    """

    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self.steps: List[SagaStep] = []
        self.step_statuses: Dict[int, SagaStepStatus] = {}
        self.step_results: Dict[int, Any] = {}
        self.context: Dict[str, Any] = {}

    def add_step(self, step: SagaStep):
        index = len(self.steps)
        self.steps.append(step)
        self.step_statuses[index] = SagaStepStatus.PENDING

    async def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute saga with automatic compensation on failure"""
        self.context = initial_context.copy()
        executed_steps = []

        try:
            for i, step in enumerate(self.steps):
                self.step_statuses[i] = SagaStepStatus.EXECUTING

                result = await step.execute(self.context)
                self.step_results[i] = result
                self.context.update(result)  # Enrich context with results

                self.step_statuses[i] = SagaStepStatus.COMPLETED
                executed_steps.append(i)

            return {
                'saga_id': self.saga_id,
                'status': 'completed',
                'context': self.context
            }

        except Exception as e:
            # Saga failed, run compensations
            return await self._compensate(executed_steps, str(e))

    async def _compensate(self, executed_steps: List[int], error: str) -> Dict[str, Any]:
        """Run compensating transactions in reverse order"""
        compensation_errors = []

        for i in reversed(executed_steps):
            try:
                self.step_statuses[i] = SagaStepStatus.COMPENSATING
                await self.steps[i].compensate(self.context)
                self.step_statuses[i] = SagaStepStatus.COMPENSATED
            except Exception as ce:
                compensation_errors.append({
                    'step': i,
                    'error': str(ce)
                })

        return {
            'saga_id': self.saga_id,
            'status': 'compensated',
            'original_error': error,
            'compensation_errors': compensation_errors
        }

# Example: E-commerce Payment Saga Steps

class ReserveInventoryStep(SagaStep):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        items = context['items']
        reservation_id = await inventory_service.reserve(items)
        return {'reservation_id': reservation_id}

    async def compensate(self, context: Dict[str, Any]) -> bool:
        reservation_id = context.get('reservation_id')
        if reservation_id:
            await inventory_service.release(reservation_id)
        return True

class ProcessPaymentStep(SagaStep):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        payment_result = await payment_service.charge(
            customer_id=context['customer_id'],
            amount=context['amount'],
            payment_method=context['payment_method']
        )
        return {
            'payment_id': payment_result['id'],
            'payment_reference': payment_result['reference']
        }

    async def compensate(self, context: Dict[str, Any]) -> bool:
        payment_id = context.get('payment_id')
        if payment_id:
            await payment_service.refund(payment_id)
        return True

class CreateOrderStep(SagaStep):
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        order = await order_service.create(
            customer_id=context['customer_id'],
            items=context['items'],
            payment_id=context['payment_id']
        )
        return {'order_id': order['id']}

    async def compensate(self, context: Dict[str, Any]) -> bool:
        order_id = context.get('order_id')
        if order_id:
            await order_service.cancel(order_id)
        return True

# Usage
async def process_order(order_data: dict):
    saga = PaymentSaga(saga_id=generate_id())
    saga.add_step(ReserveInventoryStep())
    saga.add_step(ProcessPaymentStep())
    saga.add_step(CreateOrderStep())

    result = await saga.execute(order_data)
    return result
```

## 4. Event Sourcing for Payment History

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Type
from enum import Enum
import json

class EventType(Enum):
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_DISPUTED = "payment.disputed"

@dataclass
class PaymentEvent:
    event_id: str
    payment_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    actor: str
    version: int

class PaymentAggregate:
    """
    Event-sourced payment aggregate

    Reconstructs state from event history
    Provides complete audit trail
    """

    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        self.status = None
        self.amount = None
        self.currency = None
        self.customer_id = None
        self.version = 0
        self.events: List[PaymentEvent] = []
        self.refunded_amount = 0

    def apply_event(self, event: PaymentEvent):
        """Apply event to update state"""
        handler = getattr(self, f"_apply_{event.event_type.value.replace('.', '_')}", None)
        if handler:
            handler(event)
        self.events.append(event)
        self.version = event.version

    def _apply_payment_initiated(self, event: PaymentEvent):
        self.status = PaymentStatus.PENDING
        self.amount = event.data['amount']
        self.currency = event.data['currency']
        self.customer_id = event.data['customer_id']

    def _apply_payment_authorized(self, event: PaymentEvent):
        self.status = PaymentStatus.AUTHORIZED
        self.authorization_code = event.data.get('authorization_code')

    def _apply_payment_captured(self, event: PaymentEvent):
        self.status = PaymentStatus.CAPTURED
        self.captured_at = event.timestamp

    def _apply_payment_failed(self, event: PaymentEvent):
        self.status = PaymentStatus.FAILED
        self.failure_reason = event.data.get('reason')

    def _apply_payment_refunded(self, event: PaymentEvent):
        refund_amount = event.data.get('amount', self.amount)
        self.refunded_amount += refund_amount

        if self.refunded_amount >= self.amount:
            self.status = PaymentStatus.REFUNDED
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED

    def get_snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot"""
        return {
            'payment_id': self.payment_id,
            'status': self.status.value if self.status else None,
            'amount': self.amount,
            'currency': self.currency,
            'customer_id': self.customer_id,
            'refunded_amount': self.refunded_amount,
            'version': self.version
        }

class EventStore:
    """
    Append-only event store for payment events

    Ensures immutability and complete history
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def append(self, event: PaymentEvent):
        """Append event to store"""
        await self.db.execute("""
            INSERT INTO payment_events
            (event_id, payment_id, event_type, timestamp, data, actor, version)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, event.event_id, event.payment_id, event.event_type.value,
             event.timestamp, json.dumps(event.data), event.actor, event.version)

    async def get_events(self, payment_id: str,
                         from_version: int = 0) -> List[PaymentEvent]:
        """Get all events for a payment"""
        rows = await self.db.fetch("""
            SELECT * FROM payment_events
            WHERE payment_id = $1 AND version > $2
            ORDER BY version ASC
        """, payment_id, from_version)

        return [
            PaymentEvent(
                event_id=row['event_id'],
                payment_id=row['payment_id'],
                event_type=EventType(row['event_type']),
                timestamp=row['timestamp'],
                data=json.loads(row['data']),
                actor=row['actor'],
                version=row['version']
            )
            for row in rows
        ]

    async def load_aggregate(self, payment_id: str) -> PaymentAggregate:
        """Load and reconstitute aggregate from events"""
        aggregate = PaymentAggregate(payment_id)
        events = await self.get_events(payment_id)

        for event in events:
            aggregate.apply_event(event)

        return aggregate
```

## 5. Webhook Processing Pattern

```python
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

class WebhookStatus(Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class WebhookEvent:
    webhook_id: str
    provider: str
    event_type: str
    payload: Dict[str, Any]
    signature: str
    received_at: datetime
    status: WebhookStatus = WebhookStatus.RECEIVED
    retry_count: int = 0

class WebhookProcessor:
    """
    Reliable webhook processing with deduplication and retry

    Handles:
    - Signature verification
    - Deduplication
    - Idempotent processing
    - Exponential backoff retry
    """

    MAX_RETRIES = 5
    RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1m, 5m, 15m, 1h, 2h

    def __init__(self, db, event_handlers: Dict[str, callable]):
        self.db = db
        self.handlers = event_handlers
        self.provider_secrets = {}

    def register_provider(self, provider: str, secret: str):
        self.provider_secrets[provider] = secret

    async def receive_webhook(self, provider: str, payload: Dict,
                              signature: str) -> str:
        """Receive and queue webhook for processing"""

        # Verify signature
        if not self._verify_signature(provider, payload, signature):
            raise InvalidSignature("Webhook signature verification failed")

        # Generate idempotency key from payload
        webhook_id = self._generate_webhook_id(provider, payload)

        # Check for duplicate (idempotency)
        existing = await self._get_webhook(webhook_id)
        if existing:
            return f"Webhook {webhook_id} already processed"

        # Store webhook
        event = WebhookEvent(
            webhook_id=webhook_id,
            provider=provider,
            event_type=payload.get('type', 'unknown'),
            payload=payload,
            signature=signature,
            received_at=datetime.utcnow()
        )
        await self._store_webhook(event)

        # Process asynchronously
        asyncio.create_task(self._process_webhook(event))

        return webhook_id

    async def _process_webhook(self, event: WebhookEvent):
        """Process webhook with retry logic"""
        event.status = WebhookStatus.PROCESSING
        await self._update_status(event)

        try:
            handler = self.handlers.get(event.event_type)
            if not handler:
                raise UnknownEventType(f"No handler for {event.event_type}")

            await handler(event.payload)

            event.status = WebhookStatus.PROCESSED
            await self._update_status(event)

        except RetryableError as e:
            event.status = WebhookStatus.RETRYING
            event.retry_count += 1
            await self._update_status(event)

            if event.retry_count <= self.MAX_RETRIES:
                delay = self.RETRY_DELAYS[event.retry_count - 1]
                await asyncio.sleep(delay)
                await self._process_webhook(event)
            else:
                event.status = WebhookStatus.FAILED
                await self._update_status(event)

        except Exception as e:
            event.status = WebhookStatus.FAILED
            await self._update_status(event)
            raise

    def _verify_signature(self, provider: str, payload: Dict,
                          signature: str) -> bool:
        """Verify webhook signature based on provider"""
        secret = self.provider_secrets.get(provider)
        if not secret:
            return False

        # Provider-specific verification
        if provider == "razorpay":
            return self._verify_razorpay_signature(payload, signature, secret)
        elif provider == "stripe":
            return self._verify_stripe_signature(payload, signature, secret)

        return False

    def _verify_razorpay_signature(self, payload: Dict, signature: str,
                                   secret: str) -> bool:
        payload_str = f"{payload.get('razorpay_order_id')}|{payload.get('razorpay_payment_id')}"
        expected = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def _generate_webhook_id(self, provider: str, payload: Dict) -> str:
        """Generate unique webhook ID for deduplication"""
        # Use provider-specific identifier
        if provider == "razorpay":
            return f"rp_{payload.get('razorpay_payment_id')}"
        elif provider == "stripe":
            return f"st_{payload.get('id')}"

        # Fallback: hash the payload
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        return f"{provider}_{payload_hash}"

# Example event handlers
async def handle_payment_success(payload: Dict):
    payment_id = payload.get('payment_id')
    await payment_service.mark_successful(payment_id)
    await notification_service.send_receipt(payment_id)

async def handle_payment_failed(payload: Dict):
    payment_id = payload.get('payment_id')
    reason = payload.get('error', {}).get('description')
    await payment_service.mark_failed(payment_id, reason)
    await notification_service.send_failure_notice(payment_id, reason)

# Setup processor
webhook_processor = WebhookProcessor(
    db=database,
    event_handlers={
        'payment.captured': handle_payment_success,
        'payment.failed': handle_payment_failed,
        'refund.created': handle_refund_created,
    }
)
webhook_processor.register_provider('razorpay', 'webhook_secret_key')
```

## 6. Reconciliation Pattern

```python
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Tuple
from enum import Enum
from dataclasses import dataclass

class ReconciliationStatus(Enum):
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    MISSING_INTERNAL = "missing_internal"
    MISSING_EXTERNAL = "missing_external"
    AMOUNT_MISMATCH = "amount_mismatch"

@dataclass
class ReconciliationItem:
    internal_id: str
    external_id: Optional[str]
    internal_amount: Decimal
    external_amount: Optional[Decimal]
    status: ReconciliationStatus
    discrepancy: Optional[Decimal] = None

class PaymentReconciler:
    """
    Payment reconciliation system

    Matches internal records with gateway/bank statements
    Identifies discrepancies for investigation
    """

    def __init__(self, internal_repo, external_repo):
        self.internal = internal_repo
        self.external = external_repo
        self.tolerance = Decimal('0.01')  # ₹0.01 tolerance

    async def reconcile_day(self, reconciliation_date: date) -> Dict[str, Any]:
        """Reconcile all payments for a specific day"""

        # Fetch internal records
        internal_txns = await self.internal.get_transactions(
            date=reconciliation_date,
            status=['captured', 'refunded']
        )

        # Fetch external (gateway/bank) records
        external_txns = await self.external.get_transactions(
            date=reconciliation_date
        )

        # Create lookup maps
        internal_map = {t['gateway_reference']: t for t in internal_txns}
        external_map = {t['reference']: t for t in external_txns}

        results = []

        # Check all internal transactions
        for ref, internal in internal_map.items():
            external = external_map.get(ref)

            if external is None:
                results.append(ReconciliationItem(
                    internal_id=internal['id'],
                    external_id=None,
                    internal_amount=internal['amount'],
                    external_amount=None,
                    status=ReconciliationStatus.MISSING_EXTERNAL
                ))
            elif abs(internal['amount'] - external['amount']) > self.tolerance:
                discrepancy = internal['amount'] - external['amount']
                results.append(ReconciliationItem(
                    internal_id=internal['id'],
                    external_id=external['id'],
                    internal_amount=internal['amount'],
                    external_amount=external['amount'],
                    status=ReconciliationStatus.AMOUNT_MISMATCH,
                    discrepancy=discrepancy
                ))
            else:
                results.append(ReconciliationItem(
                    internal_id=internal['id'],
                    external_id=external['id'],
                    internal_amount=internal['amount'],
                    external_amount=external['amount'],
                    status=ReconciliationStatus.MATCHED
                ))

        # Check for external transactions missing internally
        for ref, external in external_map.items():
            if ref not in internal_map:
                results.append(ReconciliationItem(
                    internal_id=None,
                    external_id=external['id'],
                    internal_amount=None,
                    external_amount=external['amount'],
                    status=ReconciliationStatus.MISSING_INTERNAL
                ))

        return self._generate_report(reconciliation_date, results)

    def _generate_report(self, date: date,
                         results: List[ReconciliationItem]) -> Dict[str, Any]:
        matched = [r for r in results if r.status == ReconciliationStatus.MATCHED]
        discrepancies = [r for r in results if r.status != ReconciliationStatus.MATCHED]

        total_internal = sum(r.internal_amount or 0 for r in results)
        total_external = sum(r.external_amount or 0 for r in results)

        return {
            'date': date.isoformat(),
            'summary': {
                'total_transactions': len(results),
                'matched': len(matched),
                'discrepancies': len(discrepancies),
                'match_rate': f"{len(matched)/len(results)*100:.2f}%",
                'total_internal': str(total_internal),
                'total_external': str(total_external),
                'net_difference': str(total_internal - total_external)
            },
            'discrepancy_breakdown': {
                'missing_external': len([r for r in results if r.status == ReconciliationStatus.MISSING_EXTERNAL]),
                'missing_internal': len([r for r in results if r.status == ReconciliationStatus.MISSING_INTERNAL]),
                'amount_mismatch': len([r for r in results if r.status == ReconciliationStatus.AMOUNT_MISMATCH])
            },
            'discrepancies': [
                {
                    'internal_id': r.internal_id,
                    'external_id': r.external_id,
                    'internal_amount': str(r.internal_amount) if r.internal_amount else None,
                    'external_amount': str(r.external_amount) if r.external_amount else None,
                    'status': r.status.value,
                    'discrepancy': str(r.discrepancy) if r.discrepancy else None
                }
                for r in discrepancies
            ]
        }
```

These patterns form the foundation of robust payment systems. Each pattern addresses specific challenges in building reliable, compliant financial applications.
