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

import pytest
from mobly import asserts

# These are placeholder interfaces for framework/harness access.
# In your environment, replace them with real API/methods for DUT security, ACL, NWK key handling, and traffic simulation.
try:
    from zigbee.security import (
        configure_acl,            # (dut_id, entries)
        get_acl_entries,          # (dut_id)
        send_cluster_command,     # (src_id, dst_id, command, key)
        rotate_network_keys,      # (dut_id, active_key, alternate_key)
        get_network_key_status,   # (dut_id)
        send_secured_nwk_frame,   # (src_id, dst_id, payload, key)
        sniff_last_outgoing_nwk_frame,  # (dut_id)
    )
except ImportError:
    # Stub mock implementations for local or CI stub testing; replace with actual project modules
    configure_acl = get_acl_entries = send_cluster_command = rotate_network_keys = \
        get_network_key_status = send_secured_nwk_frame = sniff_last_outgoing_nwk_frame = None


@pytest.mark.asyncio
async def test_access_control_list_and_nwk_keys():
    """
    TC-SECURITY-1.1: Validation of Access Control List and Network Key Handling

    - Verifies ACL enforcement and security material storage
    - Validates correct usage of Active and Alternate Network Keys
    """

    DUT = "dut-node-id"
    AUTHORIZED_ID = "auth-device-id"
    UNAUTHORIZED_ID = "unauth-device-id"
    CLUSTER_COMMAND = {"cluster": "OnOff", "command": "On"}
    ACTIVE_NWK_KEY = b"\x11" * 16
    ALT_NWK_KEY = b"\x22" * 16

    # Step 0: Commission DUT in network and configure ACL and keys
    # ACL Entry for authorized, plus one unauthorized device; keys and security attributes included
    acl_entries = [
        {
            "device_id": AUTHORIZED_ID,
            "authorized": True,
            "security_material": {
                "nwk_key": ACTIVE_NWK_KEY,
                "frame_count": 0xA5,
                "security_level": 5
            }
        },
        {
            "device_id": UNAUTHORIZED_ID,
            "authorized": False
        }
    ]
    await configure_acl(DUT, acl_entries)
    await rotate_network_keys(DUT, ACTIVE_NWK_KEY, ALT_NWK_KEY)

    # === Step 1: Authorized device - request is performed
    auth_result = await send_cluster_command(
        src_id=AUTHORIZED_ID,
        dst_id=DUT,
        command=CLUSTER_COMMAND,
        key=ACTIVE_NWK_KEY,
    )
    asserts.assert_true(
        auth_result.success,
        "Authorized device request was not performed despite correct ACL/security."
    )

    # === Step 2: Unauthorized device - request denied
    unauth_result = await send_cluster_command(
        src_id=UNAUTHORIZED_ID,
        dst_id=DUT,
        command=CLUSTER_COMMAND,
        key=ACTIVE_NWK_KEY,
    )
    asserts.assert_false(
        unauth_result.success,
        "Unauthorized device was not rejected by access control."
    )

    # === Step 3: ACL readability (direct or indirect)
    acl_readback = await get_acl_entries(DUT)
    asserts.assert_in(
        AUTHORIZED_ID, [entry["device_id"] for entry in acl_readback],
        "Authorized device missing from ACL."
    )
    # Optionally check for security material if supported
    auth_entry = next(e for e in acl_readback if e["device_id"] == AUTHORIZED_ID)
    if "security_material" in auth_entry:
        sm = auth_entry["security_material"]
        asserts.assert_equal(sm["nwk_key"], ACTIVE_NWK_KEY, "Stored NWK key mismatch in ACL entry.")
        asserts.assert_in("frame_count", sm, "Frame count missing from security material.")

    # === Step 4: Accept secured NWK frame using Active Key
    frame_payload = b'\xDE\xAD'
    nwk_frame_active_result = await send_secured_nwk_frame(
        src_id=AUTHORIZED_ID,
        dst_id=DUT,
        payload=frame_payload,
        key=ACTIVE_NWK_KEY
    )
    asserts.assert_true(
        nwk_frame_active_result.accepted,
        "DUT should accept secured frame using the Active NWK key."
    )

    # === Step 5: Accept secured NWK frame using Alternate Key
    nwk_frame_alt_result = await send_secured_nwk_frame(
        src_id=AUTHORIZED_ID,
        dst_id=DUT,
        payload=frame_payload,
        key=ALT_NWK_KEY
    )
    asserts.assert_true(
        nwk_frame_alt_result.accepted,
        "DUT should accept secured frame using the Alternate NWK key."
    )

    # === Step 6: Outgoing frame from DUT is secured with Active Network Key
    # Trigger outgoing NWK message from DUT (e.g., command reply or notification)
    # This would, in real test, be triggered by a prior request, or by instructing DUT to send.
    # Then verify with a sniffer/log that the frame is protected with ACTIVE_NWK_KEY
    outgoing_frame = await sniff_last_outgoing_nwk_frame(DUT)
    asserts.assert_is_not_none(outgoing_frame, "No outgoing NWK frame detected from DUT.")
    asserts.assert_equal(
        outgoing_frame.used_key, ACTIVE_NWK_KEY,
        "NWK frame was not secured using the Active Network Key."
    )

    print("TC-SECURITY-1.1: All access control and NWK key validation steps passed.")

# Place this test in: tests/test_TC_SECURITY_1_1.py
```
**NOTES:**
- Replace the imports and function calls with your actual Python interfaces for Zigbee ACL and security/key management (e.g., cluster attribute writes, D-Bus APIs, RPCs, etc).
- Test harness (`TH`) roles are simulated through authorized/unauthorized identities.
- All key/ACL values are illustrative—update usage and device IDs according to your testbed.
- Each assert and print maps to a TC step, enabling automatic CI output traceability.
- Ensure all cryptographic/key operations comply with your environment's security requirements.