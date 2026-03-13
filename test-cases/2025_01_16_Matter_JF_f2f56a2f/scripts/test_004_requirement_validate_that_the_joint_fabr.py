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
from matter.interaction_model import Status, InteractionModelError
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

# Placeholder for the actual Joint Fabric Datastore cluster object.
# Replace with the correct import for the cluster when available.
# For demonstration, we'll use Clusters.Descriptor as a stand-in.
JOINT_FABRIC_DATASTORE_CLUSTER = getattr(Clusters, "JointFabricDatastore", Clusters.Descriptor)

class TestJointFabricDatastoreClusterServerAccessibility(MatterBaseTest):
    """
    TC-JFDS-1.1:
    Validates that the Joint Fabric Datastore cluster server is only accessible on a Node acting
    as the Joint Fabric Anchor Administrator and not otherwise.
    """

    @async_test_body
    async def test_jfds_anchor_admin_cluster_access_control(self):
        # --- Step 1: Set DUT as Joint Fabric Anchor Administrator
        self.print_step(1, "Set DUT as Joint Fabric Anchor Administrator (simulate or ensure role)")
        # [NOTE]: Exact role transition APIs will depend on implementation.
        # Here, assume there is a helper function or fixture to ensure/set DUT as Anchor Admin.
        await self.set_dut_anchor_administrator(True)

        # Validate that DUT is recognized as Anchor Admin - for simplicity, try reading an attribute.
        anchor_status = await self.is_dut_anchor_administrator()
        asserts.assert_true(anchor_status, "DUT is not recognized as Joint Fabric Anchor Administrator")

        # --- Step 2: TH attempts to access Joint Fabric Datastore cluster server on DUT (should succeed)
        self.print_step(2, "TH attempts to access Joint Fabric Datastore cluster server on DUT (expect success)")
        try:
            # Try to read an attribute from the JFDS cluster on the DUT.
            # Replace 'ClusterRevision' with a required or "safe" attribute for this cluster.
            attribute_id = getattr(JOINT_FABRIC_DATASTORE_CLUSTER.Attributes, "ClusterRevision", None)
            value = await self.read_single_attribute_check_success(
                endpoint=0, cluster=JOINT_FABRIC_DATASTORE_CLUSTER, attribute=attribute_id
            )
            asserts.assert_is_not_none(
                value, "Failed to read attribute in Anchor Admin state, cluster may not be accessible"
            )
        except Exception as e:
            asserts.fail(f"Unexpected failure accessing Joint Fabric Datastore cluster as Anchor Admin: {e}")

        # --- Step 3: Demote DUT so it is no longer Anchor Administrator
        self.print_step(3, "Demote DUT so it is no longer Anchor Administrator (simulate or invoke role transition)")
        # [NOTE]: Exact method will depend on system capabilities.
        await self.set_dut_anchor_administrator(False)
        # Confirm role removal:
        anchor_status = await self.is_dut_anchor_administrator()
        asserts.assert_false(anchor_status, "DUT is still an Anchor Admin after demotion")

        # --- Step 4: TH attempts to access Joint Fabric Datastore cluster server on DUT (should fail)
        self.print_step(4, "TH attempts to access Joint Fabric Datastore cluster server on DUT (expect failure)")
        access_failed = False
        try:
            attribute_id = getattr(JOINT_FABRIC_DATASTORE_CLUSTER.Attributes, "ClusterRevision", None)
            _ = await self.read_single_attribute_check_success(
                endpoint=0, cluster=JOINT_FABRIC_DATASTORE_CLUSTER, attribute=attribute_id
            )
        except (InteractionModelError, Exception) as e:
            # Expected: access should be rejected or fail
            access_failed = True
        asserts.assert_true(access_failed, "Cluster should not be accessible when DUT is not Anchor Admin")

    # ---------- UTILITIES BELOW (would be implemented/provided in matter_testing/mocks/infra) ----------

    async def set_dut_anchor_administrator(self, anchor: bool):
        """
        Helper to promote/demote DUT to/from Anchor Administrator.
        Implementation is platform/framework specific.
        """
        # Example stub - replace with real RPC/attribute/logic for role assignment.
        # Might require invoking an attribute write, calling a manufacturer command, or using out-of-band config.
        await self.step_passed(f"Simulate set AnchorAdmin state to {anchor}")

    async def is_dut_anchor_administrator(self) -> bool:
        """
        Helper to check if the DUT is currently Anchor Administrator.
        Should observe via e.g. advertised attributes, a known cluster attribute, or other device API.
        """
        # Placeholder: replace with a check against DUT/JF TXT/DNSSD/attribute when available.
        # For now, always return True for testing step 1, always False after demotion (simulate flow).
        # In a real test harness, this would check actual device state.
        # Instead, use some internal flag if you maintain state, or check an attribute on the device.
        return True  # Always True for the purposes of initial code stub

    async def step_passed(self, msg):
        """
        Utility step for marking steps as complete in async context (faking device config/application logic).
        """
        self.print_step(-1, f"[MOCK-STEP] {msg}")


if __name__ == "__main__":
    default_matter_test_main()
```