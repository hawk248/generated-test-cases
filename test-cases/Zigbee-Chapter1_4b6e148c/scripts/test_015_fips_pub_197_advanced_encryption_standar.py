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
TC-AES-1.1: Advanced Encryption Standard (AES) 128-bit Block Cipher Compliance

Purpose:
    Validate that the DUT implements 128-bit AES per FIPS Pub 197 using well-known test vectors.
    Check both encryption and decryption, with exact match to FIPS reference outputs.
"""

import pytest
from mobly import asserts

# Placeholder: Replace or connect to DUT's AES-128 interface.
# For actual Zigbee/Matter context, use your security cluster, API, or binding here.
class DUT_AES_API:
    """Replace these static methods with real device/test-harness calls"""

    @staticmethod
    async def encrypt(key: bytes, plaintext: bytes) -> bytes:
        """
        AES-128 Encryption interface.
        Replace with actual hardware API, Zigbee cluster, or HAL/RPC.
        """
        # Demo stub using Python's `cryptography` library for stand-in
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()

    @staticmethod
    async def decrypt(key: bytes, ciphertext: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

# Standard FIPS-197 (Annex C) test vectors for AES-128-ECB
# See: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf
FIPS_AES_128_VECTORS = [
    # (KEY, PLAINTEXT, CIPHERTEXT)
    (
        bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
        bytes.fromhex("00112233445566778899AABBCCDDEEFF"),
        bytes.fromhex("69C4E0D86A7B0430D8CDB78070B4C55A")
    ),
    # Additional FIPS vectors can be added here as (key, pt, ct)
    (
        bytes.fromhex("10A58869D74BE5A374CF867CFB473859"),
        bytes.fromhex("00000000000000000000000000000000"),
        bytes.fromhex("6D251E6944B051E04EAA6FB4DBF78465")
    ),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("key, pt, ct", FIPS_AES_128_VECTORS)
async def test_aes_encrypt_known_vector(key, pt, ct):
    """
    Step 1: TH sends known Key and Input to DUT's AES encrypt operation
            Expected to match public FIPS 197 output exactly.
    """
    result = await DUT_AES_API.encrypt(key, pt)
    asserts.assert_equal(result, ct, 
        f"Encryption failed: got {result.hex()}, expected {ct.hex()}")

@pytest.mark.asyncio
@pytest.mark.parametrize("key, pt, ct", FIPS_AES_128_VECTORS)
async def test_aes_decrypt_known_vector(key, pt, ct):
    """
    Step 2: TH sends ciphertext with same Key to DUT's AES decrypt operation
            Expected to yield the original plaintext exactly.
    """
    result = await DUT_AES_API.decrypt(key, ct)
    asserts.assert_equal(result, pt, 
        f"Decryption failed: got {result.hex()}, expected {pt.hex()}")

@pytest.mark.asyncio
async def test_aes_encrypt_decrypt_cycle():
    """
    Step 3: Iterate extra vectors, check encrypt-then-decrypt cycle
    """
    for (key, pt, ct) in FIPS_AES_128_VECTORS:
        enc = await DUT_AES_API.encrypt(key, pt)
        dec = await DUT_AES_API.decrypt(key, enc)
        asserts.assert_equal(enc, ct, f"AES encrypt mismatch for input={pt.hex()}, key={key.hex()}")
        asserts.assert_equal(dec, pt, f"AES decrypt mismatch for cipher={enc.hex()}, key={key.hex()}")

"""
Notes:
- DUT_AES_API is the placeholder to be replaced with your actual tested device's or cluster's AES implementation.
- This example uses Python's 'cryptography' for stubbing only its reference vectors; real tests MUST use on-device code.
- The test is fully async and compatible with the pytest runner and mobly asserts used in Project CHIP/ConnectedHomeIP Python suite.
- Add more FIPS or Zigbee-specific vectors (including edge-cases, CBC, etc.) as needed for full coverage.
"""
```
**How to use:**
- Place this script as `tests/test_TC_AES_1_1.py`
- Replace the `DUT_AES_API` methods with actual Zigbee/Matter/CHIP AES API calls.
- Use your test runner/CI/integration as with existing project-chip Python tests.