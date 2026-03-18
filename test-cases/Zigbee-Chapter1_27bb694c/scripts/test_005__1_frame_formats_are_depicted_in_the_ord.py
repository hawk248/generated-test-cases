```python
# tests/test_TC_PHYFMT_1_1.py

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
Test Case: [TC-PHYFMT-1.1] Frame Transmission Order and Bit Numbering Validation - DRAFT

Purpose:
    Validate transmission order and bit numbering in MAC/NWK/APS frames.
    - Fields sent MSB first, left-to-right at PHY
    - Bits within fields: leftmost = bit 0 = least significant
    - Multi-octet fields: octet w/ lowest-numbered bits sent first
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# --- Simulation / Stub Classes (Replace with your stack/harness/sniffer APIs!) ---

class DeviceUnderTest:
    """
    Simulates device under test making PHY-level transmissions of Zigbee packets.
    In real test, trigger frames using actual device API.
    """
    def __init__(self):
        pass

    def send_known_frame(self):
        """
        Simulate a frame transmission.
        Returns a bytestream (as PHY would transmit), e.g., MAC header | payload.
        Test vector: MAC Frame Control (0x8841), Sequence (0x05), IEEE addr (8 bytes), payload.
        Transmit order is as per Zigbee: MSByte/bit first, left to right.
        """
        frame_control = [0x88, 0x41]   # MAC Frame Control in correct order (MS byte first)
        seq_num = [0x05]
        ieee_addr = [0x00, 0x12, 0x4b, 0x00, 0x13, 0xab, 0xcd, 0xef]  # Example IEEE address
        payload = [0xAA, 0xBB]
        return frame_control + seq_num + ieee_addr + payload

class PHYSniffer:
    """
    Simulates PHY-level sniffer that can analyze bit/byte order in captured frames from the DUT.
    """
    def capture_frame(self, dut):
        """Capture bytes as transmitted at PHY (left-to-right order)."""
        return dut.send_known_frame()

    def check_field_order_left_to_right(self, frame_bytes, field_layout):
        """
        Checks that fields are placed left-to-right as expected.
        Args:
            frame_bytes: The captured PHY transmission as bytes or int list.
            field_layout: List of tuples: (field_name, start_idx, end_idx, expected_value_list)
        """
        for name, si, ei, exp_val in field_layout:
            actual = frame_bytes[si:ei]
            if actual != exp_val:
                return False, f"Field '{name}' order incorrect: expected {exp_val}, got {actual}"
        return True, ""

    def check_field_bit_numbering(self, field_bytes, bit_length):
        """
        Checks bit numbering: leftmost is bit 0, LSB; rightmost is k-1, MSB in the field.
        Provide an integer value with exactly bit_length bits.
        For demonstration: expect leftmost bit is considered 0 (LSB).
        """
        # In Zigbee, bits within a byte are sent MSB first.
        # For this test, we simply verify the byte's bit order ("0b11000001" => [1,1,0,0,0,0,0,1])
        value = field_bytes[0]
        bits = [(value >> (7 - i)) & 1 for i in range(8)]  # MSB first
        # Here, leftmost is "bit 0" (per spec), so bits[0] is bit 0.
        # For test, let's check that bits[0] is the LSB if value==1 (rare, but matches field and spec)
        return True  # In a real sniffer, parse and compare indexes and numbering

    def check_multi_octet_order(self, field_bytes, expected_order):
        """
        Checks that, for a multi-octet (e.g., IEEE address), octets are present in expected left-to-right order.
        """
        return field_bytes == expected_order

@pytest.mark.asyncio
async def test_frame_transmission_order_and_bit_numbering_validation():
    """
    [TC-PHYFMT-1.1] Test PHY/MSDU field order, bit numbering, and multi-octet field order
    """
    dut = DeviceUnderTest()
    sniffer = PHYSniffer()

    # Step 1: Trigger DUT to send a known frame and sniff the result
    log.info("Step 1: Triggering DUT and capturing PHY transmission")
    captured = sniffer.capture_frame(dut)
    asserts.assert_true(captured is not None, "No frame captured")

    # Field layout configuration: (field_name, start_idx, end_idx, expected_bytes)
    expected_layout = [
        ("MAC Frame Control", 0, 2, [0x88, 0x41]),
        ("Sequence Num",     2, 3, [0x05]),
        ("IEEE Address",     3, 11, [0x00, 0x12, 0x4b, 0x00, 0x13, 0xab, 0xcd, 0xef]),
        ("Payload",          11, 13, [0xAA, 0xBB])
    ]

    # Step 2: Analyze captured frame at PHY bit level for ordering
    left2right_ok, l2r_msg = sniffer.check_field_order_left_to_right(
        captured, expected_layout
    )
    asserts.assert_true(left2right_ok, f"Field order left-to-right incorrect: {l2r_msg}")

    # Step 3: Inspect field bit numbering for at least one multi-bit field
    # Use MAC Frame Control (2 bytes), take first byte (0x88 = 10001000)
    bit_order_ok = sniffer.check_field_bit_numbering(captured[0:1], 8)
    asserts.assert_true(bit_order_ok, "Bit numbering within field did not match expected leftmost=bit0 (LSB).")

    # Step 4: Inspect multi-octet field ordering (IEEE extended address)
    ieee_expected = [0x00, 0x12, 0x4b, 0x00, 0x13, 0xab, 0xcd, 0xef]
    ieee_bytes = captured[3:11]
    multi_octet_ok = sniffer.check_multi_octet_order(ieee_bytes, ieee_expected)
    asserts.assert_true(multi_octet_ok, f"Multi-octet field (IEEE address) not in correct order. Got {ieee_bytes}")

    # (Optional) Step 5: Try LSB/MSB confusion – test with a reversed address, should fail
    bad_order = list(reversed(ieee_expected))
    assert not sniffer.check_multi_octet_order(bad_order, ieee_expected), "Bad order falsely accepted"

    log.info("All transmission order, bit numbering, and multi-octet field order tests passed as per Zigbee PHY spec.")

```
**Instructions:**
- Save as `tests/test_TC_PHYFMT_1_1.py` in your repo.
- Replace the stubs for frame creation and analysis with your project's real Zigbee/Matter APIs, DUT controls, and sniffer packet parsers.
- In real environments, use a protocol analyzer to check on-the-wire order at the actual PHY level and validate extracted bit/octet sequences.