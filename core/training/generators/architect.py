"""
Architect Generator - System Design Training Data

Generates training samples for the fintech_architect role focusing on:
- Payment system architecture
- Security architecture
- High-availability design
"""

import re
from .base import BaseGenerator, TrainingSample


class ArchitectGenerator(BaseGenerator):
    """Generator for fintech_architect role"""

    def __init__(self):
        super().__init__()
        self.role_name = "fintech_architect"
        self.focus_areas = ["system_design", "payment_architecture", "security_architecture"]
        self.compliance_tags = ["pci_dss", "rbi", "sebi", "dpdp"]

    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate architecture-focused training samples"""
        samples = []

        # Generate architecture pattern samples
        samples.extend(self._generate_pattern_samples(content, source_file))

        # Generate system design samples
        samples.extend(self._generate_design_samples(content, source_file))

        # Add synthetic architecture samples
        samples.extend(self.generate_payment_architecture_samples())

        return samples

    def _generate_pattern_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate architecture pattern samples"""
        samples = []
        sections = self.extract_sections(content)

        pattern_keywords = ["pattern", "architecture", "design", "system", "flow"]

        for section_name, section_content in sections.items():
            if not any(kw in section_name for kw in pattern_keywords):
                continue

            if len(section_content) < 100:
                continue

            topic = section_name.replace("_", " ").title()

            samples.append(self.create_sample(
                instruction=f"Design a {topic} for a FinTech application",
                output=self._format_architecture_response(topic, section_content),
                category="architecture_pattern",
                source_file=source_file
            ))

        return samples

    def _generate_design_samples(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate system design samples from code examples"""
        samples = []
        code_blocks = self.extract_code_blocks(content)

        for block in code_blocks:
            if block["language"] != "python":
                continue

            code = block["code"]

            # Look for class definitions that represent system components
            class_match = re.search(r"class\s+(\w+)", code)
            if class_match:
                class_name = class_match.group(1)

                # Generate architecture explanation
                samples.append(self.create_sample(
                    instruction=f"Explain the architecture and design considerations for a {class_name} component",
                    input_text=code[:500],
                    output=self._generate_component_design(class_name, code),
                    category="component_design",
                    source_file=source_file
                ))

        return samples

    def _format_architecture_response(self, topic: str, content: str) -> str:
        """Format architecture response"""
        return f"""## {topic} - Architecture Design

### Overview:
{content[:400]}

### Architecture Principles:

1. **Security First**
   - Defense in depth
   - Zero trust architecture
   - Encryption everywhere

2. **High Availability**
   - No single point of failure
   - Active-passive or active-active
   - Auto-scaling capabilities

3. **Compliance by Design**
   - PCI-DSS built into architecture
   - Audit logging from day one
   - Data residency compliance

### Recommended Components:

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
├─────────────────────────────────────────────────────────┤
│     API Gateway (Authentication, Rate Limiting)          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Service A   │  │  Service B   │  │  Service C   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│               Message Queue (Async Processing)           │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Database   │  │    Cache     │  │   Secrets    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Security Considerations:
- Encrypt data at rest and in transit
- Implement proper authentication
- Regular security audits
- Incident response planning

### Scalability:
- Horizontal scaling for compute
- Database sharding strategy
- Caching layer implementation"""

    def _generate_component_design(self, class_name: str, code: str) -> str:
        """Generate component design explanation"""
        return f"""## Component Design: {class_name}

### Purpose:
This component handles critical financial operations in the payment system.

### Code Structure:
```python
{code[:600]}
```

### Design Considerations:

#### 1. Reliability
- Implement retry mechanisms
- Handle partial failures
- Ensure idempotency

#### 2. Security
- Validate all inputs
- Encrypt sensitive data
- Implement audit logging

#### 3. Performance
- Optimize database queries
- Implement caching
- Use async operations

#### 4. Maintainability
- Clear separation of concerns
- Comprehensive logging
- Unit test coverage

### Integration Points:
- Upstream: API Gateway, Authentication
- Downstream: Database, External APIs
- Async: Message Queue

### Error Handling:
- Define error taxonomy
- Implement circuit breakers
- Graceful degradation

### Monitoring:
- Health check endpoints
- Metrics collection
- Alerting thresholds"""

    def generate_payment_architecture_samples(self) -> list[TrainingSample]:
        """Generate synthetic payment architecture samples"""
        samples = []

        # Payment gateway architecture
        samples.append(self.create_sample(
            instruction="Design a payment gateway architecture that is PCI-DSS compliant and highly available",
            output="""## Payment Gateway Architecture

### Requirements:
- Process 1000+ TPS
- 99.99% availability
- PCI-DSS Level 1 compliant
- Support multiple payment methods

### High-Level Architecture:

```
                                   ┌─────────────────┐
                                   │   CloudFlare    │
                                   │   (DDoS/WAF)    │
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
            │   LB Node 1   │       │   LB Node 2   │       │   LB Node 3   │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
            │ API Gateway 1 │       │ API Gateway 2 │       │ API Gateway 3 │
            │ (Auth/Rate)   │       │ (Auth/Rate)   │       │ (Auth/Rate)   │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
    ┌────────────────┬──────────────────────┼──────────────────────┬────────────────┐
    │                │                      │                      │                │
┌───▼───┐       ┌────▼────┐          ┌──────▼──────┐         ┌─────▼─────┐    ┌─────▼─────┐
│ Auth  │       │ Payment │          │   Order     │         │  Webhook  │    │   Admin   │
│Service│       │ Service │          │   Service   │         │  Service  │    │  Service  │
└───────┘       └────┬────┘          └──────┬──────┘         └───────────┘    └───────────┘
                     │                      │
                     ▼                      ▼
            ┌────────────────┐      ┌───────────────┐
            │  Payment Bus   │      │  Order Queue  │
            │   (Kafka)      │      │   (RabbitMQ)  │
            └───────┬────────┘      └───────┬───────┘
                    │                       │
        ┌───────────┼───────────┐          │
        │           │           │          │
    ┌───▼───┐   ┌───▼───┐   ┌───▼───┐  ┌───▼───┐
    │ Card  │   │  UPI  │   │Wallet │  │ Ledger│
    │Processor│  │Gateway│   │Service│  │Service│
    └───┬───┘   └───┬───┘   └───┬───┘  └───┬───┘
        │           │           │          │
        ▼           ▼           ▼          ▼
    [Card Networks] [NPCI]   [Internal]  [PostgreSQL]
```

### Components:

#### 1. Edge Layer
- **CDN/WAF**: CloudFlare or AWS Shield
- **DDoS Protection**: Rate limiting, geo-blocking
- **TLS Termination**: TLS 1.3 only

#### 2. API Gateway
- Authentication (JWT, API Keys)
- Rate limiting per merchant
- Request validation
- Audit logging

#### 3. Core Services
- **Payment Service**: Transaction orchestration
- **Order Service**: Order management, idempotency
- **Auth Service**: OAuth 2.0, MFA
- **Webhook Service**: Async notifications

#### 4. Processing Layer
- **Card Processor**: PCI-DSS scope, HSM integration
- **UPI Gateway**: NPCI integration
- **Wallet Service**: Internal wallet operations

#### 5. Data Layer
- **Primary DB**: PostgreSQL (encrypted)
- **Read Replicas**: For reporting
- **Redis**: Session, caching
- **Kafka**: Event streaming

### PCI-DSS Compliance:

| Requirement | Implementation |
|-------------|---------------|
| Network Security | WAF, Firewall, Network Segmentation |
| Cardholder Data | Tokenization, Encryption (AES-256) |
| Vulnerability Mgmt | Regular scanning, patching |
| Access Control | RBAC, MFA, Audit logs |
| Monitoring | SIEM, IDS/IPS |

### High Availability:
- Multi-AZ deployment
- Active-passive database
- Automatic failover
- No single point of failure

### Disaster Recovery:
- RPO: 1 minute
- RTO: 15 minutes
- Cross-region replication
- Regular DR drills""",
            category="payment_architecture",
            compliance_tags=["PCI-DSS", "RBI"]
        ))

        # Microservices patterns
        samples.append(self.create_sample(
            instruction="Design a saga pattern implementation for distributed payment transactions",
            output="""## Saga Pattern for Payment Transactions

### Problem:
Distributed transactions across microservices require consistency without traditional 2PC.

### Solution: Choreography-based Saga

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio

class SagaState(Enum):
    STARTED = "started"
    ORDER_CREATED = "order_created"
    PAYMENT_AUTHORIZED = "payment_authorized"
    INVENTORY_RESERVED = "inventory_reserved"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"

@dataclass
class SagaContext:
    saga_id: str
    order_id: str
    state: SagaState
    payment_id: Optional[str] = None
    reservation_id: Optional[str] = None
    error: Optional[str] = None

class PaymentSaga:
    \"\"\"
    Orchestrates payment transaction across services

    Steps:
    1. Create order
    2. Authorize payment
    3. Reserve inventory
    4. Complete transaction

    Compensation:
    - Release inventory
    - Cancel payment authorization
    - Cancel order
    \"\"\"

    def __init__(self, order_service, payment_service, inventory_service):
        self.order_service = order_service
        self.payment_service = payment_service
        self.inventory_service = inventory_service

    async def execute(self, order_request: dict) -> SagaContext:
        context = SagaContext(
            saga_id=generate_uuid(),
            order_id="",
            state=SagaState.STARTED
        )

        try:
            # Step 1: Create Order
            order = await self.order_service.create(order_request)
            context.order_id = order["id"]
            context.state = SagaState.ORDER_CREATED
            await self._log_state(context)

            # Step 2: Authorize Payment
            payment = await self.payment_service.authorize(
                order_id=context.order_id,
                amount=order_request["amount"]
            )
            context.payment_id = payment["id"]
            context.state = SagaState.PAYMENT_AUTHORIZED
            await self._log_state(context)

            # Step 3: Reserve Inventory
            reservation = await self.inventory_service.reserve(
                order_id=context.order_id,
                items=order_request["items"]
            )
            context.reservation_id = reservation["id"]
            context.state = SagaState.INVENTORY_RESERVED
            await self._log_state(context)

            # Step 4: Complete
            await self.payment_service.capture(context.payment_id)
            await self.order_service.complete(context.order_id)
            context.state = SagaState.COMPLETED
            await self._log_state(context)

            return context

        except Exception as e:
            context.error = str(e)
            await self._compensate(context)
            return context

    async def _compensate(self, context: SagaContext):
        \"\"\"Execute compensation in reverse order\"\"\"
        context.state = SagaState.COMPENSATING
        await self._log_state(context)

        try:
            # Compensate in reverse order
            if context.reservation_id:
                await self.inventory_service.release(context.reservation_id)

            if context.payment_id:
                await self.payment_service.cancel(context.payment_id)

            if context.order_id:
                await self.order_service.cancel(context.order_id)

            context.state = SagaState.FAILED
        except Exception as e:
            # Log compensation failure - may need manual intervention
            logger.critical("saga_compensation_failed",
                          saga_id=context.saga_id,
                          error=str(e))

        await self._log_state(context)

    async def _log_state(self, context: SagaContext):
        \"\"\"Audit log for saga state transitions\"\"\"
        await audit_logger.log(
            event="saga_state_change",
            saga_id=context.saga_id,
            state=context.state.value,
            context=asdict(context)
        )
```

### Architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Saga Orchestrator                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │  Step 1 │───▶│  Step 2 │───▶│  Step 3 │───▶│  Step 4 │      │
│  │  Order  │    │ Payment │    │Inventory│    │Complete │      │
│  └────┬────┘    └────┬────┘    └────┬────┘    └─────────┘      │
│       │              │              │                            │
│       ▼              ▼              ▼                            │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                      │
│  │ Cancel  │◀───│ Cancel  │◀───│ Release │     (Compensation)   │
│  │  Order  │    │ Payment │    │Inventory│                      │
│  └─────────┘    └─────────┘    └─────────┘                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Considerations:
1. **Idempotency**: Each step must be idempotent
2. **Timeouts**: Set appropriate timeouts
3. **Retries**: Implement with exponential backoff
4. **Observability**: Log all state transitions
5. **Dead Letter Queue**: Handle unrecoverable failures""",
            category="architecture_pattern",
            compliance_tags=["PCI-DSS"]
        ))

        return samples
