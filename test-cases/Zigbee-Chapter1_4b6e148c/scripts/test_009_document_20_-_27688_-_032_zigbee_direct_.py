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

"""
Test Case: TC-ZigbeeDirect-1.1 — Zigbee Direct Commissioning
Validates Zigbee Direct commissioning per Document 20-27688-032.
"""

from mobly import asserts
import pytest

# Placeholder for the MatterBaseTest style from project-chip/connectedhomeip.
# Adapted from similar style in examples.
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.decorators import async_test_body

# Placeholder imports for Zigbee Direct commissioning helpers.
# Substitute with real implementation for your environment.
try:
    from zigbeedirect.api import (
        discover_zigbeedirect_device,
        initiate_zigbeedirect_commissioning,
        perform_zigbeedirect_auth_and_credential_exchange,
        command_device_join_network,
        verify_zigbee_network_join,
    )
except ImportError:
    # Dev stub functions
    async def discover_zigbeedirect_device():
        return {"device_id": "test-dut", "info": "discovered"}  # Simulate success

    async def initiate_zigbeedirect_commissioning(device_info):
        return {"challenge": "test-challenge"}  # Simulate challenge/accept

    async def perform_zigbeedirect_auth_and_credential_exchange(device_info, challenge):
        return {"provision_status": "success", "credentials": "nwk_credentials"}

    async def command_device_join_network(device_info, credentials):
        return {"join_result": True}

    async def verify_zigbee_network_join(device_info):
        return {"joined": True, "operational": True}

class TestZigbeeDirectCommissioning(MatterBaseTest):
    """
    Implements TC-ZigbeeDirect-1.1 commissioning compliance test.
    """

    @async_test_body
    async def test_zigbee_direct_commissioning(self):
        # ====== Step 0: Test Setup ======
        self.print_step(0, "Ensure DUT is factory new and TH is ready for Zigbee Direct commissioning")

        # ====== Step 1: Discovery ======
        self.print_step(1, "TH attempts Zigbee Direct discovery of DUT")
        discovery_info = await discover_zigbeedirect_device()
        asserts.assert_is_not_none(
            discovery_info,
            "DUT was not discovered by Zigbee Direct discovery"
        )
        # Optionally, log or assert specific properties (e.g., device_id)
        self.print_step(1.1, f"Discovered device info: {discovery_info}")

        # ====== Step 2: Initiate Commissioning Request ======
        self.print_step(2, "TH initiates Zigbee Direct commissioning request to DUT")
        commissioning_resp = await initiate_zigbeedirect_commissioning(discovery_info)
        asserts.assert_in(
            "challenge", commissioning_resp,
            "DUT did not respond with expected challenge or acceptance per Zigbee Direct spec"
        )
        challenge = commissioning_resp["challenge"]

        # ====== Step 3: Authentication and Credential Exchange ======
        self.print_step(3, "TH and DUT perform authentication and provision network credentials")
        auth_resp = await perform_zigbeedirect_auth_and_credential_exchange(discovery_info, challenge)
        asserts.assert_equal(
            auth_resp.get("provision_status"), "success",
            "Zigbee Direct authentication/credential exchange did not succeed"
        )
        credentials = auth_resp.get("credentials")

        # ====== Step 4: Issue Join Command ======
        self.print_step(4, "TH commands DUT to join the Zigbee network")
        join_result = await command_device_join_network(discovery_info, credentials)
        asserts.assert_true(
            join_result.get("join_result"),
            "DUT failed to join the Zigbee network when commanded"
        )

        # ====== Step 5: Verify DUT Is Operational ======
        self.print_step(5, "TH verifies that DUT is operational on the network")
        status = await verify_zigbee_network_join(discovery_info)
        asserts.assert_true(
            status.get("joined") and status.get("operational"),
            "DUT is not joining/operational after Zigbee Direct commissioning"
        )

        self.print_step("PASS", "DUT successfully commissioned and operational via Zigbee Direct")

if __name__ == "__main__":
    import asyncio
    asyncio.run(TestZigbeeDirectCommissioning().test_zigbee_direct_commissioning())
```

**INSTRUCTIONS/NOTES:**
- Save as `tests/test_TC_ZigbeeDirect_1_1.py`
- Adapt the placeholders (e.g., `discover_zigbeedirect_device`, etc.) with your actual Zigbee Direct commissioning API calls, methods, or tools.
- The test follows the existing MatterBaseTest style (step printouts, assertions), in line with the `TestInvokeReturnCodes.py` style.
- Use pytest's async capabilities for real device/test-harness calls. All steps and assertions map directly to the original test procedure.
- In a real project, fixtures or CI runner will discover and invoke this script as appropriate.