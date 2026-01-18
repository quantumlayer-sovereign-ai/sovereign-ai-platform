"""
Shared Test Fixtures and Configuration

Provides common fixtures for all test levels:
- Unit tests
- Integration tests
- Contract tests
"""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

# ============================================================================
# Async Support
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def knowledge_base_path(project_root) -> Path:
    """Get knowledge base directory"""
    return project_root / "data" / "knowledge" / "fintech"


@pytest.fixture
def temp_workspace(tmp_path) -> Path:
    """Create temporary workspace for file operations"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def temp_vectordb(tmp_path) -> Path:
    """Create temporary directory for vector database"""
    db_path = tmp_path / "vectordb"
    db_path.mkdir()
    return db_path


# ============================================================================
# Mock Model Fixtures
# ============================================================================

@pytest.fixture
def mock_model():
    """Create mock model interface"""
    model = Mock()
    model.is_loaded = True
    model.model_info = {
        "model_id": "test-model",
        "model_size": "7b",
        "quantized": True,
        "loaded": True,
        "vram_gb": 5.0
    }
    model.generate = Mock(return_value="Generated response")
    model.generate_async = AsyncMock(return_value="Generated response")
    return model


@pytest.fixture
def mock_model_unloaded():
    """Create mock model that is not loaded"""
    model = Mock()
    model.is_loaded = False
    model.model_info = {"loaded": False}
    return model


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_code_secure() -> str:
    """Sample secure Python code"""
    return '''
import hashlib
import os
from cryptography.fernet import Fernet

def hash_sensitive_data(data: str) -> str:
    """Securely hash sensitive data with salt"""
    salt = os.urandom(32)
    return hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000).hex()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using Fernet"""
    f = Fernet(key)
    return f.encrypt(data)

def make_secure_request(url: str, data: dict):
    """Make HTTPS request"""
    import requests
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS URLs allowed")
    return requests.post(url, json=data)
'''


@pytest.fixture
def sample_code_insecure() -> str:
    """Sample insecure Python code with vulnerabilities"""
    return '''
import os
import hashlib

# Hardcoded credentials (SEC003)
API_KEY = "sk_live_1234567890abcdefghij"
password = "supersecretpassword123"

def get_user(user_id):
    # SQL Injection (SEC001)
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def hash_password(pwd):
    # Weak crypto (SEC005)
    return hashlib.md5(pwd.encode()).hexdigest()

def run_command(user_input):
    # Command injection (SEC006)
    os.system("ls " + user_input)

def fetch_data():
    # Insecure HTTP (SEC004)
    import requests
    return requests.get("http://api.example.com/data")
'''


@pytest.fixture
def sample_pci_compliant_code() -> str:
    """PCI-DSS compliant payment code"""
    return '''
import hashlib
import os
from cryptography.fernet import Fernet

class SecurePaymentProcessor:
    def __init__(self, encryption_key: bytes):
        self.fernet = Fernet(encryption_key)

    def tokenize_card(self, card_number: str) -> str:
        """Create a token for the card number"""
        salt = os.urandom(32)
        token = hashlib.pbkdf2_hmac(
            'sha256',
            card_number.encode(),
            salt,
            100000
        ).hex()
        return token

    def process_payment(self, token: str, amount: float):
        """Process payment using tokenized card"""
        url = "https://secure-payment-gateway.example.com/charge"
        # Use token, never store actual card number
        return self._make_request(url, {"token": token, "amount": amount})
'''


@pytest.fixture
def sample_pci_violation_code() -> str:
    """Code with PCI-DSS violations"""
    return '''
# Hardcoded card number (PCI-3.4)
test_card = "4111111111111111"

def store_card(card_number):
    # Storing card in plain text
    with open("cards.txt", "a") as f:
        f.write(card_number)

def send_payment(card_data):
    # Unencrypted transmission (PCI-4.1)
    import requests
    url = "http://payment-api.example.com/charge"
    return requests.post(url, data=card_data)

def get_transaction(txn_id):
    # SQL injection in financial query (PCI-6.5.1)
    query = f"SELECT * FROM transactions WHERE id = {txn_id}"
    return db.execute(query)
'''


@pytest.fixture
def sample_documents() -> list:
    """Sample documents for RAG testing"""
    return [
        {
            "content": "PCI-DSS Requirement 3.4: Render PAN unreadable anywhere it is stored.",
            "metadata": {"source": "pci_dss.md", "vertical": "fintech"}
        },
        {
            "content": "Use strong cryptography with associated key-management processes.",
            "metadata": {"source": "pci_dss.md", "vertical": "fintech"}
        },
        {
            "content": "RBI mandates tokenization for recurring card payments.",
            "metadata": {"source": "rbi_guidelines.md", "vertical": "fintech"}
        }
    ]


# ============================================================================
# Role and Agent Fixtures
# ============================================================================

@pytest.fixture
def sample_role() -> dict[str, Any]:
    """Sample agent role configuration"""
    return {
        "name": "test_coder",
        "display_name": "Test Coder",
        "description": "Test coding agent",
        "system_prompt": "You are a test coding assistant.",
        "capabilities": ["code_generation", "code_review"],
        "spawn_conditions": ["code", "implement", "write"],
        "vertical": "fintech",
        "compliance_aware": True
    }


@pytest.fixture
def fintech_roles() -> list:
    """List of FinTech role names"""
    return [
        "fintech_architect",
        "fintech_coder",
        "fintech_security",
        "fintech_compliance",
        "fintech_tester"
    ]


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_base_url() -> str:
    """Base URL for API tests"""
    return "http://localhost:8000"


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Standard API headers"""
    return {"Content-Type": "application/json"}


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    """
    Auth headers with JWT token for protected endpoint tests.
    Requires DEV_MODE=true environment variable.
    """
    import os
    os.environ["DEV_MODE"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"

    from api.auth import create_access_token
    token = create_access_token({"sub": "test-user", "email": "test@example.com", "roles": ["admin"]})

    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture(scope="module")
def auth_token() -> str:
    """Get a JWT token for testing"""
    import os
    os.environ["DEV_MODE"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"

    from api.auth import create_access_token
    return create_access_token({"sub": "test-user", "email": "test@example.com", "roles": ["admin"]})


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_registry():
    """Clean up registry after each test"""
    yield
    # Registry cleanup if needed
    try:
        from core.agents.registry import get_registry
        get_registry()  # Ensure registry is initialized
        # Reset any test roles
    except Exception:
        pass


@pytest.fixture
def isolated_registry():
    """Create isolated registry for testing"""
    from core.agents.registry import RoleRegistry
    return RoleRegistry()


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_model: Tests requiring loaded model")
    config.addinivalue_line("markers", "requires_api: Tests requiring running API")
