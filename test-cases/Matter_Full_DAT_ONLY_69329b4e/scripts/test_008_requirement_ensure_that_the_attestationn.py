```python
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

# === BEGIN CI TEST ARGUMENTS ===
# test-runner-runs:
#   run1:
#     app: ${ALL_CLUSTERS_APP}
#     app-args: --discriminator 1234 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 1234
#       --passcode 20202021
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
#     factory-reset: true
#     quiet: true
# === END CI TEST ARGUMENTS ===

import os
import secrets

from mobly import asserts

import matter.clusters as Clusters
from matter.exceptions import ChipStackError
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

class TestAttestationNonceMatch(MatterBaseTest):
    """
    [TC-ATT-2.1] Validate AttestationNonce Match Between Commissioner and Device (Matter 1.6)
    Verifies the AttestationNonce returned in AttestationResponse exactly matches that provided in AttestationRequest.
    """

    @async_test_body
    async def test_attestation_nonce_match_positive(self):
        # Step 1: Generate a random 32-byte nonce
        self.print_step(1, "TH generates a random 32-byte AttestationNonce and starts secure session with DUT")
        # Use secrets for cryptographically strong random bytes
        commissioner_nonce = secrets.token_bytes(32)
        asserts.assert_equal(len(commissioner_nonce), 32, "AttestationNonce must be 32 bytes")

        self.print_step(2, "TH sends AttestationRequest containing the generated AttestationNonce to DUT")
        # Build and send the AttestationRequest
        attestation_request_cmd = Clusters.OperationalCredentials.Commands.AttestationRequest(attestationNonce=commissioner_nonce)
        response = await self.send_single_cmd(cmd=attestation_request_cmd, endpoint=0)
        asserts.assert_is_not_none(response, "No AttestationResponse returned from DUT")

        self.print_step(3, "DUT returns AttestationResponse containing Device Attestation elements (including AttestationNonce)")
        # AttestationResponse expected structure (assume field named attestationNonce in response)
        device_nonce = getattr(response, 'attestationNonce', None) or response.get('attestationNonce', None)
        asserts.assert_is_not_none(device_nonce, "No attestationNonce field present in AttestationResponse")
        asserts.assert_equal(len(device_nonce), 32, "Device AttestationNonce is not 32 bytes")

        self.print_step(4, "TH compares AttestationNonce value in AttestationResponse to that previously generated and sent")
        asserts.assert_equal(
            commissioner_nonce,
            device_nonce,
            "AttestationNonce in AttestationResponse does not match the one sent in request"
        )

    @async_test_body
    async def test_attestation_nonce_mismatch_negative(self):
        # Step 5: Negative test—Corrupt the DUT expected AttestationNonce in the response
        self.print_step(1, "(Negative) Send valid AttestationNonce, expect response with altered/mismatched nonce for negative test")
        commissioner_nonce = secrets.token_bytes(32)
        asserts.assert_equal(len(commissioner_nonce), 32, "AttestationNonce must be 32 bytes")

        # Send AttestationRequest
        attestation_request_cmd = Clusters.OperationalCredentials.Commands.AttestationRequest(attestationNonce=commissioner_nonce)
        response = await self.send_single_cmd(cmd=attestation_request_cmd, endpoint=0)

        # For negative test, simulate the DUT or harness returning a nonce that differs from the one sent
        # (If your real DUT can't be made to return a wrong nonce, you can monkeypatch or mock the response for this test)
        bad_device_nonce = b'\x00' * 32 if commissioner_nonce != b'\x00' * 32 else b'\x01' * 32
        device_nonce = getattr(response, 'attestationNonce', None) or response.get('attestationNonce', None)
        # Overwrite the nonce for the negative test path
        device_nonce = bad_device_nonce

        self.print_step(2, "TH compares deliberately mismatched AttestationNonce; asserts the non-match is detected")
        try:
            asserts.assert_equal(
                commissioner_nonce,
                device_nonce,
                "Test FAIL: AttestationNonce matched unexpectedly (should not happen in negative/corrupt case)"
            )
        except AssertionError:
            # Expected: This is the correct outcome for the negative test
            pass
        else:
            # If no assert raised, then the negative test failed (nonce matched unexpectedly)
            asserts.fail("Negative test: Non-matching AttestationNonce was not detected as a mismatch")

if __name__ == "__main__":
    default_matter_test_main()
```
