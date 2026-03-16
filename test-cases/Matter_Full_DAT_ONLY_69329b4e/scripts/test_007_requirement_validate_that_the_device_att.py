```python
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
TC-ATTES-1.1: Device Attestation Signature Validation

Purpose:
    Verify the device attestation signature in the Attestation Response is valid per the DAC public key
    and proper construction of the attestation_tbs, as required by Matter Section 6.51 and 11.18.4.7.
"""

from mobly import asserts
import pytest
import matter.clusters as Clusters
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main
from matter.testing.decorators import async_test_body
from matter.exceptions import ChipStackError

from pyasn1.codec.der import decoder as der_decoder
from pyasn1_modules import rfc2459

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509 import load_der_x509_certificate
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import binascii

class TestAttestationSignature(MatterBaseTest):
    """
    TC-ATTES-1.1: Device Attestation Signature Validation
    """

    @async_test_body
    async def test_attestation_signature_validation(self):
        # ---- Step 1: Start secure session & send AttestationRequest command ----
        self.print_step(1, "TH sends AttestationRequest Command to DUT")
        # Secure channel setup must be complete before this test
        attestation_response = await self.send_attestation_request(self.dut_node_id)

        # ---- Step 2: Extract AttestationElements & AttestationSignature ----
        self.print_step(2, "TH extracts AttestationElements and AttestationSignature from response")
        att_elements = attestation_response.get("AttestationElements", None)
        att_signature = attestation_response.get("AttestationSignature", None)
        asserts.assert_is_not_none(att_elements, "AttestationElements missing from response")
        asserts.assert_is_not_none(att_signature, "AttestationSignature missing from response")

        # ---- Step 3: Obtain DUT's DAC public key ----
        self.print_step(3, "TH obtains DUT's public key from the DAC certificate (from elements or out-of-band)")
        dac_cert_der = self.get_dac_cert_from_attestation_elements(att_elements)
        asserts.assert_is_not_none(dac_cert_der, "Could not extract DAC certificate DER data")

        dac_cert_obj = load_der_x509_certificate(dac_cert_der)
        public_key = dac_cert_obj.public_key()
        # Ensure it's an EC (P-256) public key
        asserts.assert_true(isinstance(public_key, ec.EllipticCurvePublicKey), "DAC public key is not EC")

        # ---- Step 4: Reconstruct attestation_tbs per Matter spec ----
        self.print_step(4, "TH reconstructs attestation_tbs using AttestationElements and Challenge")
        attestation_challenge = attestation_response.get("AttestationChallenge", None)
        asserts.assert_is_not_none(attestation_challenge, "AttestationChallenge not in AttestationResponse")
        # Per Matter spec, AttestationTBS = AttestationElements || AttestationChallenge
        # Both are bytes fields (CBOR, TLV, or ASN.1 encoded); use as-is
        if isinstance(att_elements, str): # may be hex
            att_elements_bytes = binascii.unhexlify(att_elements)
        else:
            att_elements_bytes = att_elements
        if isinstance(attestation_challenge, str):
            attestation_challenge_bytes = binascii.unhexlify(attestation_challenge)
        else:
            attestation_challenge_bytes = attestation_challenge

        attestation_tbs = att_elements_bytes + attestation_challenge_bytes

        # ---- Step 5: Verify AttestationSignature using DAC public key ----
        self.print_step(5, "TH verifies AttestationSignature using Crypto_Verify (ECDSA-P256-SHA256)")

        # Matter signatures are ECDSA (raw ASN.1 DER, sometimes as raw r+s)
        signature_bytes = att_signature if isinstance(att_signature, bytes) else binascii.unhexlify(att_signature)
        try:
            public_key.verify(signature_bytes, attestation_tbs, ec.ECDSA(hashes.SHA256()))
            valid_sig = True
        except InvalidSignature:
            valid_sig = False
        except Exception as e:
            asserts.fail(f"Unexpected error during signature verification: {e}")
        asserts.assert_true(valid_sig, "Failed to verify Attestation Signature with DUT's DAC public key.")

        # ---- Step 6: Negative - Verify fails if inputs are tampered ----
        self.print_step(6, "Negative test: Signature verification fails with altered attestation_tbs or signature")
        tampered_tbs = bytearray(attestation_tbs)
        tampered_tbs[-1] ^= 0xFF  # Flip last byte
        with pytest.raises(InvalidSignature):
            public_key.verify(signature_bytes, bytes(tampered_tbs), ec.ECDSA(hashes.SHA256()))

        tampered_signature = bytearray(signature_bytes)
        tampered_signature[0] ^= 0xFF  # Flip one byte of signature
        with pytest.raises(InvalidSignature):
            public_key.verify(bytes(tampered_signature), attestation_tbs, ec.ECDSA(hashes.SHA256()))

    # --- Helper Methods ---

    async def send_attestation_request(self, node_id):
        """
        Sends AttestationRequest command to DUT and returns the AttestationResponse as dict.
        You'll need to adapt extraction for your Matter test controller implementation.
        """
        # NOTE: placeholder for actual implementation with the controller
        # Replace with your cluster/command API as needed. Typically:
        # resp = await self.send_single_cmd(cmd=Clusters.OperationalCredentials.Commands.AttestationRequest(), endpoint=0)
        # For demo, raise NotImplementedError.
        raise NotImplementedError("You must implement or bind the attestation request for your test harness.")

    def get_dac_cert_from_attestation_elements(self, attestation_elements_bytes):
        """
        Parses the AttestationElements blob and extracts the DER-encoded DAC certificate.
        You'll need to parse TLV/CBOR/ASN.1 as appropriate to return the DAC certificate bytes.
        """
        # For demo: You SHOULD implement this by parsing the attestation_elements_bytes.
        # Here, raise for clarity.
        raise NotImplementedError("You must implement parsing for attestation elements to extract the DAC certificate.")

if __name__ == "__main__":
    default_matter_test_main()
```
**NOTES:**
- Review required helper implementations for `send_attestation_request` and `get_dac_cert_from_attestation_elements` (these require project-specific APIs or utilities).
- This script covers both positive and negative signature verification per the test case.
- Follows the structure and API conventions of existing project test files.
- Use Python's `cryptography` for ECDSA signature validation, matching Matter's P-256-SHA256 requirements.