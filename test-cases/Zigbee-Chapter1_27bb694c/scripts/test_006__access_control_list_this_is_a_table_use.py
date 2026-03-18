```python
# tests/test_TC_SEC_4_1.py

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
Test Case: [TC-SEC-4.1] Access Control List and Network Key Handling Verification - DRAFT

Purpose:
    Validate that the DUT maintains an Access Control List (ACL) governing device authorization, stores associated security material,
    properly uses the active network key for outgoing/incoming NWK frames, and uses an alternate network key for incoming frames if supported.
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# -- Simulation/stub classes for demo (REPLACE with real Zigbee/Matter APIs in integration) --

class DeviceUnderTest:
    def __init__(self, supports_alternate_key=True):
        # ACL: address => authorized (True/False), key material (dict)
        self.acl = {
            "0xABCDEFA1": {"authorized": True, "key": "activekey-1", "security_level": 5, "counter": 100},
            "0xBADF00D1": {"authorized": False, "key": None, "security_level": 0, "counter": 0}
        }
        self.active_nwk_key = "activekey-1"
        self.alternate_nwk_key = "altkey-2" if supports_alternate_key else None
        self.current_keys = {"active": self.active_nwk_key, "alternate": self.alternate_nwk_key}
        self.last_secure_action = None
        self.last_acl_query = None
        self.last_nwk_frame = None
        self.last_key_switch = None
        self.supports_alternate_key = supports_alternate_key

    def query_acl(self):
        self.last_acl_query = self.acl
        return self.acl

    def process_secured_request(self, address, key_used):
        acl_entry = self.acl.get(address)
        # Only allow if address is authorized and key matches
        if acl_entry and acl_entry["authorized"] and key_used == self.current_keys["active"]:
            self.last_secure_action = ("success", address)
            return True
        self.last_secure_action = ("denied", address)
        return False

    def receive_secured_nwk_frame(self, key_used):
        # Accept if matches active key, else try alternate if supported
        if key_used == self.current_keys["active"]:
            self.last_nwk_frame = "accepted-active"
            return True
        elif self.supports_alternate_key and key_used == self.current_keys["alternate"]:
            self.last_nwk_frame = "accepted-alternate"
            return True
        else:
            self.last_nwk_frame = "rejected"
            return False

    def send_outgoing_nwk_frame(self):
        # Always use active NWK key for outgoing
        return {"encrypted_by": self.current_keys["active"]}

    def switch_nwk_keys(self, new_active, new_alternate=None):
        self.current_keys["active"] = new_active
        self.current_keys["alternate"] = new_alternate
        self.last_key_switch = (new_active, new_alternate)
        return True

class TestHarness:
    def __init__(self, dut: DeviceUnderTest):
        self.dut = dut

    def generate_secured_frame(self, address, key_used):
        return self.dut.process_secured_request(address, key_used)

    def send_nwk_frame(self, key_used):
        return self.dut.receive_secured_nwk_frame(key_used)

    def query_dut_acl(self):
        return self.dut.query_acl()

    def capture_outgoing_nwk_frame(self):
        return self.dut.send_outgoing_nwk_frame()

    def switch_keys(self, new_active, new_alternate=None):
        return self.dut.switch_nwk_keys(new_active, new_alternate)

# -- Test logic --

@pytest.mark.asyncio
async def test_tc_sec_4_1_acl_and_nwk_key_handling():
    """
    [TC-SEC-4.1] - Access Control List and Network Key Handling Verification
    """
    # Instantiate simulation DUT and harness
    dut = DeviceUnderTest(supports_alternate_key=True)
    th = TestHarness(dut)
    authorized_addr, unauthorized_addr = "0xABCDEFA1", "0xBADF00D1"

    # Step 1: Query ACL contents
    log.info("Step 1: Query ACL contents on DUT")
    acl = th.query_dut_acl()
    asserts.assert_in(authorized_addr, acl)
    asserts.assert_in(unauthorized_addr, acl)
    # Check ACL security material
    asserts.assert_true('key' in acl[authorized_addr], "ACL does not contain security material/key info")

    # Step 2: Authorized device requests secured function
    log.info("Step 2: Request secured function as authorized address with correct key")
    result = th.generate_secured_frame(authorized_addr, dut.current_keys["active"])
    asserts.assert_true(result, "DUT did not allow authorized device with correct key")

    # Step 3: Unauthorized device requests function
    log.info("Step 3: Request secured function as unauthorized address")
    result = th.generate_secured_frame(unauthorized_addr, dut.current_keys["active"])
    asserts.assert_false(result, "DUT improperly allowed unauthorized device")

    # Step 4: Monitor outgoing secured NWK frame: ensure active network key is used
    log.info("Step 4: Outgoing NWK frame uses active network key")
    outgoing_nwk = th.capture_outgoing_nwk_frame()
    asserts.assert_equal(
        outgoing_nwk["encrypted_by"], dut.current_keys["active"],
        "Outgoing NWK frame not encrypted by active key"
    )

    # Step 5: DUT receives incoming frame secured with active network key
    log.info("Step 5: DUT receives incoming frame using the active NWK key")
    assert th.send_nwk_frame(dut.current_keys["active"]), \
        "DUT did not process incoming NWK frame with active key"

    # Step 6: DUT receives incoming frame secured with alternate network key
    if dut.supports_alternate_key and dut.current_keys["alternate"]:
        log.info("Step 6: DUT receives incoming frame using alternate key")
        # First, pretend incoming frame uses alternate key, but active fails
        assert th.send_nwk_frame(dut.current_keys["alternate"]), \
            "DUT did not process incoming NWK frame with alternate key"
    else:
        pytest.skip("DUT does not support alternate NWK key; Step 6 not applicable")

    # Step 7: Switch active/alternate keys and repeat (e.g., to simulate key rotation)
    log.info("Step 7: Triggering network key switch")
    success = th.switch_keys(new_active="altkey-2", new_alternate="rotatedkey-3")
    asserts.assert_true(success, "DUT did not properly update key configuration")
    # After switch, outgoing must use new active key
    outgoing_nwk2 = th.capture_outgoing_nwk_frame()
    asserts.assert_equal(
        outgoing_nwk2["encrypted_by"], "altkey-2",
        "Outgoing NWK frame after key switch not encrypted by new active key"
    )
    # Process incoming using new keys
    assert th.send_nwk_frame("altkey-2"), "DUT did not process frame with new active key after switch"
    assert th.send_nwk_frame("rotatedkey-3"), "DUT did not process frame with new alternate key after switch"

    log.info("All ACL and NWK key handling steps passed as per TC-SEC-4.1 test specification.")

```
**Instructions:**  
- Save this file as `tests/test_TC_SEC_4_1.py`.
- Replace the `DeviceUnderTest` and `TestHarness` simulation with automation and API calls to your actual Zigbee device and harness.
- Integrate explicit attribute/cluster reads, secured command requests, frame transmission verification, and key switch events per your stack.
- Add more edge cases as needed for full ACL/security coverage.