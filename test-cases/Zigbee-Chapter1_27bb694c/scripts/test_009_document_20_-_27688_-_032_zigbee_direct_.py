```python
# tests/test_TC_ZigbeeDirect_1_1.py

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
Test Case: [TC-ZigbeeDirect-1.1] Commissioning via Zigbee Direct - DRAFT

Purpose:
    Validate that a DUT can be commissioned/joined to a Zigbee network via Zigbee Direct,
    following all security and network steps. Confirm operational network presence.
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# --- Stub classes for Zigbee Direct commissioning workflow ---
# Replace with project/hardware integration in a real test framework.

class DeviceUnderTest:
    """
    Simulates a Zigbee Direct-capable end device.
    In production, these calls should invoke real device APIs.
    """
    def __init__(self):
        self.is_factory_new = True
        self.joined_network = False
        self.security_authenticated = False
        self.network_table_present = False
        self.last_attribute_read_response = None

    def factory_reset(self):
        self.is_factory_new = True
        self.joined_network = False
        self.security_authenticated = False
        self.network_table_present = False
        self.last_attribute_read_response = None

    def zigbee_direct_commission_start(self):
        if self.is_factory_new:
            return True
        return False

    def exchange_security_authentication(self):
        if self.is_factory_new:
            self.security_authenticated = True
            return True
        return False

    def join_network(self):
        if self.security_authenticated:
            self.joined_network = True
            self.network_table_present = True
            self.is_factory_new = False
            return True
        return False

    def handle_basic_attribute_read(self, attr):
        if self.joined_network and attr == "ZCLVersion":
            self.last_attribute_read_response = 3  # Example value
            return 3
        return None

    def is_visible_on_network(self):
        return self.network_table_present and self.joined_network

class ZigbeeDirectTestHarness:
    """
    Simulates Zigbee Direct initiator (test harness).
    In real integration, these perform actual network/protocol operations.
    """

    def __init__(self, dut: DeviceUnderTest):
        self.dut = dut

    def initiate_commissioning(self):
        return self.dut.zigbee_direct_commission_start()

    def exchange_security(self):
        return self.dut.exchange_security_authentication()

    def finalize_commissioning_join(self):
        return self.dut.join_network()

    def read_basic_attribute(self):
        # Simulate a Zigbee attribute read (e.g., ZCLVersion)
        response = self.dut.handle_basic_attribute_read("ZCLVersion")
        return response

    def verify_network_presence(self):
        return self.dut.is_visible_on_network()

@pytest.mark.asyncio
async def test_commissioning_via_zigbee_direct():
    """
    [TC-ZigbeeDirect-1.1] Commissioning via Zigbee Direct
    """

    dut = DeviceUnderTest()
    th = ZigbeeDirectTestHarness(dut)

    # --- Test Setup ---
    dut.factory_reset()
    log.info("DUT factory reset and ready for Zigbee Direct commissioning.")

    # Step 1: Initiate Zigbee Direct commissioning
    log.info("Step 1: TH initiates Zigbee Direct commissioning.")
    result_commission_start = th.initiate_commissioning()
    asserts.assert_true(result_commission_start, "DUT did not respond to Zigbee Direct commissioning initiation.")

    # Step 2: Exchange all required security and authentication data
    log.info("Step 2: TH exchanges mandatory security/authentication for Zigbee Direct.")
    secure_exchange = th.exchange_security()
    asserts.assert_true(secure_exchange, "Failed Zigbee Direct security/authentication exchange with DUT.")

    # Step 3: Complete commissioning and join network
    log.info("Step 3: TH finalizes commissioning, prompts DUT network join.")
    joined = th.finalize_commissioning_join()
    asserts.assert_true(joined, "DUT did not join Zigbee network after commissioning.")

    # Step 4: Read a Zigbee attribute to confirm network presence
    log.info("Step 4: TH sends attribute read request (ZCLVersion) to verify communication.")
    attr_result = th.read_basic_attribute()
    asserts.assert_is_not_none(attr_result, "DUT did not respond to attribute read after network join.")
    assert attr_result == 3, f"Expected attribute value 3, got {attr_result}"

    # Final check: Confirmed network-visible
    asserts.assert_true(th.verify_network_presence(), "DUT is not present/visible in network table after join.")

    log.info("Zigbee Direct commissioning test completed; DUT is joined and network-visible.")

```
**Instructions:**
- Save as `tests/test_TC_ZigbeeDirect_1_1.py` in your test suite directory.
- Replace simulation logic (`DeviceUnderTest`, `ZigbeeDirectTestHarness`) with your device's Zigbee Direct and test harness APIs.
- For physical devices, use real process triggers, network table verifications, and actual Zigbee attribute read/response checks.
