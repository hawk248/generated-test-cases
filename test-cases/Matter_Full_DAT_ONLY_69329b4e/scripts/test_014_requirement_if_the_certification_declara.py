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

# === BEGIN CI TEST ARGUMENTS ===
# test-runner-runs:
#   run1:
#     app: ${ALL_CLUSTERS_APP}
#     factory-reset: true
#     quiet: true
#     app-args: --discriminator 1234 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 1234
#       --passcode 20202021
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
# === END CI TEST ARGUMENTS ===

import logging

import pytest
from mobly import asserts

from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main
from matter.testing.decorators import async_test_body

import matter.clusters as Clusters

from cryptography import x509
from cryptography.hazmat.backends import default_backend

log = logging.getLogger(__name__)

class TC_CD_2_1_AuthorizedPAAList(MatterBaseTest):
    """
    TC-CD-2.1: Validate authorized_paa_list Field Contains PAA SKI

    Verifies that when the Certification Declaration contains the authorized_paa_list field,
    the Subject Key Identifier (SKI) extension value of the Product Attestation Authority (PAA)
    certificate is present in the list.
    """

    @async_test_body
    async def test_cd_authorized_paa_list_positive(self):
        # Step 1: Retrieve Certification Declaration from DUT and parse authorized_paa_list
        self.print_step(1, "TH retrieves Certification Declaration from DUT and parses authorized_paa_list")
        cert_decl = await self.get_certification_declaration_from_dut(self.dut_node_id)
        asserts.assert_is_not_none(cert_decl, "Failed to retrieve Certification Declaration from DUT")
        authorized_paa_list = self.extract_authorized_paa_list(cert_decl)
        asserts.assert_is_not_none(authorized_paa_list, "authorized_paa_list missing in Certification Declaration")
        asserts.assert_true(
            isinstance(authorized_paa_list, list) and authorized_paa_list,
            f"authorized_paa_list is not a non-empty list: {authorized_paa_list}"
        )

        # Step 2: Retrieve PAA cert from DUT's attestation chain and extract SKI
        self.print_step(2, "TH retrieves PAA certificate from DUT’s attestation chain and extracts SKI extension value")
        paa_cert_der = await self.get_paa_cert_from_dut_chain(self.dut_node_id)
        asserts.assert_is_not_none(paa_cert_der, "PAA DER certificate not retrieved from DUT")
        paa_ski = self.extract_subject_key_identifier(paa_cert_der)
        asserts.assert_is_not_none(paa_ski, "Could not extract SKI from PAA certificate")

        # Step 3: Check if PAA SKI value is present in authorized_paa_list from CD
        self.print_step(3, "TH checks if PAA SKI value is present in authorized_paa_list from CD")
        found = paa_ski in authorized_paa_list
        asserts.assert_true(
            found,
            f"SKI '{paa_ski}' (from PAA cert) is not present in authorized_paa_list of Certification Declaration"
        )

        # Step 4: Log pass if SKI is found in list; fail otherwise
        self.print_step(4, "Test result: PASS if SKI is found in authorized_paa_list; FAIL otherwise")

    @async_test_body
    async def test_cd_authorized_paa_list_negative(self):
        # Negative test: Use CD where the SKI is NOT present
        self.print_step(1, "Negative path: Use CD where PAA SKI is NOT present in authorized_paa_list")
        cert_decl = await self.get_certification_declaration_from_dut(self.dut_node_id, negative=True)
        asserts.assert_is_not_none(cert_decl, "Certification Declaration not retrieved in negative path")
        authorized_paa_list = self.extract_authorized_paa_list(cert_decl)
        asserts.assert_is_not_none(authorized_paa_list, "authorized_paa_list missing for negative variant")

        paa_cert_der = await self.get_paa_cert_from_dut_chain(self.dut_node_id)
        paa_ski = self.extract_subject_key_identifier(paa_cert_der)
        assert paa_ski not in authorized_paa_list, (
            f"Negative test expected SKI '{paa_ski}' NOT in authorized_paa_list, but found present."
        )

    # --- Test Utility Methods ---

    async def get_certification_declaration_from_dut(self, node_id, negative=False):
        """
        Retrieve the Certification Declaration from the DUT.
        Implementers: replace this with the appropriate attribute/command for your controller.
        If negative=True, inject or request a CD deliberately missing the correct SKI.
        """
        raise NotImplementedError("Implement Certification Declaration retrieval for DUT")

    def extract_authorized_paa_list(self, cert_decl_blob):
        """
        Extracts the authorized_paa_list field from the Certification Declaration.
        This should parse the CD structure (TLV, ASN.1, CBOR, JSON, etc.) and return a list of SKI hex strings.
        """
        # Example: If cert_decl_blob is a parsed dict:
        # return cert_decl_blob.get('authorized_paa_list', None)
        raise NotImplementedError("Implement authorized_paa_list extraction from Certification Declaration structure")

    async def get_paa_cert_from_dut_chain(self, node_id):
        """
        Retrieve the DER-encoded PAA certificate from the DUT.
        This could be by requesting attestation chain or via an API.
        """
        raise NotImplementedError("Implement DER retrieval of PAA cert from device-under-test chain")

    def extract_subject_key_identifier(self, cert_der):
        """
        Extract the Subject Key Identifier (SKI) Extension value from a DER-encoded X.509 certificate.
        Returns as a hex string.
        """
        cert = x509.load_der_x509_certificate(cert_der, default_backend())
        try:
            ski_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_KEY_IDENTIFIER)
            # SKI is bytes, typically expressed in hex
            return ski_ext.value.digest.hex()
        except Exception as ex:
            log.error(f"SKI extension not found in PAA certificate: {ex}")
            return None

if __name__ == "__main__":
    default_matter_test_main()
```
