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
Test Case: [TC-GP-1.1] Green Power Basic Functionality Set Compliance - DRAFT

Purpose:
    Verify DUT implements Zigbee PRO Green Power (GP) basic functionality as required by spec 14-0563-16:
    - Proper processing of GP-DATA frames
    - Correct reject/ignore of malformed frames
    - Green Power commissioning handling
    - Command processing/forwarding as proxy/sink
    - Security policy adherence when security is enabled
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# -- Simulation/Stub Classes: Replace with DUT/Zigbee stack or testbed handlers --

class DeviceUnderTest:
    """
    Simulates a Zigbee Green Power Proxy/Sink device (or actual hardware in real use).
    """

    def __init__(self, roles=("proxy", "sink"), security=True):
        self.roles = set(roles)
        self.is_commissioned = True
        self.gp_commissioning_mode = False
        self.paired_devices = set()
        self.security_enabled = security
        self.last_gp_outcome = None

    def receive_gp_frame(self, frame, valid=True, secure=False):
        # Frame must be valid and device must be commissioned
        if not self.is_commissioned:
            self.last_gp_outcome = "not_commissioned"
            return False
        if valid:
            if secure and not self.security_enabled:
                self.last_gp_outcome = "security_reject"
                return False
            self.last_gp_outcome = "accepted"
            return True
        else:
            self.last_gp_outcome = "rejected"
            return False

    def trigger_commissioning(self):
        if "proxy" in self.roles or "sink" in self.roles:
            self.gp_commissioning_mode = True
            self.last_gp_outcome = "commissioning_started"
            return True
        self.last_gp_outcome = "no_commissioning"
        return False

    def update_paired_devices(self, device_id):
        if self.gp_commissioning_mode:
            self.paired_devices.add(device_id)
            self.gp_commissioning_mode = False
            self.last_gp_outcome = "paired"
            return True
        self.last_gp_outcome = "not_in_commissioning"
        return False

    def receive_gp_app_cmd(self, cmd, from_device=None):
        if self.is_commissioned and (not from_device or from_device in self.paired_devices):
            if "proxy" in self.roles or "sink" in self.roles:
                self.last_gp_outcome = "app_cmd_processed"
                return True
        self.last_gp_outcome = "cmd_not_processed"
        return False

    def receive_secure_gp_data(self, secure):
        if not secure or (secure and self.security_enabled):
            self.last_gp_outcome = "secure_accepted"
            return True
        self.last_gp_outcome = "security_policy_reject"
        return False

class GreenPowerTestHarness:
    """
    Simulates test harness as GPD/client and Green Power test infrastructure.
    """

    def __init__(self, dut: DeviceUnderTest):
        self.dut = dut

    def send_valid_gp_data(self):
        return self.dut.receive_gp_frame(frame="GP-DATA", valid=True)

    def send_invalid_gp_data(self):
        return self.dut.receive_gp_frame(frame="Invalid-GP", valid=False)

    def initiate_commissioning(self):
        return self.dut.trigger_commissioning()

    def send_commissioning_pairing(self, device_id):
        return self.dut.update_paired_devices(device_id)

    def send_gp_app_cmd(self, from_device="GPD1"):
        return self.dut.receive_gp_app_cmd(cmd="OnCommand", from_device=from_device)

    def send_secure_gp_data(self, secure=True):
        return self.dut.receive_secure_gp_data(secure=secure)

# --- Pytest script ---

@pytest.mark.asyncio
async def test_tc_gp_1_1_basic_functionality_set():
    """
    [TC-GP-1.1] Green Power Basic Functionality Set Compliance
    """
    # Simulate a proxy/sink DUT, security enabled
    dut = DeviceUnderTest(roles=["proxy", "sink"], security=True)
    th = GreenPowerTestHarness(dut)
    paired_device_id = "GPD1"

    # Step 1: TH sends a valid Green Power Data Frame
    log.info("Step 1: TH sends valid Green Power Data Frame (GP-DATA)")
    outcome = th.send_valid_gp_data()
    asserts.assert_true(outcome, "DUT did not accept/process valid GP-DATA frame")
    assert dut.last_gp_outcome == "accepted"

    # Step 2: TH sends invalid or malformed Green Power frame
    log.info("Step 2: TH sends invalid Green Power frame")
    outcome = th.send_invalid_gp_data()
    asserts.assert_false(outcome, "DUT did not reject/ignore malformed Green Power frame")
    assert dut.last_gp_outcome == "rejected"

    # Step 3: TH initiates Green Power commissioning (DUT as proxy/sink)
    log.info("Step 3: TH initiates Green Power commissioning to DUT")
    outcome = th.initiate_commissioning()
    asserts.assert_true(outcome, "DUT did not enter commissioning mode")
    assert dut.gp_commissioning_mode

    # TH sends pairing (commissioning) information for GPD
    log.info("Step 3b: TH pairs GPD1 with DUT during commissioning")
    outcome = th.send_commissioning_pairing(paired_device_id)
    asserts.assert_true(outcome, "DUT did not update pairing during commissioning")
    assert paired_device_id in dut.paired_devices

    # Step 4: TH sends application command via Green Power channel
    log.info("Step 4: TH sends application command via Green Power (from paired GPD)")
    outcome = th.send_gp_app_cmd(from_device=paired_device_id)
    asserts.assert_true(outcome, "DUT did not process/forward Green Power application command")
    assert dut.last_gp_outcome == "app_cmd_processed"

    # Step 5: TH modifies security context (if supported) and sends secure GP data
    log.info("Step 5: TH sends secure Green Power data frame (security enabled)")
    outcome = th.send_secure_gp_data(secure=True)
    asserts.assert_true(outcome, "DUT did not process (or properly reject) secure Green Power data as required")
    assert dut.last_gp_outcome == "secure_accepted"

    # (Optional) Test security policy when security is disabled
    log.info("Step 5b: Simulate security policy handling with security disabled")
    dut.security_enabled = False
    outcome = th.send_secure_gp_data(secure=True)
    asserts.assert_false(outcome, "DUT incorrectly processed secure data when security is disabled")
    assert dut.last_gp_outcome == "security_policy_reject"

    log.info("TC-GP-1.1 Green Power basic functionality set test completed and all steps passed.")

```
**Instructions:**
- Place the script as `tests/test_TC_GP_1_1.py` in your test suite.
- Replace stub classes (`DeviceUnderTest`, `GreenPowerTestHarness`) with your own device automation, Zigbee Green Power interfaces, and test infrastructure.
- Add/parameterize as needed for additional frame/command/security test cases, or to adapt for proxy-only/sink-only roles on the DUT.
