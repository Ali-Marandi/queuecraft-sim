"""Cryptographically signed evidence artifacts for QueueCraft Enterprise AI.

The signer uses Ed25519 from the project's existing cryptography dependency.
Signatures authenticate an artifact against a caller-supplied public key; they
are not a substitute for key management, identity, timestamping, or legal
non-repudiation services.
"""
from __future__ import annotations

import base64
from typing import Any, Mapping

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from governance_hardening import canonical_json, fingerprint

SCHEMA_VERSION = 1


def generate_keypair() -> tuple[str, str]:
    """Generate PEM-encoded Ed25519 private/public keys."""
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem.decode("utf-8"), public_pem.decode("utf-8")


def _load_private_key(pem: str) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("private key must be an Ed25519 key")
    return key


def _load_public_key(pem: str) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(pem.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("public key must be an Ed25519 key")
    return key


def _payload_bytes(artifact: Mapping[str, Any]) -> bytes:
    return canonical_json(dict(artifact)).encode("utf-8")


def sign_artifact(artifact: Mapping[str, Any], *, signer_id: str, private_key_pem: str) -> dict[str, Any]:
    """Create a detached signature envelope for a canonical JSON artifact."""
    if not signer_id.strip():
        raise ValueError("signer_id is required")
    if not isinstance(artifact, Mapping):
        raise ValueError("artifact must be a mapping")
    private = _load_private_key(private_key_pem)
    payload = _payload_bytes(artifact)
    signature = private.sign(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "Ed25519",
        "signer_id": signer_id.strip(),
        "artifact_fingerprint": fingerprint(dict(artifact)),
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def verify_signature(artifact: Mapping[str, Any], envelope: Mapping[str, Any], *, public_key_pem: str) -> dict[str, Any]:
    """Verify the detached signature and the artifact fingerprint."""
    if not isinstance(artifact, Mapping) or not isinstance(envelope, Mapping):
        raise ValueError("artifact and envelope must be mappings")
    if envelope.get("schema_version") != SCHEMA_VERSION or envelope.get("algorithm") != "Ed25519":
        return {"valid": False, "reason": "unsupported_signature_envelope"}
    try:
        signature = base64.b64decode(str(envelope["signature"]), validate=True)
        supplied_fp = str(envelope["artifact_fingerprint"])
        actual_fp = fingerprint(dict(artifact))
        if supplied_fp != actual_fp:
            return {"valid": False, "reason": "artifact_fingerprint_mismatch", "supplied": supplied_fp, "calculated": actual_fp}
        _load_public_key(public_key_pem).verify(signature, _payload_bytes(artifact))
    except (KeyError, ValueError, TypeError):
        return {"valid": False, "reason": "invalid_signature_or_key"}
    return {"valid": True, "signer_id": envelope.get("signer_id"), "artifact_fingerprint": actual_fp}
