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

from mobly import asserts
import matter.clusters as Clusters
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

# pyasn1 for X.509 parsing (VendorID is a custom OID in the DN)
from pyasn1.codec.der import decoder as der_decoder
from pyasn1_modules import rfc2459

def extract_vendor_id_from_subject_dn(cert_der: bytes):
    """
    Extract the VendorID from the subject DN of a DER-encoded X.509 certificate.
    Matter VendorID: OID 1.3.6.1.4.1.37244.1.1 (see Matter specification)
    Returns int value or None if not found.
    """
    vendor_oid = (1, 3, 6, 1, 4, 1, 37244, 1, 1)
    asn1_cert, _ = der_decoder.decode(cert_der, asn1Spec=rfc2459.Certificate())
    subject = asn1_cert['tbsCertificate']['subject']
    for rdn_set in subject:  # RDNSequence is a SET OF RelativeDistinguishedName
        for atv in rdn_set:  # RelativeDistinguishedName is a SET OF AttributeTypeAndValue
            oid = tuple(atv["type"])
            if oid == vendor_oid:
                value = atv["value"]
                # Should be a string representation of the integer VendorID
                try:
                    return int(str(value))
                except Exception as e:
                    # Could log here if desired
                    return None
    # Not present
    return None

class TestPAAPAIvendorID(MatterBaseTest):
    """[TC-ATT-6.1] PAA and PAI VendorID Match Verification"""

    @async_test_body
    async def test_paa_and_pai_vendorid_match(self):
        # --- Step 1: Extract certificates from DUT ---
        self.print_step(1, "TH extracts PAA and PAI certificates from DUT")
        # You may adapt this to your actual device API/test harness environment.
        cert_chain = await self.get_attestation_cert_chain()
        paa_cert_der = cert_chain['paa']
        pai_cert_der = cert_chain['pai']
        asserts.assert_is_not_none(paa_cert_der, "PAA certificate not retrieved.")
        asserts.assert_is_not_none(pai_cert_der, "PAI certificate not retrieved.")

        # --- Step 2: Extract VendorID from PAA subject DN (if present) ---
        self.print_step(2, "TH parses subject DN of PAA certificate and retrieves the VendorID (if present)")
        paa_vendorid = extract_vendor_id_from_subject_dn(paa_cert_der)
        # Step 3 is always required; presence/absence is used for logic
        self.print_step(3, "TH parses subject DN of PAI certificate and retrieves the VendorID")
        pai_vendorid = extract_vendor_id_from_subject_dn(pai_cert_der)
        asserts.assert_is_not_none(pai_vendorid, "VendorID not present in PAI certificate subject DN.")

        # --- Step 4: Compare if VendorID present in PAA ---
        if paa_vendorid is not None:
            self.print_step(4, "VendorID found in PAA: comparing PAA/PAI VendorID values")
            asserts.assert_equal(
                paa_vendorid, pai_vendorid,
                f"VendorID in PAA ({paa_vendorid}) does not match VendorID in PAI ({pai_vendorid})"
            )
        else:
            # --- Step 5: If no VendorID in PAA, skip comparison ---
            self.print_step(5, "VendorID not present in PAA subject DN; skipping comparison as per test requirements")
            asserts.assert_true(True, "Test passes when VendorID is not present in PAA")

    async def get_attestation_cert_chain(self):
        """
        Retrieve attestation certificate chain from device under test.
        Returns a dictionary with 'paa' and 'pai' (DER-encoded).
        This is a placeholder: implement based on your actual test harness API.
        """
        # Example (you must replace this with your actual retrieval code):
        # Let's pretend self.default_controller.GetAttestationElements returns a dict with 'paa_cert', 'pai_cert'
        attestation_elements = await self.default_controller.GetAttestationElements(self.dut_node_id)
        paa_cert_der = attestation_elements.get('paa_cert', None)
        pai_cert_der = attestation_elements.get('pai_cert', None)
        return {'paa': paa_cert_der, 'pai': pai_cert_der}

if __name__ == "__main__":
    default_matter_test_main()
```