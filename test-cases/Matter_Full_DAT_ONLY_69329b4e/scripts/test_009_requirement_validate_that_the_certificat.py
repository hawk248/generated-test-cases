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
Test Case: TC-CD-1.1 - Certification Declaration Signature Verification

Purpose:
    To verify that the Certification Declaration (CD) signature presented by the device is
    validated using the public key from the Connectivity Standards Alliance's Certificate Authority Certificate,
    ensuring the authenticity of the CD as per Matter specification.
"""

import pytest
from mobly import asserts

from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main, TestStep
from matter.testing.decorators import async_test_body

import logging

log = logging.getLogger(__name__)

class TestCertificationDeclarationSignature(MatterBaseTest):
    """
    [TC-CD-1.1] Certification Declaration Signature Verification
    """

    def steps_TC_CD_1_1(self):
        return [
            TestStep(1, "TH initiates secure commissioning session and sends attestation request to DUT"),
            TestStep(2, "TH extracts the Certification Declaration and its signature from DUT response"),
            TestStep(3, "TH retrieves CSA CA public key (from preloaded certificate)"),
            TestStep(4, "TH performs signature verification on Certification Declaration using the CSA CA public key, following Crypto_Verify() semantics"),
            TestStep(5, "(Negative) TH attempts verification with altered CD or invalid public key"),
        ]

    @async_test_body
    async def test_cd_signature_verification_positive(self):
        """
        Verifies that a Certification Declaration signature is valid using the CSA CA public key.
        """

        self.step(1)
        # Step 1: Initiate secure commissioning session, send attestation request to DUT
        attestation_response = await self.send_attestation_request_to_dut()
        asserts.assert_is_not_none(attestation_response, "No response from DUT during attestation.")

        self.step(2)
        # Step 2: Extract Certification Declaration and signature
        cd_bytes, cd_signature_bytes = self.extract_cd_and_sig(attestation_response)
        asserts.assert_is_not_none(cd_bytes, "Certification Declaration missing from attestation response")
        asserts.assert_is_not_none(cd_signature_bytes, "CD signature missing from attestation response")

        self.step(3)
        # Step 3: Retrieve CSA CA public key
        ca_cert_pem = self.get_csa_ca_certificate()
        asserts.assert_is_not_none(ca_cert_pem, "No CSA CA certificate available.")
        ca_pubkey = self.extract_public_key_from_pem(ca_cert_pem)
        asserts.assert_is_not_none(ca_pubkey, "Failed to extract public key from CSA CA certificate.")

        self.step(4)
        # Step 4: Verify the CD signature using the public key (Crypto_Verify)
        verified = self.verify_cms_signature(cd_bytes, cd_signature_bytes, ca_pubkey)
        asserts.assert_true(verified, "Certification Declaration signature verification using CSA CA public key failed")
        log.info("Certification Declaration signature verification PASSED (positive control)")

    @async_test_body
    async def test_cd_signature_verification_negative(self):
        """
        Verifies negative scenarios:
         - Manipulated CD fails verification.
         - Wrong public key fails verification.
        """

        self.step(1)
        attestation_response = await self.send_attestation_request_to_dut()
        cd_bytes, cd_signature_bytes = self.extract_cd_and_sig(attestation_response)
        ca_cert_pem = self.get_csa_ca_certificate()
        ca_pubkey = self.extract_public_key_from_pem(ca_cert_pem)

        self.step(5)
        # Negative 1: CD tampered
        tampered_cd_bytes = bytearray(cd_bytes)
        tampered_cd_bytes[0] ^= 0x01  # flip a bit
        verified_tampered = self.verify_cms_signature(bytes(tampered_cd_bytes), cd_signature_bytes, ca_pubkey)
        asserts.assert_false(verified_tampered, "Tampered CD should fail signature verification")

        # Negative 2: Invalid (random) public key
        wrong_pubkey = self.get_invalid_public_key()
        verified_wrong_key = self.verify_cms_signature(cd_bytes, cd_signature_bytes, wrong_pubkey)
        asserts.assert_false(verified_wrong_key, "Signature verification should fail with wrong public key")

        log.info("Certification Declaration signature verification NEGATIVE controls PASSED.")

    # --- Test Utility Methods ---
    async def send_attestation_request_to_dut(self):
        """
        Sends commissioning/attestation request to the DUT to retrieve attestation elements.
        Should return a structure or dict containing at least Certification Declaration and signature.
        """
        # Replace with actual command for your Matter SDK/test harness.
        # E.g., OperationalCredentials.AttestationRequest
        # Returns structure/dict with keys 'CD' and 'CDSignature'
        raise NotImplementedError("You must implement attestation request for your setup.")

    def extract_cd_and_sig(self, attestation_response):
        """
        Extract Certification Declaration bytes and its signature (likely CMS).
        """
        # Typical fields: attestation_response['CertificationDeclaration'], attestation_response['CDSignature']
        cd_bytes = attestation_response.get('CertificationDeclaration')
        cd_signature_bytes = attestation_response.get('CDSignature')
        return cd_bytes, cd_signature_bytes

    def get_csa_ca_certificate(self):
        """
        Return PEM encoding of the CSA CA certificate from preloaded config/test harness.
        """
        # Usually loaded from file, secret, or injected testbed resource
        # E.g., open('/path/to/csa_ca_cert.pem', 'rb').read()
        raise NotImplementedError("You must provide a method to access the CSA CA cert PEM.")

    def extract_public_key_from_pem(self, cert_pem):
        """
        Extract the public key from a PEM-encoded X.509 certificate.
        Uses cryptography or pyasn1, as preferred.
        """
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        return cert.public_key()

    def verify_cms_signature(self, data, signature, public_key):
        """
        Verifies a CMS (Cryptographic Message Syntax) signature over the given data using public_key.
        Crypto_Verify() semantics – use pyasn1/pyOpenSSL/cryptography as needed.
        Returns True on valid signature, False otherwise.
        """
        # Here’s a typical cryptography-based stub for an RSASSA/ecdsa signature.
        # Replace w/ your CMS wrapper or integrate M.O.C. CMS signature decoding as required in Matter F.1.
        try:
            from cryptography.hazmat.primitives.asymmetric import ec, padding
            from cryptography.hazmat.primitives import hashes

            # Some test harnesses may encapsulate the CMS SignedData and require extra parsing.
            # For ECDSA over SHA256:
            public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as ex:
            log.info(f"Signature verification failed: {ex}")
            return False

    def get_invalid_public_key(self):
        """
        Generates or loads an invalid public key for negative verification test.
        """
        from cryptography.hazmat.primitives.asymmetric import ec
        return ec.generate_private_key(ec.SECP256R1()).public_key()

if __name__ == "__main__":
    default_matter_test_main()
```
**NOTES:**
- Replace all `NotImplementedError` stubs to fit your testbed and Matter device/harness API. The test expects methods for: sending an attestation request to obtain a CD, loading the CSA CA certificate (PEM), and extracting fields from the attestation response.
- Make sure the CD and CD signature (CMS) are presented as raw bytes in your Python code.
- This is a pytest-compatible, mobly-asserts-based script conforming to existing styles in the connectedhomeip repo.