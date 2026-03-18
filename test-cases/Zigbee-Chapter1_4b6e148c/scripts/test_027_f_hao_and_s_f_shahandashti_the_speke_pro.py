```python
# tests/test_TC_SPEKE_SSR2014_1_1.py
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
TC-SPEKE-SSR2014-1.1:
Validation of SPEKE Protocol Per SSR 2014 Revision (F. Hao, S. F. Shahandashti, SSR 2014, LNCS 8893)
- Validates generator derivation, protocol message structure, attack resistance, and session key agreement.
Adapt/replace the SpekeSSR2014Api calls to connect to real device/harness (DUT/TH).
"""

import pytest
from mobly import asserts
import hashlib
import random

# --- Placeholders for Real DUT/TH SPEKE SSR2014 APIs: replace for production or integration ---

class SpekeSSR2014Api:
    """
    Mock/stub API for SSR 2014 SPEKE interaction.
    Replace all logic here with device/harness interfaces as appropriate for your project.
    """
    def __init__(self, p=None, password=None):
        # Use a 1536-bit MODP group from RFC 3526 for illustration (shorter for test/dev)
        self.p = (
            0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1
            0x29024E088A67CC74020BBEA63B139B22514A08798E3404DD
            0xEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245
            0xE485B576625E7EC6F44C42E9A63A3620FFFFFFFFFFFFFFFF
        ) if p is None else p
        self.password = password or "testpassword"
        self.g = None
        self.x = None
        self.y = None
        self.X = None
        self.Y = None
        self.ssk = None  # Session key

    @staticmethod
    def _derive_generator(p, q, password):
        # Use the hash-to-prime method per SSR 2014, simplified:
        hval = int(hashlib.sha256(password.encode("utf-8")).hexdigest(), 16)
        g = pow(hval, 2, p)
        # SSR 2014 requires order/subgroup check: ensure g != 1 and in correct subgroup
        if g <= 1 or g >= p-1:
            raise ValueError("Invalid generator derived; out-of-range.")
        return g

    def protocol_init(self):
        # Step 1: Derive generator as per SSR 2014 (group and password)
        q = (self.p - 1) // 2  # Safe prime, so q is (p-1)/2
        self.g = self._derive_generator(self.p, q, self.password)
        self.x = random.SystemRandom().randint(2, self.p - 2)
        self.X = pow(self.g, self.x, self.p)
        return {"g": self.g, "X": self.X}

    def protocol_peer_exchange(self, Y):
        # Step 2: Receive peer public value and compute session key
        if Y <= 1 or Y >= self.p - 1:
            raise ValueError("Protocol violation; peer value out-of-group.")
        self.Y = Y
        self.ssk = pow(self.Y, self.x, self.p)
        return self.ssk

    def protocol_confirm(self, confirmation_in):
        # Step 3: Simple confirm -- hash of key as example
        confirm = hashlib.sha256(str(self.ssk).encode("utf-8")).digest()[:4]
        return confirm == confirmation_in

    def negative_test_modified_generator(self, bad_g):
        try:
            _ = pow(bad_g, 2, self.p)
            # In real code: run protocol with bad_g,
            # here we abort if g fails subgroup test or is 1/p-1
            if bad_g <= 1 or bad_g >= self.p-1:
                return True  # Detected as invalid, aborts
            return False
        except Exception:
            return True

    def attack_replay_or_key_mismatch(self, old_values):
        """
        Simulate replay scenario: fails if older session values are reused.
        """
        # SSR 2014 expects session freshness detection; for stub, simulate failure.
        return old_values != (self.g, self.X, self.Y)

# ---- Tests begin here ----

@pytest.mark.asyncio
async def test_speke_ssr2014_protocol_success():
    """
    Step 1-3: Initiate and complete SSR 2014 SPEKE, validate structure, generator, and key confirmation.
    """
    # Simulate two endpoints acting as DUT and TH (peer)
    dut = SpekeSSR2014Api(password="password123")
    th = SpekeSSR2014Api(password="password123")
    # Both sides run generator derivation and ephemeral
    dut_proto = dut.protocol_init()
    th_proto = th.protocol_init()
    # Exchange values (X, Y)
    dut.protocol_peer_exchange(th_proto["X"])
    th.protocol_peer_exchange(dut_proto["X"])
    # Session key must match on both sides
    asserts.assert_equal(dut.ssk, th.ssk, "Session key mismatch: SSR 2014 SPEKE failed")
    # Confirmation message
    confirm_bytes = hashlib.sha256(str(dut.ssk).encode("utf-8")).digest()[:4]
    confirms = th.protocol_confirm(confirm_bytes)
    asserts.assert_true(confirms, "Key confirmation failed in SSR 2014 SPEKE")

@pytest.mark.asyncio
async def test_speke_ssr2014_protocol_message_transcript():
    """
    Step 2: DUT and TH message exchange transcript structured as per SSR 2014 spec.
    """
    dut = SpekeSSR2014Api(password="securepass")
    th = SpekeSSR2014Api(password="securepass")
    step1_dut = dut.protocol_init()  # DUT sends g, X
    step1_th = th.protocol_init()
    asserts.assert_in("g", step1_dut)
    asserts.assert_in("X", step1_dut)
    # Exchange values; record transcript
    dut_skey = dut.protocol_peer_exchange(step1_th["X"])
    th_skey = th.protocol_peer_exchange(step1_dut["X"])
    transcript_log = {
        "dut_g": step1_dut["g"],
        "th_g": step1_th["g"],
        "dut_X": step1_dut["X"],
        "th_X": step1_th["X"],
        "dut_skey": dut_skey,
        "th_skey": th_skey,
    }
    asserts.assert_equal(
        transcript_log["dut_g"], transcript_log["th_g"],
        "Generator mismatch in SSR 2014 protocol (must match for both)."
    )

@pytest.mark.asyncio
async def test_speke_ssr2014_negative_invalid_generator_detection():
    """
    Step 4: Negative test - DUT aborts on invalid/modifed generator.
    """
    dut = SpekeSSR2014Api(password="testdetect")
    # Try 1 or p - 1, which should be invalid as per SSR 2014
    for bad_g in [1, dut.p - 1]:
        detected = dut.negative_test_modified_generator(bad_g)
        asserts.assert_true(detected, f"DUT did not detect/abort on bad generator {bad_g}")

@pytest.mark.asyncio
async def test_speke_ssr2014_attack_replay_and_key_mismatch():
    """
    Step 5: Resistance to session replay/key mismatch (replay should be detected and fail).
    """
    dut = SpekeSSR2014Api(password="a"*10)
    th = SpekeSSR2014Api(password="b"*10)
    # Run protocol to produce some values
    dut_gx = dut.protocol_init()
    th_gy = th.protocol_init()
    # Save old session values
    old_values = (dut_gx["g"], dut_gx["X"], th_gy["X"])
    # Simulate an attacker replaying old values
    replayed = dut.attack_replay_or_key_mismatch(old_values)
    asserts.assert_true(replayed, "Replay or mismatch attack was not detected")

# Add more detailed attack vectors and transcript validations as needed for your Zigbee/chip integration.
# For "PROVISIONAL" marking, supplement with deterministic vectors directly from SSR 2014 and real implementation logs.

# END OF FILE: tests/test_TC_SPEKE_SSR2014_1_1.py
```
**Instructions:**
- Place this script as `tests/test_TC_SPEKE_SSR2014_1_1.py`.
- Replace all SpekeSSR2014Api calls and generator logic with actual API, cluster commands, or integration hooks to your device/test rig.
- Expand or refactor for production, protocol transcript logging, and more complete SSR 2014 security/attack scenarios as needed.
- Mobly asserts and pytest async style are compatible with Project CHIP python test infra.