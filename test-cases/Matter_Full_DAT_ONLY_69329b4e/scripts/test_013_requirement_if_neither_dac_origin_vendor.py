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

from mobly import asserts
import matter.clusters as Clusters
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main
from matter.testing.decorators import async_test_body

from pyasn1.codec.der import decoder as der_decoder
from pyasn1_modules import rfc2459

def extract_from_subject_dn(cert_der: bytes, oid: tuple):
    """
    Extracts string value for the given OID from the X.509 certificate subject DN.
    Returns None if not present.
    """
    asn1_cert, _ = der_decoder.decode(cert_der, asn1Spec=rfc2459.Certificate())
    subject = asn1_cert['tbsCertificate']['subject']
    for rdn_set in subject:
        for atv in rdn_set:
            if tuple(atv['type']) == oid:
                value = atv['value']
                return str(value)
    return None

def extract_vendor_id_from_subject_dn(cert_der: bytes):
    # OID: 1.3.6.1.4.1.37244.1.1 (Matter VendorID)
    VENDORID_OID = (1, 3, 6, 1, 4, 1, 37244, 1, 1)
    value = extract_from_subject_dn(cert_der, VENDORID_OID)
    return int(value) if value is not None else None

def extract_product_id_from_subject_dn(cert_der: bytes):
    # OID: 1.3.6.1.4.1.37244.1.2 (Matter ProductID)
    PRODUCTID_OID = (1, 3, 6, 1, 4, 1, 37244, 1, 2)
    value = extract_from_subject_dn(cert_der, PRODUCTID_OID)
    return int(value) if value is not None else None

class TC_CD_2_1_VIDPIDMatch(MatterBaseTest):
    """
    [TC-CD-2.1] Validate VendorID and ProductID Matching in Certification Declaration
    (No dac_origin_* Present)
    """

    @async_test_body
    async def test_vidpid_match_without_dac_origin(self):
        # Step 1: Retrieve CD, DAC, and PAI from DUT
        self.print_step(1, "TH requests Certification Declaration, DAC, and PAI from DUT")
        cd_blob, dac_cert_der, pai_cert_der = await self.get_cd_and_certs(self.dut_node_id)
        asserts.assert_is_not_none(cd_blob, "Certification Declaration not retrieved.")
        asserts.assert_is_not_none(dac_cert_der, "DAC certificate not retrieved.")
        asserts.assert_is_not_none(pai_cert_der, "PAI certificate not retrieved.")

        # Step 2: Verify no 'dac_origin_vendor_id' or 'dac_origin_product_id' in CD
        self.print_step(2, "TH verifies neither dac_origin_vendor_id nor dac_origin_product_id is present in the CD")
        # You must properly parse the CD according to project's TLV/CBOR/ASN.1 structure
        cd = self.parse_cd(cd_blob)
        asserts.assert_true(
            'dac_origin_vendor_id' not in cd and 'dac_origin_product_id' not in cd,
            "Certification Declaration should NOT include dac_origin_vendor_id or dac_origin_product_id fields for this test"
        )

        # Step 3: Extract VendorID from DAC
        self.print_step(3, "TH extracts VendorID from DAC subject DN; compares to vendor_id in CD")
        dac_vendorid = extract_vendor_id_from_subject_dn(dac_cert_der)
        asserts.assert_is_not_none(dac_vendorid, "VendorID not found in DAC certificate subject DN.")
        asserts.assert_equal(
            dac_vendorid, int(cd["vendor_id"]),
            f"VendorID from DAC ({dac_vendorid}) != vendor_id in CD ({cd['vendor_id']})"
        )

        # Step 4: Extract VendorID from PAI
        self.print_step(4, "TH extracts VendorID from PAI subject DN; compares to vendor_id in CD")
        pai_vendorid = extract_vendor_id_from_subject_dn(pai_cert_der)
        asserts.assert_is_not_none(pai_vendorid, "VendorID not found in PAI certificate subject DN.")
        asserts.assert_equal(
            pai_vendorid, int(cd["vendor_id"]),
            f"VendorID from PAI ({pai_vendorid}) != vendor_id in CD ({cd['vendor_id']})"
        )

        # Step 5: Extract ProductID from DAC and check it's present in product_id_array in CD
        self.print_step(5, "TH extracts ProductID from DAC subject DN; verifies it is present in product_id_array in CD")
        dac_productid = extract_product_id_from_subject_dn(dac_cert_der)
        asserts.assert_is_not_none(dac_productid, "ProductID not found in DAC certificate subject DN.")
        product_id_array = cd.get('product_id_array', [])
        asserts.assert_true(
            int(dac_productid) in [int(x) for x in product_id_array],
            f"ProductID from DAC ({dac_productid}) not in CD product_id_array ({product_id_array})"
        )

        # Step 6: If ProductID present in PAI, check it's present in product_id_array in CD
        self.print_step(6, "If ProductID present in PAI subject DN, TH checks it is present in product_id_array in CD")
        pai_productid = extract_product_id_from_subject_dn(pai_cert_der)
        if pai_productid is not None:
            asserts.assert_true(
                int(pai_productid) in [int(x) for x in product_id_array],
                f"ProductID from PAI ({pai_productid}) not in CD product_id_array ({product_id_array})"
            )

    async def get_cd_and_certs(self, node_id):
        """
        Fetch Certification Declaration, DAC, and PAI certificates from DUT.
        Returns: (cd_blob, dac_cert_der, pai_cert_der)
        """
        # Placeholder: Implement according to your test harness/device APIs.
        # For example, read a specific attribute/endpoint for CD, and extract certs from attestation info.
        raise NotImplementedError("Implement device-specific CD, DAC, and PAI retrieval.")

    def parse_cd(self, cd_blob):
        """
        Parse Certification Declaration into a Python dictionary.
        This must decode the TLV/ASN.1/CBOR as per project convention.
        Must return dict with at least keys:
            vendor_id (int), product_id_array (list of int), and may include others.
        """
        # Example implementation if already deserialized dict:
        # return cd_blob if isinstance(cd_blob, dict) else decode_tlv(cd_blob)
        raise NotImplementedError("Implement parsing of Certification Declaration field(s).")

if __name__ == "__main__":
    default_matter_test_main()
```
**NOTES:**
- You must supply implementations for `get_cd_and_certs()` and `parse_cd()` based on your Matter testbed, device, or SDK.
- Certificate subject DN OIDs and extraction method follow the Matter spec; adjust OIDs if your certificates use alternative fields.
- This script validates both positive and negative (deliberate mismatch) paths if required, per test instructions.
- The test structure strictly follows the style in your project and covers each test step with assertions and print_step calls.
