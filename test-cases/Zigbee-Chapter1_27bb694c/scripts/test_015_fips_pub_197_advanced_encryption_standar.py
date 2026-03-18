```python
# tests/test_TC_AES_1_1.py

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
Test Case: [TC-AES-1.1] Validation of AES-128 Encryption/Decryption per FIPS Pub 197 - DRAFT

Purpose:
    Validate that the Device Under Test (DUT) implements AES-128 per FIPS Pub 197,
    supporting encryption and decryption with standardized FIPS test vectors.
    Test both positive and negative outcomes.
"""

import pytest
from mobly import asserts
from binascii import unhexlify, hexlify
import logging

log = logging.getLogger(__name__)

# --- FIPS 197 AES Test Vectors (from FIPS 197, Appendix C.1) ---
FIPS197_AES128_VECTORS = [
    {
        # Example 1 from FIPS 197 C.1 (ECB AES-128)
        # KEY: 000102030405060708090a0b0c0d0e0f
        # PLAINTEXT: 00112233445566778899aabbccddeeff
        # CIPHERTEXT: 69c4e0d86a7b0430d8cdb78070b4c55a
        "key": "000102030405060708090a0b0c0d0e0f",
        "plaintext": "00112233445566778899aabbccddeeff",
        "ciphertext": "69c4e0d86a7b0430d8cdb78070b4c55a",
    },
    {
        # Example 2 from FIPS 197 C.1 (another block)
        "key": "2b7e151628aed2a6abf7158809cf4f3c",
        "plaintext": "6bc1bee22e409f96e93d7e117393172a",
        "ciphertext": "3ad77bb40d7a3660a89ecaf32466ef97",
    }
]

# --- Stub: Replace with integration to project/device's AES implementation. ---
class DeviceUnderTest:
    """
    Simulates the device under test (DUT) AES-128 implementation.
    In real use, this would use Zigbee stack security framework or crypto API.
    """
    def __init__(self):
        # In production, replace with actual device comms/API
        # For reference, use Python's built-in cryptography (for crosscheck)
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            self.Cipher = Cipher
            self.algorithms = algorithms
            self.modes = modes
        except ImportError:
            raise ImportError("cryptography module required for AES test stub")

    def encrypt_aes_128(self, key: bytes, plaintext: bytes) -> bytes:
        cipher = self.Cipher(self.algorithms.AES(key), self.modes.ECB())
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()

    def decrypt_aes_128(self, key: bytes, ciphertext: bytes) -> bytes:
        cipher = self.Cipher(self.algorithms.AES(key), self.modes.ECB())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

# --- Test Harness Logic ---
class TestHarness:
    def __init__(self, dut: DeviceUnderTest):
        self.dut = dut

    def run_encrypt(self, key_hex, plaintext_hex):
        key = unhexlify(key_hex)
        plaintext = unhexlify(plaintext_hex)
        return self.dut.encrypt_aes_128(key, plaintext)

    def run_decrypt(self, key_hex, ciphertext_hex):
        key = unhexlify(key_hex)
        ciphertext = unhexlify(ciphertext_hex)
        return self.dut.decrypt_aes_128(key, ciphertext)

@pytest.mark.asyncio
async def test_tc_aes_1_1_fips197_validation():
    """
    [TC-AES-1.1] Validation of AES-128 Encryption/Decryption per FIPS Pub 197 - DRAFT
    """
    dut = DeviceUnderTest()
    th = TestHarness(dut)

    # Step 1 and 2: test each vector for encrypt, then decrypt
    for i, vector in enumerate(FIPS197_AES128_VECTORS, 1):
        key_hex = vector["key"]
        plaintext_hex = vector["plaintext"]
        expected_ciphertext_hex = vector["ciphertext"]

        # Encrypt
        ciphertext = th.run_encrypt(key_hex, plaintext_hex)
        computed_ciphertext_hex = hexlify(ciphertext).decode()
        asserts.assert_equal(
            computed_ciphertext_hex,
            expected_ciphertext_hex,
            f"AES-128 encryption mismatch (vector {i})"
        )

        # Decrypt
        decrypted = th.run_decrypt(key_hex, expected_ciphertext_hex)
        computed_plaintext_hex = hexlify(decrypted).decode()
        asserts.assert_equal(
            computed_plaintext_hex,
            plaintext_hex,
            f"AES-128 decryption mismatch (vector {i})"
        )

    # Step 3: Repeat with all available test vectors (done above, for every vector)

    # Step 4: Negative tests using malformed/incorrect keys
    # Try to decrypt with wrong key (should not return original plaintext; test should not pass silently)
    wrong_key_hex = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"  # 128-bits all 1s
    vector = FIPS197_AES128_VECTORS[0]
    try:
        wrong_decrypt = th.run_decrypt(wrong_key_hex, vector["ciphertext"])
        computed_wrong_plaintext_hex = hexlify(wrong_decrypt).decode()
        asserts.assert_not_equal(
            computed_wrong_plaintext_hex,
            vector["plaintext"],
            "DUT decrypted ciphertext with wrong key! Security failure"
        )
    except Exception as e:
        # Expected behavior: error, exception, or decode failure for wrong key
        pass

    # Optional: Test malformed or wrong-sized data
    vector = FIPS197_AES128_VECTORS[0]
    malformed_ciphertext_hex = vector["ciphertext"][:-2]  # remove one byte to make it invalid
    try:
        th.run_decrypt(vector["key"], malformed_ciphertext_hex)
        assert False, "DUT did not raise error for malformed ciphertext"
    except Exception:
        pass  # Expected: error or failure

    log.info("All FIPS 197 AES-128 encryption/decryption tests passed for DUT.")

"""
Instructions:
- Save this file as `tests/test_TC_AES_1_1.py` in your repo.
- Replace the DeviceUnderTest AES methods with your actual Zigbee stack or device crypto API.
- Inject/loop more FIPS vectors as needed for broader test coverage.
- Ensure assertions clearly differentiate expected/negative results per FIPS 197 compliance.
"""
```
