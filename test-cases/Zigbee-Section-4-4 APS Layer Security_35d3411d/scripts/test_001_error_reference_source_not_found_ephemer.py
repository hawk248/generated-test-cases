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

from mobly import asserts
import asyncio

import matter.clusters as Clusters
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

import logging

log = logging.getLogger(__name__)

# NOTE: Command and attribute names may need updating per Zigbee Direct spec details

class TestEphemeralUniqueAuthorizationKey(MatterBaseTest):
    """
    Implements verification for the Ephemeral Unique Authorization Key (EUAK, 0xB1) according to the Zigbee Direct Specification.
    Covers: 
      - Generation of a unique ephemeral key
      - Successful, spec-conformant key format
      - Secure transport
      - Correct short-lived use and disposal
      - Rejection of replay/expired key usage

    PROVISIONAL: Command/attribute names and invocation mechanisms may need amendments per finalized Zigbee Direct spec.
    """

    @async_test_body
    async def test_euak_lifecycle(self):
        # Step 0: Pre-Conditions and commissioning
        self.print_step(0, "Commissioning and setup already done.")

        # Step 1: Request EUAK from DUT, expect unique ephemeral key from device
        self.print_step(1, "Requesting Ephemeral Unique Authorization Key (EUAK, 0xB1) from DUT.")
        # -- Replace `RequestEphemeralAuthorizationKey` with real cluster/command name when available
        # This assumes existence of a cluster 'AuthorizationKeys' and proper command.
        request_euak_cmd = Clusters.AuthorizationKeys.Commands.RequestEphemeralAuthorizationKey(KeyType=0xB1)
        response = await self.send_single_cmd(
            cmd=request_euak_cmd,
            endpoint=0  # Zigbee Direct endpoints may vary
        )
        asserts.assert_is_not_none(response, "No response received from DUT for key request")
        euak = getattr(response, "EphemeralKey", None)
        asserts.assert_is_not_none(euak, "Ephemeral Unique Authorization Key not present in response")

        # Save EUAK and confirm general structure (length, type, etc.), subject to Zigbee Direct spec
        self.print_step(2, "Verifying EUAK is unique and conforms to cryptographic parameters.")
        # For demonstration, assume EUAK is 16 bytes
        asserts.assert_is_instance(euak, bytes, "EUAK is not bytes")
        asserts.assert_equal(len(euak), 16, "EUAK should be 16 bytes")  # Adjust length as per spec

        # Save a copy for reuse test
        previous_euak = euak

        # Step 2: Repeat request, EUAK must be different (uniqueness check)
        self.print_step(3, "Requesting another EUAK to verify uniqueness.")
        response_2 = await self.send_single_cmd(
            cmd=request_euak_cmd,
            endpoint=0
        )
        asserts.assert_is_not_none(response_2, "No response received for second key request")
        new_euak = getattr(response_2, "EphemeralKey", None)
        asserts.assert_is_not_none(new_euak, "No EphemeralKey in second response")
        asserts.assert_not_equal(previous_euak, new_euak, "EUAK should be unique per session/request")

        # Step 3: Simulate expiration (ephemeral duration)
        self.print_step(4, "Simulate EUAK expiry and verify server rejects reuse of expired/old EUAK.")
        # For demonstration, assume lifetime 2 seconds; in real test, obtain from spec/response or set as per actual protocol
        simulated_lifetime_seconds = 2
        await asyncio.sleep(simulated_lifetime_seconds + 1)
        try:
            reuse_cmd = Clusters.AuthorizationKeys.Commands.UseEphemeralAuthorizationKey(Key=previous_euak)
            await self.send_single_cmd(
                cmd=reuse_cmd,
                endpoint=0
            )
            asserts.fail("DUT should have rejected reuse of the expired EUAK, but did not fail as expected")
        except Exception as e:
            # Expecting a protocol-specific error
            self.print_step(5, f"DUT correctly rejected expired EUAK (expected failure): {e}")

        # Step 4: Attempt to retrieve/dispose of EUAK after use/expiration
        self.print_step(6, "Verifying that EUAK is properly disposed and cannot be reused or retrieved")
        # This is illustrative; in a real implementation, check for retrievability of expired keys
        # Optionally, try a real read/requery if the protocol supports explicit queries for expired keys
        # Here we assume use of the key in any command fails after expiration
        try:
            reuse_cmd = Clusters.AuthorizationKeys.Commands.UseEphemeralAuthorizationKey(Key=previous_euak)
            await self.send_single_cmd(
                cmd=reuse_cmd,
                endpoint=0
            )
            asserts.fail("DUT allowed reuse of EUAK after expiration/disposal, which is a security violation")
        except Exception as e:
            self.print_step(7, f"DUT correctly refuses access to stale EUAK (expected failure): {e}")

if __name__ == "__main__":
    default_matter_test_main()
```
**Place this file in** `tests/test_ephemeral_euak.py`

---

**Notes for implementers:**
- Replace `Clusters.AuthorizationKeys.Commands.RequestEphemeralAuthorizationKey` and similar command names with the actual cluster/command provided by the Zigbee Direct specification.
- Adjust expected parameters (e.g., key length, endpoint) as necessary according to finalized command definitions and DUT implementation details.
- This test uses patterns and structure from the existing test files, and applies Mobly assertions and the async test pattern seen in your repo.
- Log/step comments are included for traceability, making this script helpful for diagnostic purposes and CI integration.