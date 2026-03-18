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
Test Case: [TC-GP-1.1] Green Power Frame Handling and Security Material Compliance - DRAFT

Purpose:
    Validate that the DUT processes Green Power Device Frames conformant to Document 09-5499r26,
    including mandatory handling of GP primitives, security material, and frame formats.
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# --- Simulation stubs (replace with actual device/test harness APIs for integration) ---

class DeviceUnderTest:
    """
    Simulates a Zigbee GP Sink/Proxy/Combo device.
    Replace with real device APIs for GP frame/primitive handling and security checks.
    """
    def __init__(self):
        self.gp_security_material = {"key": b"123456789ABCDEF0", "frame_counter": 42}
        self.received_frames = []
        self.last_sec_request = None
        self.last_sec_response = None
        self.last_process_result = None

    def preload_security_material(self, key, frame_counter):
        self.gp_security_material = {"key": key, "frame_counter": frame_counter}

    def receive_gp_data_indication(self, frame, secured=False, counter=None):
        self.received_frames.append(frame)
        # Simulate processing logic: accept only well-formed, expected security/counter if required
        if frame.get("valid", False):
            if secured:
                # GP-SEC.request shall be triggered
                self.last_sec_request = {"key": self.gp_security_material["key"], "counter": counter}
                # "Process" security and build response primitive
                success = (counter == self.gp_security_material["frame_counter"])  # Accept if counter matches
                self.last_sec_response = {"success": success}
                self.last_process_result = "PROCESSED_SECURE" if success else "REJECTED_SECURE_FAIL"
                return success
            else:
                self.last_process_result = "PROCESSED_UNSECURED"
                return True
        else:
            # Should reject/discard non-conformant
            self.last_process_result = "DISCARDED_INVALID"
            return False

    def check_last_sec_request(self):
        return self.last_sec_request

    def check_last_sec_response(self):
        return self.last_sec_response

    def check_last_process_result(self):
        return self.last_process_result

    def check_key_usage(self, key):
        # Simulate confirming key used matches configured material
        return key == self.gp_security_material["key"]

    def check_frame_counter_usage(self, counter):
        return counter == self.gp_security_material["frame_counter"]


class GreenPowerTestHarness:
    """
    Simulates a Zigbee Test Harness able to craft and inject valid/invalid GP frames and trigger GP primitives.
    """
    def __init__(self, dut):
        self.dut = dut

    def send_valid_gp_data_indication(self, secured=False):
        frame = {"valid": True, "type": "GP-DATA.indication"}
        counter = self.dut.gp_security_material["frame_counter"] if secured else None
        return self.dut.receive_gp_data_indication(frame, secured=secured, counter=counter), frame

    def send_invalid_gp_frame(self):
        frame = {"valid": False, "type": "GP-DATA.indication"}
        return self.dut.receive_gp_data_indication(frame, secured=False, counter=None), frame

    def check_gp_sec_request_response(self):
        return self.dut.check_last_sec_request(), self.dut.check_last_sec_response()

    def verify_frame_format_and_security_usage(self):
        # Returns a tuple (frame_format_ok, key_usage_ok, counter_usage_ok)
        req = self.dut.check_last_sec_request()
        resp = self.dut.check_last_sec_response()
        gp_key_ok = self.dut.check_key_usage(req["key"]) if req else False
        counter_ok = self.dut.check_frame_counter_usage(req["counter"]) if req else False
        frame_format_ok = self.dut.check_last_process_result() in ("PROCESSED_SECURE", "PROCESSED_UNSECURED")
        return frame_format_ok, gp_key_ok, counter_ok

    def replay_edgecase_frame(self, counter):
        # Attempts to send replay/edge frame, expecting failure
        frame = {"valid": True, "type": "GP-DATA.indication"}
        return self.dut.receive_gp_data_indication(frame, secured=True, counter=counter)

# --- Main pytest test ---

@pytest.mark.asyncio
async def test_tc_gp_1_1_green_power_frame_and_security_material_compliance():
    """
    [TC-GP-1.1] Green Power Frame Handling and Security Material Compliance
    """
    dut = DeviceUnderTest()
    th = GreenPowerTestHarness(dut)

    # Setup: Commission as GP sink/Proxy/Combo, preload keys and counters for security, ensure ready
    dut.preload_security_material(key=b"123456789ABCDEF0", frame_counter=42)
    log.info("DUT commissioned as GP Sink/Proxy with security material.")

    # Step 1: TH sends valid GP-DATA.indication frame to DUT
    log.info("Step 1: Sending valid GP-DATA.indication...")
    processed, frame1 = th.send_valid_gp_data_indication(secured=False)
    asserts.assert_true(processed, "DUT did not process valid Green Power data indication (unsecured)")
    assert dut.check_last_process_result() == "PROCESSED_UNSECURED"

    # Step 2: TH sends a secured, valid GP frame (triggers GP-SEC.request/response flow)
    log.info("Step 2: Sending secured GP frame/primitive to DUT...")
    processed_sec, frame2 = th.send_valid_gp_data_indication(secured=True)
    asserts.assert_true(processed_sec, "DUT failed to process secured GP frame or did not issue correct GP-SEC.response")
    req, resp = th.check_gp_sec_request_response()
    asserts.assert_is_not_none(req, "DUT did not trigger GP-SEC.request")
    asserts.assert_true(resp.get("success", False), "GP-SEC.response not reported as successful")

    # Step 3: TH sends invalid/modified GP frame (should be rejected)
    log.info("Step 3: Sending invalid/modified GP frame...")
    accepted_invalid, frame3 = th.send_invalid_gp_frame()
    asserts.assert_false(accepted_invalid, "DUT accepted invalid non-conformant GP frame (should discard)")
    assert dut.check_last_process_result() == "DISCARDED_INVALID"

    # Step 4: TH verifies GP frame format, key/counter usage, and error handling behavior
    log.info("Step 4: Verifying GP frame format, security key/counter, error case...")
    frame_format_ok, key_ok, counter_ok = th.verify_frame_format_and_security_usage()
    asserts.assert_true(frame_format_ok, "DUT failed to conform to mandatory Green Power frame format")
    asserts.assert_true(key_ok, "DUT failed to use required security key for GP-SEC.request")
    asserts.assert_true(counter_ok, "DUT failed to use correct frame counter in GP-SEC.request/processing")

    # (Optional) Step: Replay/edge-case with altered counter/key (should be rejected)
    log.info("Optional: Attempt counter replay/edge-case GP frame...")
    replayed = th.replay_edgecase_frame(counter=999)  # Incorrect (replay/edge) counter
    asserts.assert_false(replayed, "DUT failed to reject replayed/edge-case GP frame (security policy)")

    log.info("Green Power Frame Handling and Security Material compliance test completed successfully.")

# Instructions:
# - Save as `tests/test_TC_GP_1_1.py` in your test suite.
# - Replace `DeviceUnderTest` and `GreenPowerTestHarness` with stack- or hardware-specific API calls for device commissioning, frame injection, and Green Power event observation.
# - Add further assertions and variants for more detailed testing per 09-5499r26 as your environment requires.
```