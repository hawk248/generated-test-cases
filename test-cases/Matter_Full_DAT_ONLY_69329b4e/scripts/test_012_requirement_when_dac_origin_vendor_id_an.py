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
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main
from matter.testing.decorators import async_test_body

from pyasn1.codec.der import decoder as der_decoder
from pyasn1_modules import rfc2459

def extract_field_from_dn(cert_der: bytes, oid_tuple):
    """Extract integer-encoded field (VendorID/ProductID) from subject DN based on OID tuple."""
    asn1_cert, _ = der_decoder.decode(cert_der, asn1Spec=rfc2459.Certificate())
    subject = asn1_cert['tbsCertificate']['subject']
    for rdn_set in subject:
        for atv in rdn_set:
            oid = tuple(atv['type'])
            if oid == oid_tuple:
                value = atv['value']
                try:
                    return int(str(value))
                except Exception as e:
                    return None
    return None

class TestCDDACPAIMatch(MatterBaseTest):
    """
    TC-CD-2.1: Validate dac_origin_vendor_id and dac_origin_product_id Matching in Certification Declaration
    Verifies (per Matter 1.6, Section 6.5, F.5) that when both fields are present in the Certification Declaration,
    the VendorID and ProductID values in the subject DNs of the DAC and PAI match those declared.
    """

    # OIDs as per Matter spec (see https://github.com/CHIP-Specifications/chip-certificates)
    OID_VENDOR_ID = (1, 3, 6, 1, 4, 1, 37244, 1, 1)
    OID_PRODUCT_ID = (1, 3, 6, 1, 4, 1, 37244, 1, 2)

    @async_test_body
    async def test_cd_dacpai_match(self):
        self.print_step(1, "TH retrieves Certification Declaration, DAC, and PAI from DUT")
        cd, dac_der, pai_der = await self.get_cd_and_dac_pai_from_dut()
        asserts.assert_is_not_none(cd, "Certification Declaration not retrieved")
        asserts.assert_is_not_none(dac_der, "DAC certificate not retrieved")
        asserts.assert_is_not_none(pai_der, "PAI certificate not retrieved")

        self.print_step(2, "TH parses dac_origin_vendor_id and dac_origin_product_id from CD")
        dac_origin_vendor_id, dac_origin_product_id = self.extract_origin_vid_pid_from_cd(cd)
        asserts.assert_is_not_none(dac_origin_vendor_id, "dac_origin_vendor_id not present in CD")
        asserts.assert_is_not_none(dac_origin_product_id, "dac_origin_product_id not present in CD")

        self.print_step(3, "TH parses VendorID and ProductID from DAC and PAI subject DNs")
        dac_vendor_id = extract_field_from_dn(dac_der, self.OID_VENDOR_ID)
        dac_product_id = extract_field_from_dn(dac_der, self.OID_PRODUCT_ID)
        pai_vendor_id = extract_field_from_dn(pai_der, self.OID_VENDOR_ID)
        pai_product_id = extract_field_from_dn(pai_der, self.OID_PRODUCT_ID)
        asserts.assert_is_not_none(dac_vendor_id, "VendorID missing in DAC subject DN")
        asserts.assert_is_not_none(dac_product_id, "ProductID missing in DAC subject DN")
        asserts.assert_is_not_none(pai_vendor_id, "VendorID missing in PAI subject DN")

        self.print_step(4, "TH verifies VendorID in DAC subject DN matches dac_origin_vendor_id from CD")
        asserts.assert_equal(
            dac_vendor_id, dac_origin_vendor_id,
            f"DAC VendorID ({dac_vendor_id}) does not match CD dac_origin_vendor_id ({dac_origin_vendor_id})"
        )
        self.print_step(5, "TH verifies VendorID in PAI subject DN matches dac_origin_vendor_id from CD")
        asserts.assert_equal(
            pai_vendor_id, dac_origin_vendor_id,
            f"PAI VendorID ({pai_vendor_id}) does not match CD dac_origin_vendor_id ({dac_origin_vendor_id})"
        )
        self.print_step(6, "TH verifies ProductID in DAC subject DN matches dac_origin_product_id from CD")
        asserts.assert_equal(
            dac_product_id, dac_origin_product_id,
            f"DAC ProductID ({dac_product_id}) does not match CD dac_origin_product_id ({dac_origin_product_id})"
        )

        self.print_step(7, "If PAI has ProductID, verify it matches dac_origin_product_id from CD")
        if pai_product_id is not None:
            asserts.assert_equal(
                pai_product_id, dac_origin_product_id,
                f"PAI ProductID ({pai_product_id}) does not match CD dac_origin_product_id ({dac_origin_product_id})"
            )
        else:
            self.print_step(7.5, "PAI ProductID field not present; skipping check as allowed by the spec.")

        self.print_step(8, "Test passes only if all required pairs match exactly")

    # --- Helpers: To be implemented for actual project/harness integration

    async def get_cd_and_dac_pai_from_dut(self):
        """
        Retrieve the Certification Declaration (CD) and DER-encoded DAC and PAI certificates from DUT.
        Returns: (CD, dac_der, pai_der)
        THIS MUST be implemented as per your controller/harness.
        """
        # Placeholders for project integration:
        # Replace with real calls to fetch these from the DUT (likely via OperationalCredentials attributes/commands)
        raise NotImplementedError("Implement retrieval of Certification Declaration, DAC DER, and PAI DER from DUT")

    def extract_origin_vid_pid_from_cd(self, certification_declaration):
        """
        Parses the Certification Declaration to extract dac_origin_vendor_id and dac_origin_product_id fields.
        Format might be CBOR, TLV, or ASN.1, depending on your ecosystem.
        Placeholder returns (None, None) until implemented.
        """
        # Implement this based on your encoding of the CD (parsing CBOR/TLV/ASN.1 as needed).
        # Example:
        # return certification_declaration['dac_origin_vendor_id'], certification_declaration['dac_origin_product_id']
        raise NotImplementedError("Implement decoder for Certification Declaration structure")

if __name__ == "__main__":
    default_matter_test_main()
```
**NOTES:**
- Implement the two helpers (`get_cd_and_dac_pai_from_dut()` and `extract_origin_vid_pid_from_cd()`) per your controller/harness API and CD encoding.
- This script provides explicit log steps, field-by-field assertions, and follows both the style and structure of example tests from the CHIP repo.
- Add handling for negative/mismatch cases in your test vectors/environment to trigger failures as needed.