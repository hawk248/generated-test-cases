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

# Test Case: TC-JFDS-1.1
# Title: Joint Fabric Access Control Change Propagation

import logging

from mobly import asserts

import matter.clusters as Clusters
from matter.interaction_model import Status
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

log = logging.getLogger(__name__)

class TC_JFDS_1_1(MatterBaseTest):
    """
    [TC-JFDS-1.1] Joint Fabric Access Control Change Propagation

    Validates that access control updates are first made in the Datastore,
    status is marked 'pending' for impacted nodes, and update is only
    applied to node after propagation by the Datastore (status: committed).
    """

    @async_test_body
    async def test_access_control_change_propagation(self):
        # Preparation/Setup
        self.print_step(0, "Commission DUT (Datastore), TH (test harness), and Node X to the same Joint Fabric")
        # Assume commissioning done in environment setup.
        # Query initial access control on DUT and Node X.
        original_acl = await self.read_single_attribute_check_success(
            cluster=Clusters.AccessControl,
            attribute=Clusters.AccessControl.Attributes.Acl,
            endpoint=0,
            dev_ctrl=self.default_controller
        )
        log.info(f"Original ACL on DUT: {original_acl}")

        # Step 1
        self.print_step(1, "TH submits an access control configuration change to the Datastore for Node X (e.g., add group or ACL entry)")
        changed_acl = original_acl.copy()
        # For the purposes of the example, simply add a new (dummy) view entry for Node X
        # NOTE: Update this logic to match the format used in your ACL entries
        # Here we assume Node X has a test_node_id (e.g., 0x123456789abcdef).
        NODE_X_ID = self.matter_test_config.global_test_params['NODE_X_ID']
        view_entry = {
            "privilege": 1,  # View privilege
            "auth_mode": 2,  # CASE
            "subjects": [NODE_X_ID],  # List of subject node ids
            "targets": [],
            "fabricIndex": 1  # Use your test fabric index as appropriate
        }
        changed_acl.append(view_entry)
        # Send change via Datastore interface (likely via WriteAttribute)
        write_result = await self.default_controller.WriteAttribute(
            self.dut_node_id,
            [
                (0, Clusters.AccessControl.Attributes.Acl(changed_acl))
            ]
        )
        asserts.assert_equal(write_result[0].Status, Status.Success, "ACL write to Datastore failed")

        # Step 2
        self.print_step(2, "TH queries Datastore for configuration and per-node status")
        # Assume per-node config status available under a (provisional) attribute:
        # Clusters.DatastoreCluster.Attributes.NodeConfigStatus (fabric-specific, pseudo-code below)
        node_config_status = await self.default_controller.ReadAttribute(
            self.dut_node_id,
            [
                (0, ("DatastoreCluster", "NodeConfigStatus"))  # Replace with actual attribute reference
            ]
        )
        # Find Node X entry:
        node_x_status = next(
            (s for s in node_config_status[0].value if s.get("nodeId") == NODE_X_ID), None
        )
        asserts.assert_is_not_none(node_x_status, "No per-node config status for Node X in Datastore after change")
        asserts.assert_equal(
            node_x_status["status"], "pending",
            f"Expected Node X status to be 'pending', found '{node_x_status['status']}'"
        )
        new_acl = await self.read_single_attribute_check_success(
            cluster=Clusters.AccessControl,
            attribute=Clusters.AccessControl.Attributes.Acl,
            endpoint=0,
            dev_ctrl=self.default_controller
        )
        asserts.assert_true(any(
            e for e in new_acl if e.get("subjects") == [NODE_X_ID]), "Datastore ACL does not include new entry for Node X")

        # Step 3
        self.print_step(3, "Datastore propagates configuration change to Node X (triggers update)")
        # Simulate waiting for propagation; in a real system we may poll, subscribe, or listen for an event.
        # For test: poll Node X config until update arrives or timeout.
        max_wait = 10
        for i in range(max_wait):
            node_x_acl = await self.read_single_attribute_check_success(
                cluster=Clusters.AccessControl,
                attribute=Clusters.AccessControl.Attributes.Acl,
                endpoint=0,
                dev_ctrl=self.get_node_controller(NODE_X_ID)
            )
            if any(e for e in node_x_acl if e.get("subjects") == [NODE_X_ID]):
                break
            await self.async_sleep(1)
        else:
            asserts.fail(f"Configuration change never appeared on Node X after {max_wait} seconds")

        # Step 4
        self.print_step(4, "Datastore verifies Node X has updated, then transitions Node X status to 'committed'")
        node_config_status = await self.default_controller.ReadAttribute(
            self.dut_node_id,
            [
                (0, ("DatastoreCluster", "NodeConfigStatus"))
            ]
        )
        node_x_status = next(
            (s for s in node_config_status[0].value if s.get("nodeId") == NODE_X_ID), None
        )
        asserts.assert_is_not_none(node_x_status, "No per-node config status for Node X (after propagation)")
        asserts.assert_equal(
            node_x_status["status"], "committed",
            f"Expected Node X status to be 'committed', found '{node_x_status['status']}'"
        )

        # Step 5
        self.print_step(5, "TH verifies change was not directly applied to Node X prior to appearing in Datastore (before 'pending')")
        # (Note: in actual system, would need event log or query to validate this strictly.)

if __name__ == "__main__":
    default_matter_test_main()
```
**NOTES**:
- Substitute `DatastoreCluster` and `NodeConfigStatus` for actual cluster/object names for your implementation—they are provisional here.
- Uses global param `NODE_X_ID` for the subject; ensure this is set in `global_test_params` in the test runner config.
- Insert any custom methods (e.g., `get_node_controller()`) for node addressability if not present in your harness.
- Mobly asserts and test structure follow src/python_testing examples for Chip/Matter pytest integration.
- Step comments and print_step usage clarify which procedure portion matches which line of code.
