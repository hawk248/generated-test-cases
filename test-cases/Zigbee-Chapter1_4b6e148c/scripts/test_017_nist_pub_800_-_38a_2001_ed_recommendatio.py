```python
# tests/test_TC_CRYPTO_1_1.py
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
TC-CRYPTO-1.1: Block Cipher Modes of Operation Compliance (NIST 800-38A)

Validates that the DUT implements block cipher encryption/decryption for various
modes (ECB, CBC, CFB, OFB, CTR) in compliance with NIST Special Pub 800-38A.
Test vectors are taken from NIST 800-38A Appendices.
Replace the CryptoDUTApi interface with actual DUT/harness code.
"""

import pytest
from mobly import asserts

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    Cipher = algorithms = modes = None

# --------- Placeholder DUT/Harness Crypto Interface -----------
class CryptoDUTApi:
    """Mock/test API for block cipher encryption/decryption (replace with DUT/harness APIs)."""

    @staticmethod
    async def encrypt(mode: str, key: bytes, iv: bytes, plaintext: bytes) -> bytes:
        # Using cryptography package for testing only; replace logic for real DUT api
        cipher = CryptoDUTApi._get_cipher(mode, key, iv)
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()
    
    @staticmethod
    async def decrypt(mode: str, key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
        cipher = CryptoDUTApi._get_cipher(mode, key, iv)
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def _get_cipher(mode, key, iv):
        """Return cryptography Cipher object for test; adapt as needed."""
        if Cipher is None:
            raise RuntimeError("cryptography package is not installed!")
        aes = algorithms.AES(key)
        m = {
            "ECB": modes.ECB(),
            "CBC": modes.CBC(iv),
            "CFB": modes.CFB(iv),
            "OFB": modes.OFB(iv),
            "CTR": modes.CTR(iv),
        }
        return Cipher(aes, m[mode])

# ------------- NIST 800-38A Test Vectors ---------------
# All vectors: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38a.pdf
VECTORS = {
    "ECB": [
        {
            "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
            "pt":  bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "ct":  bytes.fromhex("3ad77bb40d7a3660a89ecaf32466ef97"),
        }
    ],
    "CBC": [
        {
            "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
            "iv":  bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
            "pt":  bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "ct":  bytes.fromhex("7649abac8119b246cee98e9b12e9197d"),
        }
    ],
    "CFB": [
        {
            "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
            "iv":  bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
            "pt":  bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "ct":  bytes.fromhex("3b3fd92eb72dad20333449f8e83cfb4a"),
        }
    ],
    "OFB": [
        {
            "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
            "iv":  bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
            "pt":  bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "ct":  bytes.fromhex("3b3fd92eb72dad20333449f8e83cfb4a"),
        }
    ],
    "CTR": [
        {
            "key": bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"),
            "iv":  bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"),
            "pt":  bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "ct":  bytes.fromhex("874d6191b620e3261bef6864990db6ce"),
        }
    ],
}

@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["ECB", "CBC", "CFB", "OFB", "CTR"])
async def test_block_cipher_encrypt_decrypt(mode):
    """
    Steps 1-3 (positive): Encrypt and decrypt for each supported mode.
    """
    for vector in VECTORS[mode]:
        key = vector["key"]
        pt = vector["pt"]
        ct_expected = vector["ct"]
        iv = vector.get("iv", b"")

        # Step 1: Encrypt and compare
        ct_actual = await CryptoDUTApi.encrypt(mode, key, iv, pt)
        asserts.assert_equal(
            ct_actual, ct_expected,
            f"{mode} encrypt: DUT ciphertext mismatch (expected {ct_expected.hex()}, got {ct_actual.hex()})"
        )

        # Step 2: Decrypt and compare
        pt_actual = await CryptoDUTApi.decrypt(mode, key, iv, ct_actual)
        asserts.assert_equal(
            pt_actual, pt,
            f"{mode} decrypt: DUT plaintext mismatch (expected {pt.hex()}, got {pt_actual.hex()})"
        )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,invalid_iv_length",
    [
        ("CBC", 0),          # ECB has no IV, but CBC requires 16 bytes
        ("CFB", 4),          # Too short IV for block operation
        ("OFB", 15),         # Invalid IV length
        ("CTR", 8),          # Should be 16 bytes for AES
    ]
)
async def test_cipher_mode_invalid_iv(mode, invalid_iv_length):
    """
    Step 4: TH attempts encryption with invalid parameters (e.g. wrong IV length).
    """
    vector = VECTORS[mode][0]
    key = vector["key"]
    plaintext = vector["pt"]
    bad_iv = bytes([0x01] * invalid_iv_length)
    try:
        _ = await CryptoDUTApi.encrypt(mode, key, bad_iv, plaintext)
        asserts.fail(f"{mode} mode did not error on invalid IV length ({invalid_iv_length})")
    except Exception as e:
        assert "invalid" in str(e).lower() or isinstance(e, ValueError)

# Note:
# - If DUT supports only a subset of modes, adjust VECTORS and parametrization accordingly.
# - Expand vectors for coverage or use full NIST test suites as needed.
# - CryptoDUTApi should be replaced by your real harness/DUT invocation logic, with
#   async handling mapped to device API, RPC, or CLI.

"""
USAGE:
- Place this file as tests/test_TC_CRYPTO_1_1.py
- Run using pytest in your environment:
    pytest tests/test_TC_CRYPTO_1_1.py
- To adapt for ConnectedHomeIP, link CryptoDUTApi methods to actual test infrastructure.
"""

```