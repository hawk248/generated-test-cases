```python
#!/usr/bin/env python3
#
#    Copyright (c) 2024 Project CHIP Authors
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

import pytest

# === BEGIN TEST CASE INFO ===
# TC-FRMT-1.1: PHY Transmission Order and Field Bit Numbering Validation
# Requirement:
#   1. Frame formats transmitted left to right, leftmost bit first.
#   2. Bits within each field: 0 (leftmost, least significant) to k-1 (rightmost, most significant).
#   3. Multi-octet fields transmitted octet with the lowest numbered bits first.
#   Source: Zigbee Spec [docs-06-3474-24-csg-zigbee-specificationR24]
#           Section 1.2.3, lines 1196–1204.
# Devices:
#   - DUT: Zigbee PHY/MAC transmitter.
#   - TH: Protocol sniffer/PHY analyzer.
# === END TEST CASE INFO ===


@pytest.mark.asyncio
async def test_phy_frame_transmission_order(zb_device, phy_sniffer):
    """
    TC-FRMT-1.1 — PHY Transmission Order and Field Bit Numbering Validation

    Purpose:
      - Validate Zigbee PHY transmission order: bits, bytes, and field handling.

    Test Steps:
      1. Commission device and configure a test MAC frame with a known 2-octet field.
      2. Have sniffer record the transmission at the bit level.
      3. Inspect bit order: leftmost/LSB first.
      4. Inspect field bit numbering (0 = leftmost/LSB, k-1 = rightmost/MSB).
      5. Inspect multi-octet field: lowest-numbered octet first.
      6. Compare with expected spec encoding.
    """

    # STEP 1: Commission DUT and prepare known frame (e.g., with a 2-octet field)
    # --- Use a known address (0x1234) with unique pattern for clarity
    test_address = 0x1234
    frame = zb_device.prepare_test_frame(multi_octet_field=test_address)
    await zb_device.send_frame(frame)

    # STEP 2: Capture raw PHY transmission at the bit level
    # --- Sniffer must be able to return a structure like:
    # {
    #     "field_name": ...,
    #     "raw_bits": "LSB/bit0,bit1,...bitk",
    #     "raw_bytes": [octet0, octet1, ...]
    # }
    capture = await phy_sniffer.capture_last_frame()

    # STEP 3: Inspect the transmitted bits: leftmost/LSB first in stream
    first_bit = capture.raw_bits[0]
    expected_first_bit = (test_address & 0x1)  # LSB of leftmost field bit
    assert first_bit == expected_first_bit, (
        f"First transmitted bit '{first_bit}' not matching LSB of field value '{expected_first_bit}'"
    )

    # STEP 4: Confirm field bit numbering (0 = leftmost/LSB, up to k-1 = rightmost/MSB)
    for field_name, field_info in capture.fields.items():
        bits = field_info['raw_bits']
        for i, bit in enumerate(bits):
            expected_bit_val = (field_info['expected_val'] >> i) & 0x1
            assert bit == expected_bit_val, (
                f"Bit {i} of field '{field_name}' does not match least-significant numbering. "
                f"Got {bit}, expected {expected_bit_val}"
            )

    # STEP 5: Multi-octet field: octet with lowest-numbered bits is sent first
    # In 0x1234, octet[0]=0x34, octet[1]=0x12 (little endian for lowest bits first)
    multi_octet = capture.fields["multi_octet_field"]['raw_bytes']
    expected_octets = [0x34, 0x12]  # Ordering: lowest-numbered bits to highest
    assert list(multi_octet) == expected_octets, (
        f"Multi-octet field byte order: got {multi_octet}, expected {expected_octets}"
    )

    # STEP 6: Full order and structure match encoding sequence from spec
    expected_frame_bits = zb_device.get_expected_bit_sequence_for_field(test_address)  # helper method
    assert capture.raw_bits == expected_frame_bits, (
        f"Entire frame bitwise mismatch: got {capture.raw_bits}, expected {expected_frame_bits}"
    )

    # Comments on test
    # Use unique bit/byte patterns to ensure detection of order issues.
    # This test assumes test fixtures/hooks provided on zb_device and phy_sniffer.


# To run with pytest:
# $ pytest tests/test_TC_FRMT_1_1.py
```
**NOTES/ASSUMPTIONS:**
- The test expects the fixture `zb_device` to provide Zigbee PHY/MAC transmit functions and helpers to prepare/send a test frame with a known field value.
- The fixture `phy_sniffer` represents a PHY test harness/sniffer, capable of capturing and exposing transmission at bit and byte detail (fields, raw bits, etc).
- You must adapt the field/attribute names or capture format depending on the sniffer/tooling used in your environment.
- If you do not have a real sniffer, you may mock `phy_sniffer.capture_last_frame()` for development/unit test execution.

**Place this file as**: `tests/test_TC_FRMT_1_1.py`
