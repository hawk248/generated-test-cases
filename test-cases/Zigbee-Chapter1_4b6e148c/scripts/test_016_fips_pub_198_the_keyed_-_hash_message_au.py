```python
# tests/test_TC_HMAC_1_1.py
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
TC-HMAC-1.1: HMAC Keyed-Hash Message Authentication Code Compliance

Purpose:
    Validate that the DUT correctly implements the HMAC algorithm (per FIPS Pub 198),
    using official NIST/FIPS test vectors and cross-verifying with a trusted
    reference implementation (e.g., hashlib, hmac).
"""

import pytest
from mobly import asserts
import hmac as py_hmac
import hashlib

# Placeholder API for DUT HMAC invocation. In real test, use RPC/Cluster/API call.
class DUT_HMAC_API:
    """
    Replace these methods with true device/test harness calls for HMAC computation/verification.
    """
    @staticmethod
    async def compute_hmac(key: bytes, message: bytes, hash_name: str = "sha256") -> bytes:
        # In actual use, replace this with a real async call to the DUT's HMAC function.
        # Here, use host python for demonstration only.
        return py_hmac.new(key, message, getattr(hashlib, hash_name)).digest()

    @staticmethod
    async def validate_hmac_frame(key: bytes, message: bytes, hmac_value: bytes, hash_name: str = "sha256") -> bool:
        # Example: DUT verifies a frame's HMAC; in real test, call device API.
        expected = py_hmac.new(key, message, getattr(hashlib, hash_name)).digest()
        return hmac_value == expected


# --- Standard FIPS 198 Test Vectors for HMAC ---
# See FIPS 198 Appendix A/B and relevant NIST test vector repositories.
# The following are for SHA-256, as used in Zigbee and common IoT stacks.
SHA256_VECTORS = [
    # (Key, Message, Expected HMAC)
    (
        bytes.fromhex('0b'*20),
        b'Hi There',
        bytes.fromhex('b0344c61d8db38535ca8afceaf0bf12b'
                      '881dc200c9833da726e9376c2e32cff7')
    ),
    (
        b'Jefe',
        b'what do ya want for nothing?',
        bytes.fromhex('5bdcc146bf60754e6a042426089575c7'
                      '5a003f089d2739839dec58b964ec3843')
    ),
    (
        bytes.fromhex('aa'*20),
        bytes.fromhex('dd'*50),
        bytes.fromhex('773ea91e36800e46854db8ebd09181a7'
                      '2959098b3ef8c122d9635514ced565fe')
    ),
    # Test with truncated HMAC, not for strict byte-matching: use first 16 bytes, etc.
    # More legacy and corner cases can be added as required.
]

@pytest.mark.asyncio
@pytest.mark.parametrize("key, msg, hmac_ref", SHA256_VECTORS)
async def test_hmac_computation_against_reference(key, msg, hmac_ref):
    """
    Step 1 & 2: Compute DUT HMAC and compare against known reference
    """
    # Step 1: TH sends key+msg to DUT, requests computation
    dut_output = await DUT_HMAC_API.compute_hmac(key, msg, hash_name="sha256")
    # Step 2: TH computes using same reference (handled by vector)
    asserts.assert_equal(
        dut_output, hmac_ref,
        f"HMAC output mismatch: got {dut_output.hex()}, expected {hmac_ref.hex()}"
    )

@pytest.mark.asyncio
async def test_hmac_vector_coverage():
    """
    Step 3: Iterate through all standard HMAC vectors.
    (Already achieved with parameterized tests above, but also test negative cases.)
    """
    # Try empty message, long key, etc.
    key = b'\x0c' * 20
    msg = b'Test With Truncation'
    expected = bytes.fromhex('415fad6271580a531d4179bc891d87a6')
    # Only check first 16 bytes (truncated HMAC case from RFC4231)
    dut_output = await DUT_HMAC_API.compute_hmac(key, msg, hash_name="sha256")
    asserts.assert_equal(
        dut_output[:16], expected,
        f"HMAC truncation check: got {dut_output[:16].hex()}, expected {expected.hex()}"
    )

@pytest.mark.asyncio
async def test_hmac_validate_frame_accept_and_reject():
    """
    Step 4: Verify that DUT accepts valid frame (matching key/HMAC), rejects tampered frame.
    """
    key = bytes.fromhex('0b'*20)
    msg = b'Hi There'
    reference_hmac = await DUT_HMAC_API.compute_hmac(key, msg)
    # Should accept unchanged
    accept = await DUT_HMAC_API.validate_hmac_frame(key, msg, reference_hmac)
    asserts.assert_true(accept, "DUT did not accept valid frame/HMAC.")

    # Should reject on tamper (change last byte)
    altered = reference_hmac[:-1] + bytes([reference_hmac[-1] ^ 0xFF])
    reject = await DUT_HMAC_API.validate_hmac_frame(key, msg, altered)
    asserts.assert_false(reject, "DUT did not reject INVALID frame/HMAC.")

# Save as: tests/test_TC_HMAC_1_1.py

"""
NOTES:
- Replace DUT_HMAC_API methods with real cluster command, attribute, REST call, or other device API.
- Mobly asserts are used per project-chip/connectedhomeip conventions.
- Add more SHA1, SHA-512, or Zigbee-relevant vectors for exhaustive compliance testing.
- These scripts are CI-compatible and can be run using pytest as with other MatterBaseTest-style test scripts.
"""
```
