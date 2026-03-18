```python
#!/usr/bin/env -S python3 -B
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
# === BEGIN CI TEST ARGUMENTS ===
# test-runner-runs:
#   run1:
#     app: ${ALL_CLUSTERS_APP}
#     app-args: --discriminator 1234 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 1234
#       --passcode 20202021
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
#     factory-reset: true
#     quiet: true
# === END CI TEST ARGUMENTS ===

import pytest
from mobly import asserts

# You should replace the following with the actual way to access your device APIs.
# See the style in 'test_testing/TestInvokeReturnCodes.py' and other module imports.
# For now, we mock this using simple lambdas for illustration.

class DeviceSerializationAPI:
    """Placeholder for DUT communication. Replace with real APIs."""
    @staticmethod
    def serialize_integer(value: int, size_bytes: int) -> bytes:
        # Serializes to most-significant-octet first (big endian) of given size
        return value.to_bytes(size_bytes, byteorder='big')

    @staticmethod
    def deserialize_integer(octets: bytes) -> int:
        return int.from_bytes(octets, byteorder='big')

    @staticmethod
    def serialize_octet_string_to_binstr(octet_string: bytes) -> str:
        # Returns 'xxxxxxxx yyyyyyyy' with MSB first in each octet
        return ' '.join(f"{byte:08b}" for byte in octet_string)

# The test class follows the project CHIP test style (see examples).

class TestDevCodeSerialization:
    """
    TC-DEVCODE-1.1: Validate Integer and Octet Representation

    Tests serialization/deserialization of integer and octet string values
    for Zigbee codecs as specified in Zigbee Spec §2.2 [B7].
    """

    @pytest.mark.asyncio
    async def test_integer_4byte_to_octet_string(self):
        """
        Step 1: TH sends integer value 0x12345678 to DUT and requests its serialized octet string form.
                DUT returns octet string [0x12, 0x34, 0x56, 0x78]
        """
        integer = 0x12345678
        expected = bytes([0x12, 0x34, 0x56, 0x78])
        # Replace with: actual = await self.your_dut_api.serialize_integer(integer, size_bytes=4)
        actual = DeviceSerializationAPI.serialize_integer(integer, 4)
        asserts.assert_equal(actual, expected, "4-byte integer serialization MSB first order")

    @pytest.mark.asyncio
    async def test_integer_2byte_to_octet_string(self):
        """
        Step 2: TH sends integer value 0x0001 to DUT; requests serialized octet string.
                DUT returns octet string [0x00, 0x01]
        """
        integer = 0x0001
        expected = bytes([0x00, 0x01])
        actual = DeviceSerializationAPI.serialize_integer(integer, 2)
        asserts.assert_equal(actual, expected, "2-byte integer serialization MSB first order")

    @pytest.mark.asyncio
    async def test_octet_string_to_binary_string(self):
        """
        Step 3: TH requests DUT to serialize an octet string [0xAB, 0xCD].
                DUT represents it as bitstring "10101011 11001101" in MSB-first order.
        """
        octet_str = bytes([0xAB, 0xCD])
        expected_binstr = "10101011 11001101"
        actual_binstr = DeviceSerializationAPI.serialize_octet_string_to_binstr(octet_str)
        asserts.assert_equal(actual_binstr, expected_binstr, "Octet to binary string, MSB-first per byte")

    @pytest.mark.asyncio
    async def test_octets_to_integer_deserialization(self):
        """
        Step 4: TH requests DUT to deserialize octet string [0x12, 0x34, 0x56, 0x78] to integer.
                DUT returns integer 0x12345678.
        """
        octets = bytes([0x12, 0x34, 0x56, 0x78])
        expected = 0x12345678
        actual = DeviceSerializationAPI.deserialize_integer(octets)
        asserts.assert_equal(actual, expected, "Octet string deserialization (MSB first) to integer")

    @pytest.mark.asyncio
    async def test_additional_endianness_vectors(self):
        """
        Additional endianness/representation checks (optional).
        """
        cases = [
            (0x01000000, 4, bytes([0x01, 0x00, 0x00, 0x00])),
            (0x00000001, 4, bytes([0x00, 0x00, 0x00, 0x01])),
            (0xABCD, 2, bytes([0xAB, 0xCD]))
        ]
        for val, sz, expected in cases:
            actual = DeviceSerializationAPI.serialize_integer(val, sz)
            asserts.assert_equal(actual, expected, f"{sz}-byte serialization for 0x{val:X}")

# Note: If using the connectedhomeip runner, make sure to adapt to MatterBaseTest if needed,
#       and replace DeviceSerializationAPI with controller interface for real device.

```
Save this file as `tests/test_TC_DEVCODE_1_1.py`.  
Adapt `DeviceSerializationAPI` to use whatever DUT API is available (e.g., REST, cluster attribute, or RPC), and use async calls and real assertions as appropriate for your environment and test runner.