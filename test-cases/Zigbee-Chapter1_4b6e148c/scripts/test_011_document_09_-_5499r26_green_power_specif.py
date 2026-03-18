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
Test Case: TC-GP-1.1 - Green Power Device Frame Handling and Security Material Support

API Test for Zigbee Green Power proxy/sink/server operations.
Validates frame handling, security material policy, GP-DATA.indication, and replay protection.
Adapt to your system/harness for actual Green Power primitives and frame interaction.
"""

import pytest
from mobly import asserts

# Placeholder for your actual Zigbee/Green Power harness API.
# Replace these with real implementations (e.g., via serial, Matter cluster, or REST/RPC).
class GreenPowerDUT:
    def __init__(self):
        self.frame_counter = 0
        self.provisioned_keys = {"gpd_id_1": b"\xCA" * 16}
        self.processed_frames = set()
        self.last_gp_data_indication = None

    async def process_gpd_frame(self, frame, security_key):
        # Simulate frame validation/processing and replay protection
        expected_key = self.provisioned_keys.get(frame["gpd_id"])
        if (not security_key) or (security_key != expected_key):
            return {"accepted": False, "reason": "invalid security material"}
        if frame["frame_counter"] <= self.frame_counter:
            return {"accepted": False, "reason": "replay detected"}
        self.frame_counter = frame["frame_counter"]
        self.processed_frames.add(frame["frame_counter"])
        return {"accepted": True, "acknowledged": True}

    async def get_frame_counter(self, gpd_id):
        return self.frame_counter

    async def get_security_key(self, gpd_id):
        return self.provisioned_keys.get(gpd_id)

    async def trigger_gp_data_indication(self, gpd_id, payload):
        # Simulate GP-DATA.indication primitive output
        self.last_gp_data_indication = {"gpd_id": gpd_id, "payload": payload}
        return self.last_gp_data_indication

    async def get_gp_data_indication(self):
        return self.last_gp_data_indication

    async def reset(self):
        self.frame_counter = 0
        self.processed_frames = set()
        self.last_gp_data_indication = None

class TestGreenPowerDeviceFrameHandling:
    @pytest.fixture(autouse=True)
    async def setup_dut(self):
        self.dut = GreenPowerDUT()
        await self.dut.reset()

    @pytest.mark.asyncio
    async def test_valid_secured_gpd_frame_is_processed(self):
        """Step 1: TH sends a valid, secured Green Power Device (GPD) frame to DUT."""
        gpd_id = "gpd_id_1"
        frame = {
            "gpd_id": gpd_id,
            "frame_counter": 1,
            "payload": b'\x01\x23'
        }
        security_key = await self.dut.get_security_key(gpd_id)
        result = await self.dut.process_gpd_frame(frame, security_key)
        asserts.assert_true(result["accepted"], "DUT did not accept a valid, secured GPD frame.")
        asserts.assert_true(result.get("acknowledged"), "DUT did not acknowledge secured GPD frame.")

    @pytest.mark.asyncio
    async def test_invalid_security_material_is_rejected(self):
        """Step 2: TH sends a GPD frame with invalid or missing security material."""
        gpd_id = "gpd_id_1"
        frame = {
            "gpd_id": gpd_id,
            "frame_counter": 2,
            "payload": b'\xAB'
        }
        bad_security_key = b"\x00" * 16
        result = await self.dut.process_gpd_frame(frame, bad_security_key)
        asserts.assert_false(result["accepted"], "DUT accepted a frame with invalid security material.")

    @pytest.mark.asyncio
    async def test_frame_counter_and_key_maintenance(self):
        """Step 3: TH inspects proper maintenance of frame counters and key usage."""
        gpd_id = "gpd_id_1"
        correct_key = await self.dut.get_security_key(gpd_id)
        # Send two valid frames
        for cnt in [10, 20]:
            frame = {"gpd_id": gpd_id, "frame_counter": cnt, "payload": b'\xAA'}
            result = await self.dut.process_gpd_frame(frame, correct_key)
            asserts.assert_true(result["accepted"], f"Valid frame {cnt} not accepted.")
        # Frame counter must track highest value seen
        stored_counter = await self.dut.get_frame_counter(gpd_id)
        asserts.assert_equal(stored_counter, 20, "Frame counter not updated correctly in DUT.")

    @pytest.mark.asyncio
    async def test_gp_data_indication_primitive_generation(self):
        """Step 4: TH triggers a GP-DATA.indication primitive and monitors DUT output."""
        gpd_id = "gpd_id_1"
        payload = b'\xBEEF'
        expected_indication = {"gpd_id": gpd_id, "payload": payload}
        actual_indication = await self.dut.trigger_gp_data_indication(gpd_id, payload)
        asserts.assert_equal(actual_indication, expected_indication, "GP-DATA.indication incorrect or not generated.")

    @pytest.mark.asyncio
    async def test_replay_protection_via_frame_counter(self):
        """Step 5: TH tests replay protection by sending a previously used frame sequence."""
        gpd_id = "gpd_id_1"
        key = await self.dut.get_security_key(gpd_id)
        # Send valid frame
        valid_frame = {"gpd_id": gpd_id, "frame_counter": 100, "payload": b'\x31'}
        result_valid = await self.dut.process_gpd_frame(valid_frame, key)
        asserts.assert_true(result_valid["accepted"], "Fresh valid frame should be accepted.")
        # Replay: same frame_counter again
        replay_frame = {"gpd_id": gpd_id, "frame_counter": 100, "payload": b'\x31'}
        result_replay = await self.dut.process_gpd_frame(replay_frame, key)
        asserts.assert_false(result_replay["accepted"], "Replay protection failed: DUT accepted repeated frame_counter.")

# Save the script as: tests/test_TC_GP_1_1.py

"""
NOTES:
- Replace GreenPowerDUT with true driver/integration code for your Zigbee Green Power device or stack.
- Mobly assertions (asserts.assert_*) are used per project style.
- All Green Power primitives (frame processing, sec material, GP-DATA.indication, etc.) should eventually tie into actual hardware or simulated Green Power stack.
- For full certification, expand negative/malformed frame cases and multi-GPD scenarios.
"""
```
