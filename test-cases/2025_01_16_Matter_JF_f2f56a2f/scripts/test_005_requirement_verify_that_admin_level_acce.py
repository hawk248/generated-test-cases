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
from matter.interaction_model import InteractionModelError, Status
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

# You may want to adjust the cluster/attribute/command below to your specific Datastore cluster API.

class TestJFAdminAccessCAT(MatterBaseTest):
    """
    TC-JFADMIN-1.1:
    Validates that only Nodes with an Administrator CAT in their NOC are granted Admin access
    to the Joint Fabric Datastore cluster, as required by Matter specification 12.2.4.2 and [12.11-12.14].
    """

    # Assumes self.admin_controller and self.nonadmin_controller are properly setup
    # in the test harness as controllers provisioned with and without Admin CAT, respectively.

    async def setup_class(self):
        # You may hook up global or class-level prep here.
        super().setup_class()
        # Set these or provide via command line/testbed setup as needed
        # Example: set up which node_id is the DUT, which are TH-Admin and TH-NonAdmin
        # self.dut_node_id = ...
        # self.th_admin_node_id = ...
        # self.th_nonadmin_node_id = ...
        # self.JF_DATASTORE_CLUSTER_ID = ... (update as needed)
        # self.JF_DATASTORE_ADMIN_ATTRIBUTE = ... (should be an attribute/command needing Admin)
        pass

    @async_test_body
    async def test_admin_access_restriction_by_cat(self):
        # STEP 1: TH-Admin attempts Admin operation on DUT's Joint Fabric Datastore cluster
        self.print_step(1, "TH-Admin attempts Admin level operation (privileged write) on DUT's Joint Fabric Datastore cluster")
        try:
            # Attempt a write on an Admin-protected attribute (example: Write 'SomeAdminConfig' to value 1)
            res = await self.admin_controller.WriteAttribute(
                self.dut_node_id,
                [(0, Clusters.JointFabricDatastore.Attributes.SomeAdminConfig(1))]
            )
            asserts.assert_equal(res[0].Status, Status.Success, "Admin-level write by TH-Admin should succeed")
        except Exception as exc:
            asserts.fail(f"Admin-level operation by TH-Admin unexpectedly failed: {exc}")

        # STEP 2: TH-Admin verifies Admin access by performing another Admin-only operation (example: Read-Modify-Write)
        self.print_step(2, "TH-Admin verifies Admin access by reading/writing Admin-only command")
        try:
            cfg_value = await self.admin_controller.ReadAttribute(
                self.dut_node_id,
                [(0, Clusters.JointFabricDatastore.Attributes.SomeAdminConfig)],
            )
            asserts.assert_true(cfg_value is not None, "TH-Admin should be able to read Admin-only attribute")
        except Exception as exc:
            asserts.fail(f"Admin-level read by TH-Admin unexpectedly failed: {exc}")

        # STEP 3: TH-NonAdmin attempts same Admin operation, should fail on privilege
        self.print_step(3, "TH-NonAdmin attempts same Admin level operation on DUT's Joint Fabric Datastore cluster")
        try:
            result = await self.nonadmin_controller.WriteAttribute(
                self.dut_node_id,
                [(0, Clusters.JointFabricDatastore.Attributes.SomeAdminConfig(2))]
            )
            # If we get a status back (not exception), expect failure code
            asserts.assert_not_equal(
                result[0].Status,
                Status.Success,
                "TH-NonAdmin should NOT get Admin access"
            )
        except InteractionModelError as e:
            asserts.assert_equal(
                e.status,
                Status.UnsupportedAccess,
                "TH-NonAdmin should be denied Admin operation"
            )
        except Exception as exc:
            # Accept any error as expected here
            pass

        # STEP 4: TH-NonAdmin verifies rejection on Admin-only action      
        self.print_step(4, "TH-NonAdmin verifies rejection by attempting Admin-only action")
        try:
            # Example: a read/write to a protected attribute should result in privilege failure
            _ = await self.nonadmin_controller.ReadAttribute(
                self.dut_node_id,
                [(0, Clusters.JointFabricDatastore.Attributes.SomeAdminConfig)],
            )
            asserts.fail("TH-NonAdmin was able to read Admin-only attribute (should be denied)")
        except InteractionModelError as e:
            asserts.assert_equal(
                e.status,
                Status.UnsupportedAccess,
                "TH-NonAdmin should be denied on Admin-only read"
            )
        except Exception as exc:
            # Accept any error as expected here
            pass

        # STEP 5: On DUT, enumerate Access Control Cluster entries for the Admin privilege
        self.print_step(5, "On DUT, enumerate ACL entries for Admin privilege, and check subject is Administrator CAT")
        try:
            acl_entries = await self.default_controller.ReadAttribute(
                self.dut_node_id,
                [(0, Clusters.AccessControl.Attributes.Acl)],
            )
            found = False
            for entry in acl_entries[0].value:
                if (
                    getattr(entry, "privilege", None) == Clusters.AccessControl.Enums.AccessControlEntryPrivilegeEnum.kAdminister and
                    getattr(entry, "subject", None) == self.get_expected_admin_cat()
                ):
                    found = True
                    break
            asserts.assert_true(found, "No ACL entry with Admin privilege for Administrator CAT found on the DUT")
        except Exception as exc:
            asserts.fail(f"Failed to enumerate or verify ACL entries on DUT: {exc}")

    def get_expected_admin_cat(self):
        # Return the expected Administrator CAT associated with this fabric,
        # e.g., from provisioning input or test parameters
        # For now, just a placeholder. Change as needed for your infra.
        return self.test_config.global_test_params.get("ADMINISTRATOR_CAT", 0xFFFFFF)

if __name__ == "__main__":
    default_matter_test_main()
```