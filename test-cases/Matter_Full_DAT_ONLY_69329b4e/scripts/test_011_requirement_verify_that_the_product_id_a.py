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

from mobly import asserts

import matter.clusters as Clusters
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

log = logging.getLogger(__name__)

class TC_CD_2_1_ProductIDList(MatterBaseTest):
    """
    TC-CD-2.1: Certification Declaration ProductID List Matches Basic Information ProductID

    Verifies that the product_id_array field in the Certification Declaration contains
    the ProductID attribute found in the Basic Information cluster.
    """

    @async_test_body
    async def test_cd_productid_in_array(self):
        # STEP 0: Commissioning or operational check
        self.print_step(0, "Commissioning - ensure both DUT and TH are powered on, networked")

        # STEP 1: Retrieve Certification Declaration from DUT and extract product_id_array
        self.print_step(1, "TH retrieves the Certification Declaration from DUT and parses product_id_array field")
        cert_decl = await self.get_certification_declaration_from_dut(self.dut_node_id)
        asserts.assert_is_not_none(cert_decl, "Failed to retrieve Certification Declaration from DUT")
        product_id_array = self.extract_product_id_array_from_cd(cert_decl)
        asserts.assert_is_not_none(product_id_array, "product_id_array field not found or not parsed from Certification Declaration")
        asserts.assert_true(isinstance(product_id_array, list), "product_id_array field must be a list")
        log.info(f"ProductID array from CD: {product_id_array}")

        # STEP 2: Read ProductID from Basic Information cluster
        self.print_step(2, "TH reads the ProductID attribute from DUT's Basic Information cluster")
        basic_info_product_id = await self.read_single_attribute_check_success(
            cluster=Clusters.BasicInformation,
            attribute=Clusters.BasicInformation.Attributes.ProductID,
        )
        asserts.assert_is_not_none(basic_info_product_id, "Failed to read ProductID attribute from Basic Information cluster")
        log.info(f"ProductID from Basic Information cluster: {basic_info_product_id}")

        # STEP 3: Check if ProductID is in product_id_array
        self.print_step(3, "TH checks if ProductID from BasicInfo is present in product_id_array of Certification Declaration")
        asserts.assert_in(
            int(basic_info_product_id),
            [int(pid) for pid in product_id_array],
            f"ProductID {basic_info_product_id} from BasicInformation cluster is not present in product_id_array of Certification Declaration"
        )

        # STEP 4: Log pass
        self.print_step(4, "Test PASSED: ProductID from Basic Info cluster is included in CD's product_id_array")

    # Negative scenario
    @async_test_body
    async def test_cd_productid_not_in_array_negative(self):
        # This test expects a DUT/CD setup where the product_id_array omits the valid ProductID value.
        self.print_step(0, "Commissioning - negative: setup with CD missing actual ProductID in product_id_array")

        cert_decl = await self.get_certification_declaration_from_dut(self.dut_node_id)
        asserts.assert_is_not_none(cert_decl, "Failed to retrieve Certification Declaration from DUT")
        product_id_array = self.extract_product_id_array_from_cd(cert_decl)
        asserts.assert_is_not_none(product_id_array, "product_id_array field not found in Certification Declaration")
        asserts.assert_true(isinstance(product_id_array, list), "product_id_array field must be a list")

        basic_info_product_id = await self.read_single_attribute_check_success(
            cluster=Clusters.BasicInformation,
            attribute=Clusters.BasicInformation.Attributes.ProductID,
        )
        asserts.assert_is_not_none(basic_info_product_id, "Failed to read ProductID attribute from Basic Information cluster")

        self.print_step(1, "TH checks that ProductID is NOT present in product_id_array and expects failure")
        if int(basic_info_product_id) in [int(pid) for pid in product_id_array]:
            asserts.fail(
                f"Negative test: ProductID {basic_info_product_id} was unexpectedly found in CD's product_id_array!"
            )
        # If not found, the test passes (expected negative behavior)

    # Helpers -- these would need to be properly implemented per project constraints

    async def get_certification_declaration_from_dut(self, node_id):
        """
        Retrieve the Certification Declaration from the DUT.
        You MUST implement this to query the actual value (via attribute, command, or other API).
        """
        # Example (update to match your actual interface):
        # result = await self.read_single_attribute_check_success(
        #     cluster=Clusters.OperationalCredentials,
        #     attribute=Clusters.OperationalCredentials.Attributes.CertificationDeclaration,
        # )
        # return result
        raise NotImplementedError("Implement retrieval of Certification Declaration for your harness/DUT.")

    def extract_product_id_array_from_cd(self, cert_decl_blob):
        """
        Parses the Certification Declaration blob and extracts the product_id_array field.
        This MUST be implemented to decode according to your data format (CBOR, TLV, ASN.1, dict, etc).
        """
        # Example stub: If it's a decoded dict, just pull out 'product_id_array'
        # return cert_decl_blob.get('product_id_array', None)
        raise NotImplementedError("Implement logic to extract product_id_array from Certification Declaration blob.")

if __name__ == "__main__":
    default_matter_test_main()
```
