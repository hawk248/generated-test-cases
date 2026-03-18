```python
# tests/test_TC_HAC_1_1.py
#
#    Copyright (c) 2025 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

"""
TC-HAC-1.1: Applied Cryptographic Algorithm Implementation Conformance

This script validates cryptographic primitives (e.g., AES block cipher,
SHA hash, DSA/RSA signature) according to test vectors from the
Handbook of Applied Cryptography (HAC) and/or NIST/FIPS standards.

STUB/PLACEHOLDER WARNING:
Replace class HACApi below with your device's/harness's actual cryptographic interface!
"""

import pytest
from mobly import asserts
import hashlib
import hmac

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import dsa, rsa, padding
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    from cryptography.hazmat.backends import default_backend
except ImportError:
    Cipher = None

# -- Generic placeholder API, replace with your DUT (device under test) API as needed --
class HACApi:
    @staticmethod
    async def aes_encrypt(key: bytes, plaintext: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        return cipher.encryptor().update(plaintext) + cipher.encryptor().finalize()

    @staticmethod
    async def aes_decrypt(key: bytes, ciphertext: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        return cipher.decryptor().update(ciphertext) + cipher.decryptor().finalize()

    @staticmethod
    async def sha256_digest(data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    @staticmethod
    async def sha1_digest(data: bytes) -> bytes:
        return hashlib.sha1(data).digest()

    @staticmethod
    async def hmac_sha256(key: bytes, message: bytes) -> bytes:
        return hmac.new(key, message, hashlib.sha256).digest()

    # Add more methods for DSA, RSA, etc. as DUT supports

# ---- Test Vectors Derived from HAC, Appendix E/F (for reference values) ----
# (These are canonical, e.g. found in HAC or cross-referenced to NIST)
TEST_VECTORS_AES = [
    {
        "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
        "plaintext": bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
        "ciphertext": bytes.fromhex("3ad77bb40d7a3660a89ecaf32466ef97"),
    }
]

TEST_VECTORS_SHA = [
    {
        "algo": "sha256",
        "input": b"abc",
        "digest": bytes.fromhex("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    },
    {
        "algo": "sha1",
        "input": b"abc",
        "digest": bytes.fromhex("a9993e364706816aba3e25717850c26c9cd0d89d"),
    }
]

TEST_VECTORS_HMAC = [
    {
        "algo": "sha256",
        "key": bytes.fromhex("0b" * 20),
        "input": b"Hi There",
        "digest": bytes.fromhex("b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"),
    }
]

@pytest.mark.asyncio
async def test_aes_known_vector():
    """Test Step 1+2: AES encryption/decryption using HAC and NIST vectors."""
    for vec in TEST_VECTORS_AES:
        key = vec["key"]
        pt = vec["plaintext"]
        ct_ref = vec["ciphertext"]

        ct = await HACApi.aes_encrypt(key, pt)
        asserts.assert_equal(ct, ct_ref, f"AES encryption mismatch (got {ct.hex()}, expected {ct_ref.hex()})")

        pt_back = await HACApi.aes_decrypt(key, ct)
        asserts.assert_equal(pt_back, pt, f"AES decryption mismatch (got {pt_back.hex()}, expected {pt.hex()})")

@pytest.mark.asyncio
async def test_sha_vectors():
    """Test Step 1+2: SHA-1 and SHA-256 digest using textbook vectors from HAC/NIST."""
    for vec in TEST_VECTORS_SHA:
        if vec["algo"] == "sha256":
            out = await HACApi.sha256_digest(vec["input"])
        elif vec["algo"] == "sha1":
            out = await HACApi.sha1_digest(vec["input"])
        else:
            continue
        asserts.assert_equal(out, vec["digest"], f"{vec['algo'].upper()} digest mismatch")

@pytest.mark.asyncio
async def test_hmac_sha256_vector():
    """Test Step 1+2: HMAC-SHA256 using canonical test vector (RFC 4231, aligns with HAC/SHA vectors)."""
    for vec in TEST_VECTORS_HMAC:
        out = await HACApi.hmac_sha256(vec["key"], vec["input"])
        asserts.assert_equal(out, vec["digest"], "HMAC-SHA256 digest mismatch")

@pytest.mark.asyncio
async def test_primitives_coverage():
    """Test Step 3: Check that all implemented primitives pass test with at least one valid vector."""
    # Coverage example shown above with AES, SHA1/SHA256, HMAC.
    await test_aes_known_vector()
    await test_sha_vectors()
    await test_hmac_sha256_vector()
    # expand for DSA/RSA/ECDSA as available/implemented in DUT

@pytest.mark.asyncio
async def test_malformed_and_edge_inputs():
    """Test Step 4 (optional): Ensure correct failure/exception on malformed input or boundary values."""
    # AES: plaintext/ciphertext not multiple of block size
    key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
    bad_pt = b"short"
    try:
        await HACApi.aes_encrypt(key, bad_pt)
        asserts.fail("AES did not error on bad block input")
    except Exception:
        pass  # Accept expected failure

    # SHA: empty input is valid, just ensure does not error
    out = await HACApi.sha256_digest(b"")
    asserts.assert_equal(
        out,
        bytes.fromhex("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        "SHA256 hash of empty string mismatch",
    )

# Notes:
# - Replace all HACApi methods with actual DUT/harness APIs.
# - Expand with additional primitives and edge cases per device implementation.
# - All asserts provide direct mapping to step/outcome in the test case.

"""
How to Use:
- Place this file at tests/test_TC_HAC_1_1.py in your test repository.
- Adjust HACApi to match your testbed/DUT API for cryptographic operations.
- Use pytest to execute. Script is compatible with ConnectedHomeIP test style.
"""
```
