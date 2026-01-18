# eIDAS Electronic Signatures and Trust Services

## Overview

The eIDAS Regulation (EU) 910/2014 establishes a legal framework for electronic identification and trust services. For FinTech applications, eIDAS is critical for:

- Electronic signatures on contracts
- TPP authentication certificates (PSD2)
- Qualified timestamps for audit trails
- Cross-border electronic identification

## Signature Levels

### Simple Electronic Signature
Basic electronic signature - any data attached to or associated with other data.

### Advanced Electronic Signature (AdES)
Must be:
- Uniquely linked to the signatory
- Capable of identifying the signatory
- Created using data under signatory's sole control
- Linked to signed data (detects any changes)

### Qualified Electronic Signature (QES)
- Advanced signature created by a qualified device
- Based on qualified certificate
- **Legal equivalent to handwritten signature**

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib
import base64

class SignatureLevel(Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"
    QUALIFIED = "qualified"

class SignatureFormat(Enum):
    XADES = "XAdES"      # XML-based
    PADES = "PAdES"      # PDF-based
    CADES = "CAdES"      # CMS-based
    JADES = "JAdES"      # JSON-based
    ASICE = "ASiC-E"     # Container format

@dataclass
class SignatureResult:
    """Result of signature creation"""
    signature_id: str
    signature_level: SignatureLevel
    format: SignatureFormat
    signature_value: str
    certificate_chain: list[str]
    signed_at: datetime
    timestamp_token: Optional[str] = None

class EIDASSignatureService:
    """
    eIDAS-compliant electronic signature service

    Supports simple, advanced, and qualified signatures
    """

    def create_signature(
        self,
        document: bytes,
        signer_certificate: str,
        private_key: str,
        level: SignatureLevel = SignatureLevel.ADVANCED,
        format: SignatureFormat = SignatureFormat.CADES
    ) -> SignatureResult:
        """
        Create electronic signature on document

        For QES, must use qualified signing device
        """
        # Calculate document hash
        doc_hash = hashlib.sha256(document).digest()

        # Create signature (simplified - real implementation uses cryptographic library)
        signature_value = self._sign_hash(doc_hash, private_key)

        # For AdES/QES, add signed attributes
        if level in [SignatureLevel.ADVANCED, SignatureLevel.QUALIFIED]:
            signed_attributes = self._create_signed_attributes(
                doc_hash,
                signer_certificate,
                datetime.utcnow()
            )
            signature_value = self._sign_with_attributes(
                signed_attributes, private_key
            )

        return SignatureResult(
            signature_id=self._generate_signature_id(),
            signature_level=level,
            format=format,
            signature_value=base64.b64encode(signature_value).decode(),
            certificate_chain=[signer_certificate],
            signed_at=datetime.utcnow()
        )

    def verify_signature(
        self,
        document: bytes,
        signature: SignatureResult
    ) -> dict:
        """
        Verify electronic signature

        Returns verification result with certificate validation
        """
        # Verify document hasn't changed
        doc_hash = hashlib.sha256(document).digest()

        # Verify signature
        is_valid = self._verify_signature_value(
            doc_hash,
            base64.b64decode(signature.signature_value),
            signature.certificate_chain[0]
        )

        # Validate certificate chain
        cert_valid = self._validate_certificate_chain(signature.certificate_chain)

        # For QES, verify QTSP and qualified certificate
        if signature.signature_level == SignatureLevel.QUALIFIED:
            qtsp_valid = self._verify_qtsp(signature.certificate_chain[0])
        else:
            qtsp_valid = None

        return {
            "signature_valid": is_valid,
            "certificate_valid": cert_valid,
            "qtsp_valid": qtsp_valid,
            "signed_at": signature.signed_at.isoformat(),
            "level": signature.signature_level.value
        }


class QualifiedSignatureService:
    """
    Service for Qualified Electronic Signatures

    Integrates with Qualified Trust Service Providers (QTSPs)
    """

    def __init__(self, qtsp_endpoint: str, api_key: str):
        self.qtsp_endpoint = qtsp_endpoint
        self.api_key = api_key

    async def qualified_signature(
        self,
        document: bytes,
        signer_id: str,
        document_name: str
    ) -> SignatureResult:
        """
        Create Qualified Electronic Signature via QTSP

        Legal equivalent to handwritten signature (Article 25(2))
        """
        # Hash document locally
        doc_hash = base64.b64encode(
            hashlib.sha256(document).digest()
        ).decode()

        # Request signature from QTSP
        response = await self._request_qtsp_signature(
            document_hash=doc_hash,
            signer_id=signer_id,
            document_name=document_name
        )

        return SignatureResult(
            signature_id=response["signature_id"],
            signature_level=SignatureLevel.QUALIFIED,
            format=SignatureFormat.CADES,
            signature_value=response["signature"],
            certificate_chain=response["certificate_chain"],
            signed_at=datetime.fromisoformat(response["timestamp"]),
            timestamp_token=response.get("timestamp_token")
        )

    async def verify_qes(
        self,
        document: bytes,
        signature: SignatureResult
    ) -> dict:
        """
        Verify Qualified Electronic Signature

        Checks QTSP validation and EU Trusted List
        """
        # Verify with QTSP validation service
        validation = await self._validate_with_qtsp(
            document=document,
            signature=signature
        )

        # Check if QTSP is on EU Trusted List
        on_trusted_list = await self._check_eu_trusted_list(
            signature.certificate_chain[0]
        )

        return {
            "valid": validation["valid"],
            "on_eu_trusted_list": on_trusted_list,
            "certificate_status": validation["certificate_status"],
            "timestamp_valid": validation.get("timestamp_valid"),
            "legal_validity": validation["valid"] and on_trusted_list
        }
```

## Qualified Timestamps

Qualified timestamps provide proof of existence at a specific time.

```python
from datetime import datetime
import hashlib
import base64

class QualifiedTimestampService:
    """
    eIDAS Qualified Timestamp Service

    Provides legally recognized proof of time
    """

    def __init__(self, tsa_endpoint: str):
        self.tsa_endpoint = tsa_endpoint

    async def timestamp_document(
        self,
        document: bytes
    ) -> dict:
        """
        Get qualified timestamp from Time Stamping Authority

        Article 42 - Legal presumption of accuracy
        """
        # Calculate hash
        doc_hash = hashlib.sha256(document).digest()

        # Request timestamp from TSA
        timestamp_token = await self._request_timestamp(doc_hash)

        return {
            "timestamp_token": base64.b64encode(timestamp_token).decode(),
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": "SHA-256",
            "tsa": self.tsa_endpoint,
            "qualified": True
        }

    async def verify_timestamp(
        self,
        document: bytes,
        timestamp_token: str
    ) -> dict:
        """
        Verify qualified timestamp

        Confirms document existed at claimed time
        """
        doc_hash = hashlib.sha256(document).digest()
        token = base64.b64decode(timestamp_token)

        # Verify with TSA
        verification = await self._verify_timestamp_token(doc_hash, token)

        return {
            "valid": verification["valid"],
            "timestamp": verification["timestamp"],
            "tsa_certificate_valid": verification["tsa_valid"],
            "on_trusted_list": verification["on_trusted_list"]
        }
```

## QWAC Certificates for PSD2

Qualified Website Authentication Certificates (QWAC) are required for TPPs under PSD2.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class QWACRole(Enum):
    PSP_AI = "PSP_AI"   # Account Information
    PSP_PI = "PSP_PI"   # Payment Initiation
    PSP_IC = "PSP_IC"   # Card Issuing
    PSP_AS = "PSP_AS"   # Account Servicing

@dataclass
class QWACInfo:
    """Information extracted from QWAC certificate"""
    organization_name: str
    organization_id: str
    country: str
    roles: list[QWACRole]
    authorization_number: str
    nca: str  # National Competent Authority
    valid_from: datetime
    valid_until: datetime

class QWACValidator:
    """
    Validate PSD2 QWAC certificates

    Ensures TPP is authorized by competent authority
    """

    async def validate_qwac(
        self,
        certificate_pem: str
    ) -> QWACInfo:
        """
        Validate QWAC certificate and extract TPP information

        Checks:
        1. Certificate chain validity
        2. QTSP on EU Trusted List
        3. Certificate not revoked
        4. TPP authorization still valid
        """
        # Parse certificate
        cert_info = self._parse_certificate(certificate_pem)

        # Extract PSD2 roles from certificate extensions
        roles = self._extract_psd2_roles(cert_info)

        # Validate certificate chain
        chain_valid = await self._validate_chain(certificate_pem)
        if not chain_valid:
            raise InvalidCertificateError("Certificate chain validation failed")

        # Check revocation status (OCSP/CRL)
        revocation = await self._check_revocation(certificate_pem)
        if revocation["revoked"]:
            raise RevokedCertificateError("Certificate has been revoked")

        # Verify QTSP is on EU Trusted List
        on_trusted_list = await self._check_eu_trusted_list(
            cert_info["issuer"]
        )
        if not on_trusted_list:
            raise UntrustedIssuerError("Issuer not on EU Trusted List")

        return QWACInfo(
            organization_name=cert_info["subject"]["O"],
            organization_id=cert_info["subject"]["organizationIdentifier"],
            country=cert_info["subject"]["C"],
            roles=roles,
            authorization_number=cert_info["psd2_authorization_number"],
            nca=cert_info["psd2_nca"],
            valid_from=cert_info["not_before"],
            valid_until=cert_info["not_after"]
        )

    def check_qwac(
        self,
        qwac_info: QWACInfo,
        required_role: QWACRole
    ) -> bool:
        """
        Check if QWAC has required role for operation

        E.g., AISP operations require PSP_AI role
        """
        return required_role in qwac_info.roles
```

## Electronic Seals

Electronic seals authenticate organizational documents.

```python
class QualifiedSealService:
    """
    eIDAS Qualified Electronic Seal Service

    For authenticating organizational documents
    """

    async def create_seal(
        self,
        document: bytes,
        organization_certificate: str
    ) -> dict:
        """
        Create qualified electronic seal

        Authenticates origin and integrity of document
        """
        doc_hash = hashlib.sha256(document).digest()

        # Create seal with organization certificate
        seal_value = await self._create_seal(
            doc_hash,
            organization_certificate
        )

        # Add qualified timestamp
        timestamp = await self._add_timestamp(seal_value)

        return {
            "seal_id": self._generate_seal_id(),
            "seal_value": base64.b64encode(seal_value).decode(),
            "timestamp": timestamp,
            "organization": self._extract_org_name(organization_certificate),
            "created_at": datetime.utcnow().isoformat()
        }

    async def verify_seal(
        self,
        document: bytes,
        seal_value: str
    ) -> dict:
        """
        Verify electronic seal

        Confirms document authenticity and origin
        """
        verification = await self._verify_seal(
            document,
            base64.b64decode(seal_value)
        )

        return {
            "valid": verification["valid"],
            "organization": verification["organization"],
            "sealed_at": verification["timestamp"],
            "qualified": verification["is_qualified"]
        }
```

## Long-Term Preservation (LTV)

Ensure signatures remain verifiable over time.

```python
class LongTermValidation:
    """
    Long-term validation for electronic signatures

    Embeds validation data for future verification
    """

    async def create_ltv_signature(
        self,
        document: bytes,
        signature: SignatureResult
    ) -> SignatureResult:
        """
        Create LTV-enabled signature

        Embeds certificates, OCSP responses, and timestamps
        """
        # Get complete certificate chain
        cert_chain = await self._get_full_chain(signature.certificate_chain[0])

        # Get OCSP responses for all certificates
        ocsp_responses = await self._get_ocsp_responses(cert_chain)

        # Add archive timestamp
        archive_timestamp = await self._get_qualified_timestamp(
            signature.signature_value
        )

        # Embed all validation data
        ltv_signature = await self._embed_ltv_data(
            signature=signature,
            certificates=cert_chain,
            ocsp_responses=ocsp_responses,
            archive_timestamp=archive_timestamp
        )

        return ltv_signature

    async def preserve_signature(
        self,
        signature: SignatureResult
    ) -> SignatureResult:
        """
        Add preservation data to existing signature

        Call periodically to extend validity beyond certificate expiry
        """
        # Add new timestamp
        new_timestamp = await self._get_qualified_timestamp(
            signature.signature_value
        )

        # Add current validation data
        return await self._add_preservation_data(signature, new_timestamp)
```
