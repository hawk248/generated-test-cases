```python
# tests/test_TC_IEEE154_1_1.py

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
Test Case: TC-IEEE154-1.1 - IEEE 802.15.4 MAC/PHY Compliance
API Test for 802.15.4 MAC/PHY conformance key features.
Adapted to pytest, following project-chip/connectedhomeip python testing style.
"""

import pytest
from mobly import asserts

# Placeholders for real device/MAC/PHY test interfaces or lower-level drivers
# Replace with imports from your actual Zigbee/802.15.4 test infrastructure!
class IEEE154DUT:
    """
    Mock/Stub for the Device Under Test's MAC/PHY API.
    Replace with the real interface to your Zigbee/802.15.4 device.
    """
    def __init__(self, short_addr=0x0001, ext_addr=0x00124B000199ABCD):
        self.short_addr = short_addr
        self.ext_addr = ext_addr
        self.pan_id = 0x1234
        self.channel = 15
        self.received_frames = []
        self.test_channel_busy = False  # Used to simulate channel access delays/retries
    
    def configure(self, pan_id, channel, short_addr, ext_addr):
        self.pan_id = pan_id
        self.channel = channel
        self.short_addr = short_addr
        self.ext_addr = ext_addr
        
    def join_pan(self):
        # Simulate PAN join procedure (mock)
        return True

    def receive_mac_frame(self, frame):
        self.received_frames.append(frame)
        return True  # Simulate correct protocol handling

    def send_mac_frame(self, dest_addr, payload):
        # Return a tuple (raw_bytes, fields, expected order)
        # Structure would match actual 802.15.4 MAC frame in the real system
        frame_bytes = bytes([
            0x61,           # Frame Control (mocked)
            0x08,           # Sequence Number
            self.pan_id & 0xFF, (self.pan_id >> 8) & 0xFF,
            dest_addr & 0xFF, (dest_addr >> 8) & 0xFF,
            self.short_addr & 0xFF, (self.short_addr >> 8) & 0xFF,
        ]) + payload
        return frame_bytes

    def perform_channel_access(self, channel_busy):
        # Simulates CSMA-CA: Return True if channel free, False if busy/delayed
        return not channel_busy

    def get_frame_structure(self, frame_bytes):
        # A real method/code would parse a frame and return its fields.
        return {
            "frame_control": frame_bytes[0],
            "seq_num": frame_bytes[1],
            "pan_id": frame_bytes[2] | (frame_bytes[3]<<8),
            "dest_addr": frame_bytes[4] | (frame_bytes[5]<<8),
            "src_addr": frame_bytes[6] | (frame_bytes[7]<<8),
            "payload": frame_bytes[8:]
        }

    def get_configured_addresses(self):
        return self.short_addr, self.ext_addr

class IEEE154TH:
    """
    Mock/Stub for the Test Harness (or packet sniffer, with protocol control).
    Replace with integration to your real test infrastructure!
    """
    def __init__(self, pan_id=0x1234, channel=15):
        self.pan_id = pan_id
        self.channel = channel
        self.last_captured_frame = None
        self.last_sent_frame = None

    def send_frame(self, dest_addr, payload):
        # Create and 'send' a IEEE 802.15.4-compliant MAC data frame.
        frame = bytes([
            0x61,               # Frame control
            0x12,               # Seq number
            self.pan_id & 0xFF, (self.pan_id >> 8) & 0xFF,
            dest_addr & 0xFF, (dest_addr >> 8) & 0xFF,
            0x01, 0x00          # Source address = 0x0001 (arbitrary TH addr)
        ]) + payload
        self.last_sent_frame = frame
        return frame

    def capture_frame(self, incoming_frame):
        self.last_captured_frame = incoming_frame

    def analyze_frame(self, frame_bytes):
        # Should perform protocol decoding and bit/octet order checks here
        # This is a stub – actual analyzers invoke field checks at bit/octet level
        return {
            "frame_structure_ok": True,
            "transmission_order_ok": True,
            "addressing_ok": True
        }

@pytest.fixture
def ieee154_devices():
    """Fixture to yield a (DUT, TH) device tuple."""
    dut = IEEE154DUT()
    th = IEEE154TH()
    # Ensure both configured to the same PAN and channel
    dut.configure(pan_id=th.pan_id, channel=th.channel, short_addr=0x0002, ext_addr=0x00124B000199BEAD)
    dut.join_pan()
    return dut, th

@pytest.mark.asyncio
async def test_mac_physical_layer_compliance(ieee154_devices):
    """
    TC-IEEE154-1.1 - IEEE 802.15.4 MAC/PHY Compliance Test
    """

    dut, th = ieee154_devices

    # STEP 1: TH sends a MAC data frame to DUT
    payload = b'\xAA\xBB\xCC'
    th_frame1 = th.send_frame(dest_addr=dut.short_addr, payload=payload)
    result1 = dut.receive_mac_frame(th_frame1)
    asserts.assert_true(result1, "DUT did not process incoming MAC frame per addressing and format rules")
    # (In real test, inspect DUT logs or state indicating valid frame reception)

    # STEP 2: DUT sends MAC data frame; TH/sniffer captures and analyzes it
    dut_frame2 = dut.send_mac_frame(dest_addr=0x0001, payload=b'\xDE\xAD')
    th.capture_frame(dut_frame2)
    frame_info = dut.get_frame_structure(dut_frame2)
    # Check frame format and transmission order (octet, bit, MSB first etc.)
    analysis = th.analyze_frame(dut_frame2)
    asserts.assert_true(analysis["frame_structure_ok"], "Frame format not compliant to IEEE 802.15.4")
    asserts.assert_true(analysis["transmission_order_ok"], "Frame transmission order incorrect (expected MSB first octet/bit order)")

    # STEP 3: Channel access (CSMA-CA) check.
    # TH simulates a busy channel.
    channel_busy = True
    access_result = dut.perform_channel_access(channel_busy=channel_busy)
    asserts.assert_false(access_result, "DUT should defer channel access when busy (CSMA-CA)")

    # STEP 4: Inspect beacon/data/command frames (structure/bit order)
    # For this mock, simply ensure that any structurally compliant frame is recognized
    asserts.assert_true(analysis["frame_structure_ok"], "DUT's frame does not match IEEE 802.15.4 structure (data/command/beacon as supported)")

    # STEP 5: Check correct addressing (short, extended)
    short_addr, ext_addr = dut.get_configured_addresses()
    assert short_addr == 0x0002, f"Short address mismatch: expected 0x0002, got {short_addr:#04x}"
    assert (isinstance(ext_addr, int) and len(f"{ext_addr:016X}") == 16), f"Extended address malformed: {ext_addr}"

    # For full integration, you would use real hardware or virtual Zigbee stacks, packet sniffers, and field/binary analyzers.

    print("PASS: 802.15.4 MAC/PHY conformance basic requirements met")

# Save as: tests/test_TC_IEEE154_1_1.py
```
**NOTES:**
- All device and test harness operations are stubs and should be replaced with real Python APIs/methods from your test harness, stack controller, or device driver.
- Use Mobly asserts for idiomatic project-chip style, and pytest async interface.
- In full integration, bit/octet order is checked with protocol analyzers or captured packet dumps versus the IEEE 802.15.4 standard, especially for MSB-first transmission and address/field structure.
- Expand with more granular field/bit checks and validator logic as you integrate with real test tools or APIs.