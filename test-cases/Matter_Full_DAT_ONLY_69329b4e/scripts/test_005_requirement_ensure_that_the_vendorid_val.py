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

import sys
from mobly import asserts

import matter.clusters as Clusters
from matter.exceptions import ChipStackError
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

from pyasn1.codec.der import decoder as der_decoder
from pyasn1.type.univ import Sequence
from pyasn1_modules import rfc2459

def extract_vendor_id_from_subject_dn(cert_der: bytes) -> int:
    """
    Extract the VendorID from the subject DN of a DER-encoded X.509 certificate.
    Assumes VendorID is encoded as a custom OID in the DN, per the Matter specification.
    Returns VendorID as integer, or raises ValueError if not found.
    """
    asn1_cert, _ = der_decoder.decode(cert_der, asn1Spec=rfc2459.Certificate())
    subject = asn1_cert["tbsCertificate"]["subject"]
    vendor_id_oid = (1, 3, 6, 1, 4, 1, 37244, 1, 1)  # Matter VendorID OID
    # Walk RDNSequence
    for rdn_set in subject:  # RDNSequence (SET OF RelativeDistinguishedName)
        for atv in rdn_set:  # SET OF AttributeTypeAndValue
            oid = tuple(atv["type"])
            if oid == vendor_id_oid:
                value = atv["value"]
                # Typically it's encoded as PrintableString or UTF8String
                if value.getTagSet() == rfc2459.PrintableString().getTagSet() or value.getTagSet() == rfc2459.UTF8String().getTagSet():
                    try:
                        return int(str(value))
                    except Exception as e:
                        raise ValueError(f"VendorID value in DN is not integer: {e}")
    raise ValueError("VendorID OID not found in subject DN.")

class TC_ATT_VENDORID_1_1(MatterBaseTest):
    """
    TC-ATT-VENDORID-1.1: Validate VendorID Consistency Between DAC and PAI

    Verifies that the VendorID value found in the subject Distinguished Name (DN) of the Device Attestation Certificate (DAC)
    matches the VendorID value found in the subject DN of the Product Attestation Intermediate (PAI) certificate.
    Reference: Matter v1.6 Section 6.5 Attestation PKI
    """

    @async_test_body
    async def test_vendor_id_match_between_dac_and_pai(self):
        # ---- Step 1: Initiate commissioning to trigger attestation from the DUT ----
        self.print_step(1, "TH initiates commissioning to trigger attestation from the DUT")
        attestation_elements = await self.default_controller.GetAttestationElements(self.dut_node_id)
        # attestation_elements typically contains DAC & PAI certificates as DER-encoded X.509
        dac_cert_der = attestation_elements['dac_cert']   # expected key: 'dac_cert', adjust if something different
        pai_cert_der = attestation_elements['pai_cert']   # expected key: 'pai_cert'
        asserts.assert_is_not_none(dac_cert_der, "DAC certificate not present in attestation elements")
        asserts.assert_is_not_none(pai_cert_der, "PAI certificate not present in attestation elements")

        # ---- Step 2: Extract the subject DN from both the DAC and PAI certificates ----
        self.print_step(2, "TH extracts the subject DN from both the DAC and PAI certificates and parses VendorID values")
        try:
            vendor_id_dac = extract_vendor_id_from_subject_dn(dac_cert_der)
        except Exception as e:
            asserts.fail(f"Failed to extract VendorID from DAC subject DN: {e}")

        try:
            vendor_id_pai = extract_vendor_id_from_subject_dn(pai_cert_der)
        except Exception as e:
            asserts.fail(f"Failed to extract VendorID from PAI subject DN: {e}")

        # ---- Step 3: Compare the VendorID value in the subject DN of the DAC against that in the PAI ----
        self.print_step(3, f"TH compares VendorID of DAC ({vendor_id_dac}) to PAI ({vendor_id_pai})")
        asserts.assert_equal(
            vendor_id_dac,
            vendor_id_pai,
            f"VendorID mismatch: DAC ({vendor_id_dac}) != PAI ({vendor_id_pai})"
        )

        # ---- Step 4: Log pass/fail based on the comparison ----
        self.print_step(4, "TH logs a pass if VendorID values match, fail otherwise")
        # Mobly asserts provide pass/fail outcome

if __name__ == "__main__":
    default_matter_test_main()
```