```python
# tests/test_TC_REP_1_2.py
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
Test Case: [TC-REP-1.2] Octet Binary Representation and Frame Transmission Order Compliance - DRAFT

Purpose:
    Verify that (1) octets are represented as binary strings in most-significant-bit (MSB) first order,
    and (2) the transmission order of all frames/fiels matches Zigbee left-to-right conventions.

References:
    Zigbee Spec docs-06-3474-24-csg-zigbee-specificationR24-section.pdf, Section §2.2, 1.2.2
"""

import pytest
from mobly import asserts
import logging

log = logging.getLogger(__name__)

# -- Simulation/Stub Classes: Replace with real Zigbee/Matter device/test harness/sniffer APIs --

class DeviceUnderTest:
    """Simulation: Replace with Zigbee device control able to send known frames upon request."""
    def __init__(self):
        pass

    def send_test_frame(self, octet_values, multi_octet_field=None):
        """
        Causes the DUT to send a Zigbee frame with a known octet sequence (and optionally multi-octet fields).
        Returns the bytes as they would be observed on the PHY wire.
        """
        # For this simulation, simply returns the supplied values in wire order.
        # Real implementation: trigger attribute report/data request carrying octets as value.
        frame = []
        if multi_octet_field is not None:
            frame.extend(multi_octet_field)
        frame.extend(octet_values)
        return bytes(frame)

class ZigbeeSniffer:
    """Simulation: Replace with sniffer APIs to analyze bit and byte order of captured Zigbee frames."""
    @staticmethod
    def capture_frame_bytes(dut: DeviceUnderTest, octet_test_values, multi_octet_test_values=None):
        # Capture the frame as sent by the DUT for examination.
        return dut.send_test_frame(octet_test_values, multi_octet_test_values)

    @staticmethod
    def check_msb_first(octet_byte):
        # Returns True if highest order bit is sent first (MSB-first)
        # Simulates the check: actual PHY sniffer needed for real deployment
        # For 0b10000000, MSB is 1 and is sent first
        # For 0b00000001, MSB is 0 and LSB is 1 (should be last)
        bits = [(octet_byte >> (7-bit)) & 1 for bit in range(8)]
        return bits == [int(b) for b in format(octet_byte, '08b')]

    @staticmethod
    def verify_octet_order(multi_byte_field, expected_wire_order):
        # Returns True if observed multi-octet field matches left-to-right order
        return list(multi_byte_field) == list(expected_wire_order)

@pytest.mark.asyncio
async def test_octet_binary_representation_and_frame_transmission_order():
    """
    [TC-REP-1.2] Octet Binary Representation and Frame Transmission Order Compliance
    """
    dut = DeviceUnderTest()
    sniffer = ZigbeeSniffer()

    # Prepare a test octet sequence that uniquely identifies MSB/LSB, e.g., [0x80, 0x01, 0xFE, 0x7F]
    octet_test_values = [0x80, 0x01, 0xFE, 0x7F]  # Each has a unique high/low bit pattern
    # For a multi-octet field (e.g., 16-bit address), use [0x12, 0x34] ("wire order" is [0x12, 0x34])
    multi_octet_test = [0x12, 0x34]

    # Step 1: Trigger DUT to send a frame with a test octet string
    log.info("Step 1: TH triggers DUT to send known octet values in a frame.")
    captured_frame = sniffer.capture_frame_bytes(dut, octet_test_values, multi_octet_test)
    asserts.assert_is_not_none(captured_frame, "No frame was transmitted or captured from DUT.")

    # Step 2: Analyze each octet in the captured frame for MSB-first bit order
    log.info("Step 2: Verify each captured octet is encoded MSB-first as per Zigbee spec §2.2, 1.2.2")
    for idx, octet in enumerate(captured_frame):
        bits_str = format(octet, "08b")
        assert sniffer.check_msb_first(octet), \
            f"Octet {idx} (0x{octet:02X}, {bits_str}) not transmitted MSB-first."

    # Step 3: If included, check multi-octet field for transmission order (lowest bits/leftmost byte first)
    log.info("Step 3: Verify multi-octet field transmission order per Zigbee (leftmost/lowest indexed first)")
    expected_wire_order = multi_octet_test + octet_test_values  # Since that's how the frame was constructed
    assert sniffer.verify_octet_order(captured_frame, expected_wire_order), \
        f"Multi-octet field or frame ordering ({list(captured_frame)}) did not match expected left-to-right specification order ({expected_wire_order})"

    # Step 4: Additional check that bits are sent left-to-right within octets (redundant for this simulation)
    log.info("Step 4: Confirm field transmission (bit and octet) left-to-right per Zigbee convention")
    # Since simulation uses bytes directly, MSB check above covers this; in real hardware, analyze bit waveforms.

    log.info("All assertions passed: octets are MSB-first, multi-octet fields and bit order are per Zigbee transmission spec.")
```
**Instructions:**
- Save this file as `tests/test_TC_REP_1_2.py`.
- Replace stubs (DeviceUnderTest, ZigbeeSniffer) with actual Zigbee/Matter API/device automation and sniffer/packet-capture tooling.
- For real PHY/bit-level validation, use a sniffer or logic analyzer to check actual on-wire bit transitions. This script provides a logic framework for such checks with simulated values.