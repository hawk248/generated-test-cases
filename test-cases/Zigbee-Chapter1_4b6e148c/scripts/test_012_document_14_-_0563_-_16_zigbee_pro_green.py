```python
# tests/test_TC_GP_1_1.py
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
TC-GP-1.1: Zigbee PRO Green Power Feature - Basic Functionality Set Support

This script validates basic support for the Green Power feature (per 14-0563-16)
following the project-chip/connectedhomeip python test style.

STUB/PLACEHOLDER WARNING:
Replace class GreenPowerApi below with the real test harness/device control API.
"""

import pytest
from mobly import asserts

# Placeholder for the actual Green Power test harness and DUT control API.
class GreenPowerApi:
    """
    Mock API for Green Power feature interaction for test purposes only.
    Replace with your testbed's actual API for real device interaction.
    """

    def __init__(self, security_supported=True):
        self.recv_frames = []
        self.attrs = {"GPCommissioned": False, "PairingStatus": "NotPaired"}
        self.security_mode = security_supported
        self.last_operation_state = "Idle"

    async def send_gp_data_frame(self, frame):
        # Emulate receiving and processing a Green Power data frame
        self.recv_frames.append(frame)
        self.last_operation_state = "DataProcessed"
        return {"processed": True}

    async def issue_gp_command(self, command):
        # Emulate command handling (commissioning, pairing, etc.)
        if command == "commission":
            self.attrs["GPCommissioned"] = True
            self.last_operation_state = "Commissioned"
            return {"ack": True}
        elif command == "pairing":
            self.attrs["PairingStatus"] = "Paired"
            self.last_operation_state = "Paired"
            return {"ack": True}
        else:
            self.last_operation_state = "UnknownCommand"
            return {"ack": False}

    async def get_gp_attribute(self, attr):
        return self.attrs.get(attr, None)

    async def set_gp_attribute(self, attr, value):
        self.attrs[attr] = value
        return True

    async def send_gp_security_frame(self, challenge):
        if self.security_mode:
            self.last_operation_state = "SecurityProcessed"
            return {"valid": challenge == "valid_challenge"}
        else:
            self.last_operation_state = "SecurityUnsupported"
            return {"valid": False}

    async def query_operation_status(self):
        return self.last_operation_state

# The test class follows the MatterBaseTest project style. No real state is kept between tests.
@pytest.mark.asyncio
class TestGreenPowerBasicFunctionality:
    """
    TC-GP-1.1: Zigbee PRO Green Power Feature - Basic Functionality Set Support
    """

    @pytest.fixture(scope="function", autouse=True)
    async def setup(self):
        # Replace with API that connects to actual DUT and test harness.
        self.dut = GreenPowerApi(security_supported=True)
        self.th = self.dut  # For this mock, DUT and TH are unified; in a real setup these are separate.

    async def test_receive_and_process_data_frame(self):
        # Step 1: TH sends Green Power Data frame to DUT; expects process confirmation.
        data_frame = {"src_id": 0x1234, "payload": b'\x01\x02'}
        result = await self.th.send_gp_data_frame(data_frame)
        asserts.assert_true(result["processed"], "DUT did not process Green Power frame as specified.")

    async def test_gp_command_handling(self):
        # Step 2: TH issues recognized GP command (commissioning, pairing)
        comm_result = await self.th.issue_gp_command("commission")
        asserts.assert_true(comm_result["ack"], "DUT did not acknowledge commissioning command.")

        pair_result = await self.th.issue_gp_command("pairing")
        asserts.assert_true(pair_result["ack"], "DUT did not acknowledge pairing command.")

    async def test_gp_attribute_storage_and_retrieval(self):
        # Step 3: TH verifies DUT can store/retrieve GP attributes
        await self.th.set_gp_attribute("GPCommissioned", True)
        val = await self.th.get_gp_attribute("GPCommissioned")
        asserts.assert_equal(val, True, "DUT attribute GPCommissioned not stored/retrieved correctly.")

        await self.th.set_gp_attribute("PairingStatus", "Paired")
        val = await self.th.get_gp_attribute("PairingStatus")
        asserts.assert_equal(val, "Paired", "DUT attribute PairingStatus not set/retrieved as expected.")

    async def test_gp_security_challenge_handling(self):
        # Step 4: TH sends GP security challenge, expects correct DUT processing
        resp = await self.th.send_gp_security_frame("valid_challenge")
        asserts.assert_true(resp["valid"], "DUT did not correctly process valid GP security challenge.")

        resp_invalid = await self.th.send_gp_security_frame("invalid")
        asserts.assert_false(resp_invalid["valid"], "DUT accepted invalid security challenge, this should fail.")

    async def test_gp_operation_status_query(self):
        # Step 5: TH queries GP operation status
        await self.th.issue_gp_command("commission")
        status = await self.th.query_operation_status()
        asserts.assert_equal(status, "Commissioned", "DUT did not indicate correct operational state after commission.")

        await self.th.issue_gp_command("pairing")
        status = await self.th.query_operation_status()
        asserts.assert_equal(status, "Paired", "DUT did not indicate correct operational state after pairing.")

        await self.th.send_gp_data_frame({"src_id": 0x5678, "payload": b'\x03\x04'})
        status = await self.th.query_operation_status()
        asserts.assert_equal(status, "DataProcessed", "DUT operation state after data frame not as expected.")

# This script can be discovered/run by pytest and follows the preferred style from project-chip/connectedhomeip.
# Save as: tests/test_TC_GP_1_1.py
```
**NOTES:**
- Replace the mock GreenPowerApi class and all method implementations with real device proxy/test harness APIs in your testbed.
- The test sequence is parametrized according to the basic set required by Document 14-0563-16.
- All assertions map directly to a specific step or expected outcome from the requested test case description.
- For each test step/requirement, a separate async test function is provided for clear pytest/CI output. 

To execute, place this file at `tests/test_TC_GP_1_1.py` in your test repository and call with your test runner (`pytest` or project-specific runner).