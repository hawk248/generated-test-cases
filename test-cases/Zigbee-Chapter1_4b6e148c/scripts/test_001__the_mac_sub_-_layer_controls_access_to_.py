```python
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
Test Case: TC-MAC-1.1 - MAC Sub-layer Access and Transmission Control
API Test for 802.15.4 MAC layer - validates CSMA-CA/LBT, beacon, synchronization, and transmission reliability.

- Assumes existence of a Python API client for the Device Under Test (DUT) and Test Harness (TH),
  with appropriate methods for MAC/PHY manipulation, frame transmission, and environment control.
"""

import pytest
from unittest.mock import MagicMock

# Mocks for illustrative purposes only; replace these with real API bindings or system calls.
# Example: from chip_mac import MACApi

class MACApiMock:
    def __init__(self, beacon_capable=False):
        self.beacon_capable = beacon_capable
        self.transmission_log = []
        self.beacon_log = []
        self.synchronized = True
        self.last_tx_status = "IDLE"
        self.environment = {"channel_busy": False, "coordinator_time": 0}
        
    def set_mac_mode(self, mode):
        assert mode in ("CSMA-CA", "LBT")
        self.mac_mode = mode

    def configure_beaconing(self, enabled, interval_ms=100):
        self.beacon_capable = enabled
        self.beacon_interval_ms = interval_ms

    def transmit_data_frame(self, frame):
        # Step 1 & 2: Channel access simulation
        if self.environment["channel_busy"]:
            if self.mac_mode == "CSMA-CA":
                # Delay/retry logic, simplified
                self.last_tx_status = "BACKOFF_RETRY"
                return False  # Do not transmit until free
            elif self.mac_mode == "LBT":
                self.last_tx_status = "LISTEN_DEFER"
                return False
        self.last_tx_status = "SUCCESS"
        self.transmission_log.append(frame)
        return True

    def induce_frame_loss(self):
        # Step 4: Frame loss simulation (for reliability test)
        self.last_tx_status = "TX_FAILED"
    
    def retry_last_frame(self):
        # Simplified retry for test
        retry_success = True
        self.last_tx_status = "SUCCESS" if retry_success else "FAILED"
        self.transmission_log.append("retransmit")
        return retry_success

    def start_beacon(self):
        # Step 3: Beacon simulation
        if not self.beacon_capable:
            return False
        self.beacon_log.append("beacon_tx")
        return True

    def get_beacon_count(self):
        return len(self.beacon_log)

    def set_channel_busy(self, busy=True):
        self.environment["channel_busy"] = busy

    def synchronize_to_coordinator(self, new_time):
        # Step 5: Synchronization simulation
        if abs(new_time - self.environment["coordinator_time"]) > 0:
            self.synchronized = True
            self.environment["coordinator_time"] = new_time
        return self.synchronized

# Fixtures
@pytest.fixture(params=["CSMA-CA", "LBT"])
def mac_dut(request):
    """ Initialize the MACApiMock for each supported MAC mode. """
    dut = MACApiMock(beacon_capable=True)
    dut.set_mac_mode(request.param)
    return dut

@pytest.fixture
def test_harness():
    """ Provide a test harness (TH) instance with monitoring/injection support. """
    th = MagicMock()
    return th

# STEP 1: Instruct DUT to transmit a data frame on an idle channel
def test_transmit_on_idle_channel(mac_dut, test_harness):
    mac_dut.set_channel_busy(False)  # Ensure channel is idle
    result = mac_dut.transmit_data_frame(frame="frame-1")
    assert result, "DUT should transmit frame successfully on idle channel"
    assert mac_dut.last_tx_status == "SUCCESS"

# STEP 2: Simulate busy channel and check MAC access (CSMA-CA/LBT backoff/listen)
def test_transmit_on_busy_channel(mac_dut, test_harness):
    mac_dut.set_channel_busy(True)   # Channel busy state
    result = mac_dut.transmit_data_frame(frame="frame-2")
    assert not result, "DUT should defer transmission or backoff on busy channel"
    # Check if MAC behavior matches mode-specific expectation
    if mac_dut.mac_mode == "CSMA-CA":
        assert mac_dut.last_tx_status == "BACKOFF_RETRY"
    elif mac_dut.mac_mode == "LBT":
        assert mac_dut.last_tx_status == "LISTEN_DEFER"

# STEP 3: (If beacon-capable) Instruct DUT to transmit beacon frames at configured interval
def test_beacon_transmission(mac_dut, test_harness):
    if not mac_dut.beacon_capable:
        pytest.skip("DUT does not support beaconing. Skipping.")
    initial_beacons = mac_dut.get_beacon_count()
    assert mac_dut.start_beacon(), "DUT should be able to send beacon"
    assert mac_dut.get_beacon_count() == initial_beacons + 1, "Beacon transmission should be logged"

# STEP 4: Induce frame loss; DUT should retry/retransmit as per reliability mechanism
def test_transmission_reliability(mac_dut, test_harness):
    # Simulate transmission, then induce loss
    mac_dut.transmit_data_frame(frame="frame-3")
    mac_dut.induce_frame_loss()
    assert mac_dut.last_tx_status == "TX_FAILED", "Frame loss should be indicated"
    retry_result = mac_dut.retry_last_frame()
    assert retry_result, "DUT should retry transmission after frame loss"
    assert mac_dut.last_tx_status == "SUCCESS", "Retry should eventually succeed"

# STEP 5: If sync supported: Change network coordinator timing, check that DUT synchronizes
def test_mac_synchronization(mac_dut, test_harness):
    new_coordinator_time = 12345  # Example new time for coordinator
    result = mac_dut.synchronize_to_coordinator(new_coordinator_time)
    assert result, "DUT should synchronize to new coordinator timing"
    assert mac_dut.environment["coordinator_time"] == new_coordinator_time

# Additional notes:
# - In a real implementation, replace MACApiMock with real device APIs.
# - This test suite can be extended for multi-mode MAC/PHY DUTs by parametrize/loop.
# - Add logs/prints as needed for CI traceability, following project conventions.
```
Save as: `tests/test_TC_MAC_1_1.py`