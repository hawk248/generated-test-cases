```python
# tests/test_TC_CHARSET_1_1.py
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
Test Case: TC-CHARSET-1.1
ISO/IEC 646 (7-bit ASCII) Character Set Encoding/Decoding – DRAFT

Validates that the DUT correctly encodes and decodes character data using the ISO/IEC 646 character set (ASCII).
"""

import pytest
from mobly import asserts

# --- Placeholder harness for string storage/retrieval/encoding on DUT ---
# Replace these with your actual Matter/Zigbee string attribute/command APIs!

class DUTCharsetAPI:
    """
    Simulates DUT's ISO/IEC 646 string attribute/command interface.
    Replace all methods with async APIs or direct access to device as needed.
    """
    _storage = {}

    @staticmethod
    async def store_string(key: str, value: str):
        # Only store valid ISO/IEC 646 chars (0x00-0x7F), simulate possible DUT behavior
        for c in value:
            if ord(c) > 0x7F:
                raise ValueError("Out-of-range character")
        DUTCharsetAPI._storage[key] = value

    @staticmethod
    async def get_string(key: str) -> str:
        # Return stored value, if present
        return DUTCharsetAPI._storage.get(key, "")

    @staticmethod
    async def encode_to_ascii_binary(s: str) -> bytes:
        # Returns bytes, where each char is encoded as per ASCII (0x00-0x7F)
        return bytes(ord(c) for c in s if ord(c) <= 0x7F)

# ---- Test vectors for ISO/IEC 646 (ASCII) ----
ASCII_TEST_STRING = "Hello123!@#"
ASCII_CONTROL_CHARS = "".join(chr(i) for i in [0x00, 0x1F, 0x7F]) + "A"
OUT_OF_RANGE_STRING = "NormalASCII" + chr(0x80) + chr(0xFF)
BOUNDARY_STRING = "".join(chr(i) for i in range(32, 127))  # All printable 7-bit chars

@pytest.mark.asyncio
async def test_valid_ascii_storage_and_retrieval():
    """
    Step 1/2: Send valid ASCII string to DUT, retrieve, and verify.
    """
    key = "s1"
    await DUTCharsetAPI.store_string(key, ASCII_TEST_STRING)
    retrieved = await DUTCharsetAPI.get_string(key)
    asserts.assert_equal(
        retrieved, ASCII_TEST_STRING,
        f"DUT did not preserve ASCII string: sent [{ASCII_TEST_STRING}], got [{retrieved}]"
    )

@pytest.mark.asyncio
async def test_ascii_control_characters():
    """
    Step 3: Store and retrieve control/boundary chars.
    """
    key = "s2"
    # Accept if device can store all allowed ASCII (some implementations may restrict control chars)
    try:
        await DUTCharsetAPI.store_string(key, ASCII_CONTROL_CHARS)
        retrieved = await DUTCharsetAPI.get_string(key)
        asserts.assert_equal(
            retrieved, ASCII_CONTROL_CHARS,
            f"DUT did not handle/control characters: sent [{ASCII_CONTROL_CHARS}], got [{retrieved}]"
        )
    except ValueError:
        # Acceptable if DUT rejects (but it must NOT corrupt/truncate silently)
        pass

@pytest.mark.asyncio
async def test_out_of_range_ascii_rejection():
    """
    Step 4: DUT must NOT silently accept or encode 8-bit/Unicode chars
    """
    key = "s3"
    with pytest.raises(ValueError):
        await DUTCharsetAPI.store_string(key, OUT_OF_RANGE_STRING)

@pytest.mark.asyncio
async def test_ascii_encoding_as_binary():
    """
    Step 5: Verify binary encoding (ASCII, 7-bit mapped)
    """
    ref = "Sample!"
    expected = bytes(ord(c) for c in ref)
    encoded = await DUTCharsetAPI.encode_to_ascii_binary(ref)
    asserts.assert_equal(
        encoded, expected,
        f"Binary encoding of '{ref}' is not standard ASCII: expected {expected}, got {encoded}"
    )

@pytest.mark.asyncio
async def test_full_ascii_boundary_chars():
    """
    Optional: Test all printable 7-bit ASCII chars
    """
    key = "s4"
    await DUTCharsetAPI.store_string(key, BOUNDARY_STRING)
    received = await DUTCharsetAPI.get_string(key)
    asserts.assert_equal(
        received, BOUNDARY_STRING,
        "DUT's ASCII handling does not match all printable boundary chars"
    )

# Notes:
# - In actual project, replace DUTCharsetAPI with calls to your device-under-test.
# - Add further fixtures or device reset/setup as needed for full integration.
# - Each assertion and exception maps directly to an original test case step.
# - For negative checks (Step 4), DUT may raise or error appropriately according to spec.


# END OF FILE: tests/test_TC_CHARSET_1_1.py
```
