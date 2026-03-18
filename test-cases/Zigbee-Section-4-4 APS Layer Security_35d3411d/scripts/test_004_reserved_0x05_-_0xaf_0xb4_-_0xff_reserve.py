```python
#
#    Copyright (c) 2024 Project CHIP Authors
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
#     factory-reset: true
#     quiet: true
#     app-args: --discriminator 1234 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 1234
#       --passcode 20202021
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
# === END CI TEST ARGUMENTS ===

import pytest
from mobly import asserts

# Placeholder: Replace these stubs with actual Zigbee Direct/APS/transport key library calls as available in your environment.
# These would interface with your Zigbee test harness APIs or driver layer.
class APSMETransportKey:
    """Stub for APSME-TRANSPORT-KEY.request primitive generator."""
    @staticmethod
    def send_transport_key_request(dut, key_type, key_data=b""):
        """
        Simulate sending APSME-TRANSPORT-KEY.request with given key_type to DUT.
        Returns a tuple: (status, command_generated)
        status: 'success', 'error', or another string.
        command_generated: bool indicating whether a Transport-Key command was actually emitted by DUT.
        Replace with real interactions or mocks as appropriate.
        """
        # Simulate real response: in actual test, invoke your commissioning/test harness library
        reserved_ranges = (
            list(range(0x05, 0xB0)),
            list(range(0xB4, 0x100))  # up to, including 0xFF
        )
        reserved_values = set(reserved_ranges[0] + reserved_ranges[1])
        if key_type in reserved_values:
            return ("error", False)
        else:
            return ("success", True)  # For positive cases; not checked here.

@pytest.mark.asyncio
async def test_reserved_standard_key_types_are_rejected():
    """
    TC-APSSEC-4.1: Reserved StandardKeyType Values Are Not Accepted by APSME-TRANSPORT-KEY.request

    Purpose:
        Verify that the APSME-TRANSPORT-KEY.request primitive rejects reserved StandardKeyType values
        and does NOT emit Transport-Key commands for such requests.
    """

    # Step 0: Setup DUT and Test Harness (TH)
    # [In real test, this will be handled by commissioning scripts/fixtures]
    dut = "DUT_PLACEHOLDER"  # Replace with connected device handle
    th = "TH_PLACEHOLDER"    # Replace with test harness object/connection

    # Step 1: Send APSME-TRANSPORT-KEY.request with StandardKeyType 0x05 (reserved)
    status_05, generated_05 = APSMETransportKey.send_transport_key_request(dut, 0x05)
    asserts.assert_not_equal(status_05, "success",
        "DUT accepted reserved StandardKeyType 0x05! This is not compliant.")
    asserts.assert_false(generated_05,
        "Transport-Key command was generated for reserved StandardKeyType 0x05.")

    # Step 2: Send with StandardKeyType 0xAF (reserved mid-range value)
    status_af, generated_af = APSMETransportKey.send_transport_key_request(dut, 0xAF)
    asserts.assert_not_equal(status_af, "success",
        "DUT accepted reserved StandardKeyType 0xAF! This is not compliant.")
    asserts.assert_false(generated_af,
        "Transport-Key command was generated for reserved StandardKeyType 0xAF.")

    # Step 3: Send with StandardKeyType 0xB4 (reserved, start of higher range)
    status_b4, generated_b4 = APSMETransportKey.send_transport_key_request(dut, 0xB4)
    asserts.assert_not_equal(status_b4, "success",
        "DUT accepted reserved StandardKeyType 0xB4! This is not compliant.")
    asserts.assert_false(generated_b4,
        "Transport-Key command was generated for reserved StandardKeyType 0xB4.")

    # Step 4: Send with StandardKeyType 0xFF (last reserved value)
    status_ff, generated_ff = APSMETransportKey.send_transport_key_request(dut, 0xFF)
    asserts.assert_not_equal(status_ff, "success",
        "DUT accepted reserved StandardKeyType 0xFF! This is not compliant.")
    asserts.assert_false(generated_ff,
        "Transport-Key command was generated for reserved StandardKeyType 0xFF.")

    # Step 5: Confirm that in all of the above, DUT never emitted a Transport-Key frame
    # (already asserted individually above, but provide summary assertion as well)
    all_generated = any([generated_05, generated_af, generated_b4, generated_ff])
    asserts.assert_false(
        all_generated,
        "DUT generated at least one Transport-Key command for reserved StandardKeyType values; this is a FAIL."
    )

    # Optional (if log or packet inspection is available)
    # Check logs/traffic to confirm no Transport-Key command frame was sent for any reserved type.
    # e.g., assert no outbound APS Transport-Key command in monitor logs matching session.

    # If any reserved key type is accepted and a Transport-Key command is issued, test FAILS.

# End of file: tests/test_TC_APSSEC_4_1_reserved_standardkeytypes.py
```
**Place this file as `tests/test_TC_APSSEC_4_1_reserved_standardkeytypes.py`.**
- Replace the stub class `APSMETransportKey` with your Zigbee test harness or actual protocol API if available.
- Integrate with fixtures for commissioning/setup if using a larger automation harness.
- Assertions via `mobly.asserts` are used for stepwise reporting as in your other project test files.
- Each step as per the manual procedure is commented and reflected as a scenario/assert.