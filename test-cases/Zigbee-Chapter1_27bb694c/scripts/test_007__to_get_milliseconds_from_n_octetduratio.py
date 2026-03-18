```python
# tests/test_TC_TIME_1_1.py
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
Test Case: [TC-TIME-1.1] Verification of OctetDuration to Milliseconds Conversion for 2.4 GHz – DRAFT

Purpose:
    Validate device under test (DUT) correctly converts the number of OctetDurations to milliseconds
    for the 2.4 GHz PHY using the formula: ms = N * (8/250000) * 1000
"""

import pytest
from mobly import asserts
import math
import logging

log = logging.getLogger(__name__)

# --- STUB/Placeholders for DUT/TH integration. Replace with actual stack/harness API. ---

class DeviceUnderTest:
    """
    Simulates the DUT providing an API/attribute for converting N octet durations to milliseconds.
    """
    PHYSICAL_MODE = "2.4GHz"
    BIT_RATE_2_4GHZ = 250000  # bits/second

    def __init__(self):
        self.phy_mode = self.PHYSICAL_MODE

    def set_phy_mode(self, mode):
        self.phy_mode = mode

    def convert_octet_durations_to_ms(self, N):
        """
        Simulates the conversion.
        Returns: milliseconds as a float.
        Only valid for 2.4GHz in this test.
        """
        if self.phy_mode != self.PHYSICAL_MODE:
            raise ValueError("DUT not in 2.4GHz mode for timing conversion")
        return N * (8 / self.BIT_RATE_2_4GHZ) * 1000


class TestHarness:
    """
    Simulates the test harness that will request conversions and verify correctness.
    """
    TOLERANCE = 0.02  # 2% tolerance for floating point/impl. rounding

    def __init__(self, dut):
        self.dut = dut

    def check_conversion(self, N, expected_ms):
        obtained = self.dut.convert_octet_durations_to_ms(N)
        abs_diff = abs(obtained - expected_ms)
        tol = abs(expected_ms) * self.TOLERANCE
        msg = (
            f"DUT: For N={N}, expected {expected_ms:.4f} ms, got {obtained:.4f} ms"
        )
        # Allow for small tolerance (<=2% or absolute <=0.01ms for very small)
        asserts.assert_true(
            abs_diff <= max(tol, 0.01),
            f"{msg} (difference {abs_diff:.4f} ms > tolerance {tol:.4f})"
        )
        log.info(f"PASS: {msg} (difference={abs_diff:.4f} ms ≤ tolerance={tol:.4f})")


@pytest.mark.asyncio
async def test_tc_time_1_1_octetduration_to_milliseconds_conversion():
    """
    [TC-TIME-1.1] Verification of OctetDuration to Milliseconds Conversion for 2.4 GHz
    """
    dut = DeviceUnderTest()
    th = TestHarness(dut)
    dut.set_phy_mode("2.4GHz")

    # Step 1: Test N = 1
    th.check_conversion(N=1, expected_ms=1 * (8/250000) * 1000)  # 0.032 ms

    # Step 2: Test N = 10
    th.check_conversion(N=10, expected_ms=10 * (8/250000) * 1000)  # 0.32 ms

    # Step 3: Test N = 125
    th.check_conversion(N=125, expected_ms=125 * (8/250000) * 1000)  # 4.0 ms

    # Step 4: Test N = 250
    th.check_conversion(N=250, expected_ms=250 * (8/250000) * 1000)  # 8.0 ms

    # Step 5: Test additional N values (edge, 0, negative, large)
    for N in [0, 500, 1000, 7, 10000, 50]:
        th.check_conversion(N, expected_ms=N * (8 / 250000) * 1000)

    # Negative/invalid case: try with non-2.4GHz mode (should raise)
    dut.set_phy_mode("SubGHz")
    try:
        dut.convert_octet_durations_to_ms(10)
        assert False, "DUT did not raise error when not in 2.4GHz mode"
    except ValueError:
        log.info("PASS: DUT correctly rejected conversion when not in 2.4GHz mode")

    log.info("All octetduration to ms conversion checks for 2.4 GHz PHY passed per spec.")

```
**Instructions:**
- Save this file as `tests/test_TC_TIME_1_1.py` in your repo.
- Replace all device/harness stubs with the actual API/attribute/control interface for your platform.
- Add more parameterized values as needed for thoroughness or extend to handle error/edge/bounds as your spec requires.
