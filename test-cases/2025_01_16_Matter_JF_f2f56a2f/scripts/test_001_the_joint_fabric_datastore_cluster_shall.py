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
#     app-args: --discriminator 2025 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 2025
#       --passcode 20202021
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
# === END CI TEST ARGUMENTS ===

import pytest
import logging
from typing import Dict, Any

from mobly import asserts

import matter.clusters as Clusters
from matter.interaction_model import InteractionModelError, Status
from matter.testing.decorators import async_test_body
from matter.testing.matter_testing import MatterBaseTest
from matter.testing.runner import default_matter_test_main

log = logging.getLogger(__name__)

# Test Constants (could eventually be parameterized)
DUMMY_NODE_ID = 12345
EXISTING_NODE_ID = 1001
NON_EXISTENT_NODE_ID = 9999
DUPLICATE_GROUP_ID = 2001
VALID_GROUP_ID = 3333
NON_EXISTENT_GROUP_ID = 4444
DUMMY_USER = 'invalidUser'
VALID_NODE_CONFIG = {"name": "NodeAlpha", "ip": "fd00::1"}
INVALID_NODE_CONFIG = {"name": "", "ip": "BAD_IP_ADDR"}
VALID_CREDENTIALS = {"username": "admin", "password": "correct"}
INVALID_CREDENTIALS = {"username": DUMMY_USER, "password": "wrongpass"}


class TestJointFabricDatastoreClusterManagementAndAudit(MatterBaseTest):
    """
    [TC-JFDSC-1.1] Joint Fabric Datastore Cluster Management Operations and Audit Log Verification (with edge cases)
    """

    @async_test_body
    async def test_management_and_audit_log(self):

        # Step 1: Add a new Node via UI/API
        self.print_step(1, "Add a new Node to the Joint Fabric")
        added_node_id = await self.add_node(VALID_NODE_CONFIG)
        asserts.assert_is_not_none(added_node_id)
        asserts.assert_true(await self.is_node_in_directory(added_node_id), "Node not present in directory after add")

        # Step 2: Verify audit log for 'Node added'
        self.print_step(2, "Verify audit log for 'Node added'")
        self.assert_audit_log_contains("Node added", node_id=added_node_id)

        # Step 3: Modify configuration of existing Node
        self.print_step(3, "Modify configuration of existing Node")
        new_config = {"name": "NodeAlphaRenamed"}
        await self.modify_node(added_node_id, new_config)
        asserts.assert_true(await self.is_node_config_updated(added_node_id, new_config), "Node configuration not updated")

        # Step 4: Check audit log for 'Node modified'
        self.print_step(4, "Verify audit log for 'Node modified'")
        self.assert_audit_log_contains("Node modified", node_id=added_node_id, changes=new_config)

        # Step 5: Remove a Node from the Joint Fabric
        self.print_step(5, "Remove Node from Joint Fabric")
        await self.remove_node(added_node_id)
        asserts.assert_false(await self.is_node_in_directory(added_node_id), "Node still present in directory after removal")

        # Step 6: Verify audit log for 'Node removed'
        self.print_step(6, "Verify audit log for 'Node removed'")
        self.assert_audit_log_contains("Node removed", node_id=added_node_id)

        # Step 7: Create a new Group
        self.print_step(7, "Create a new Group")
        group_id = await self.create_group(VALID_GROUP_ID)
        asserts.assert_true(await self.is_group_in_listing(group_id), "Group not present after creation")

        # Step 8: Audit log for 'Group created'
        self.print_step(8, "Verify audit log for 'Group created'")
        self.assert_audit_log_contains("Group created", group_id=group_id)

        # Step 9: Delete a Group
        self.print_step(9, "Delete Group")
        await self.delete_group(group_id)
        asserts.assert_false(await self.is_group_in_listing(group_id), "Group still present after deletion")

        # Step 10: Audit log for 'Group deleted'
        self.print_step(10, "Verify audit log for 'Group deleted'")
        self.assert_audit_log_contains("Group deleted", group_id=group_id)

        # Step 11: Assign a Node to a Group
        self.print_step(11, "Assign a Node to a Group")
        node_id = await self.add_node({"name": "GroupMemberNode"})
        group_id = await self.create_group(VALID_GROUP_ID + 1)
        await self.assign_node_to_group(node_id, group_id)
        asserts.assert_true(await self.is_node_in_group(node_id, group_id), "Node is not a member of group")

        # Step 12: Audit log for 'Node assigned to Group'
        self.print_step(12, "Verify audit log for 'Node assigned to Group'")
        self.assert_audit_log_contains("Node assigned to Group", node_id=node_id, group_id=group_id)

        # Step 13: Remove a Node from a Group
        self.print_step(13, "Remove a Node from a Group")
        await self.remove_node_from_group(node_id, group_id)
        asserts.assert_false(await self.is_node_in_group(node_id, group_id), "Node still listed in group after removal")

        # Step 14: Audit log for 'Node removed from Group'
        self.print_step(14, "Verify audit log for 'Node removed from Group'")
        self.assert_audit_log_contains("Node removed from Group", node_id=node_id, group_id=group_id)

        # Edge Step 15: Attempt to add Node with existing NodeID
        self.print_step(15, "Attempt to add a Node with an existing NodeID")
        try:
            await self.add_node({"node_id": node_id, **VALID_NODE_CONFIG})
            asserts.fail("Should not allow duplicate NodeID addition")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.DuplicateExists or "already exists" in str(e), "Unexpected error")

        # Step 16: Audit log for failed duplicate add
        self.print_step(16, "Check audit log for duplicate Node creation attempt")
        self.assert_audit_log_contains("Failed Node add", node_id=node_id, reason_contains="duplicate")

        # Step 17: Remove a non-existent Node
        self.print_step(17, "Remove a non-existent Node")
        try:
            await self.remove_node(NON_EXISTENT_NODE_ID)
            asserts.fail("Should not allow removal of non-existent node")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.NotFound or "not found" in str(e))

        # Step 18: Audit log verify
        self.print_step(18, "Audit log for attempted removal of non-existent Node")
        self.assert_audit_log_contains("Failed Node remove", node_id=NON_EXISTENT_NODE_ID, reason_contains="not found")

        # Step 19: Modify Node with invalid parameters
        self.print_step(19, "Modify Node with invalid params")
        try:
            await self.modify_node(node_id, INVALID_NODE_CONFIG)
            asserts.fail("Invalid modification accepted")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.InvalidCommand or "invalid" in str(e))

        # Step 20: Audit log for invalid modification
        self.print_step(20, "Audit log for failed Node modification")
        self.assert_audit_log_contains("Failed Node modify", node_id=node_id, reason_contains="invalid")

        # Step 21: Create Group with already existing GroupID
        self.print_step(21, "Attempt to create a Group with an existing GroupID")
        await self.create_group(DUPLICATE_GROUP_ID)
        try:
            await self.create_group(DUPLICATE_GROUP_ID)
            asserts.fail("Duplicate group creation not prevented")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.DuplicateExists or "already exists" in str(e))

        # Step 22: Audit log for duplicate group creation failure
        self.print_step(22, "Audit log for failed group creation (duplicate GroupID)")
        self.assert_audit_log_contains("Failed Group create", group_id=DUPLICATE_GROUP_ID, reason_contains="duplicate")

        # Step 23: Delete a non-existent Group
        self.print_step(23, "Delete a non-existent Group")
        try:
            await self.delete_group(NON_EXISTENT_GROUP_ID)
            asserts.fail("Should not delete a non-existent group")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.NotFound or "not found" in str(e))

        # Step 24: Audit log for failed deletion of non-existent group
        self.print_step(24, "Audit log for failed group removal (non-existent GroupID)")
        self.assert_audit_log_contains("Failed Group delete", group_id=NON_EXISTENT_GROUP_ID, reason_contains="not found")

        # Step 25: Assign a Node to non-existent Group
        self.print_step(25, "Assign Node to non-existent Group")
        try:
            await self.assign_node_to_group(node_id, NON_EXISTENT_GROUP_ID)
            asserts.fail("Node assigned to non-existent group")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.NotFound or "not found" in str(e))

        # Step 26: Assign non-existent Node to Group
        self.print_step(26, "Assign non-existent Node to Group")
        try:
            await self.assign_node_to_group(NON_EXISTENT_NODE_ID, group_id)
            asserts.fail("Non-existent Node assigned to group")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.NotFound or "not found" in str(e))

        # Step 27: Audit log for failed group membership assign
        self.print_step(27, "Audit log for failed Node-to-Group assignment attempts")
        self.assert_audit_log_contains("Failed Group assign", node_id=node_id, group_id=NON_EXISTENT_GROUP_ID)
        self.assert_audit_log_contains("Failed Group assign", node_id=NON_EXISTENT_NODE_ID, group_id=group_id)

        # Step 28: Remove Node from Group where not a member
        self.print_step(28, "Remove Node from group where it is NOT a member")
        try:
            await self.remove_node_from_group(node_id, group_id)
            asserts.fail("Should not remove Node from group it isn't a member of")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.NotFound or "not a member" in str(e))

        # Step 29: Audit log for failed attempt
        self.print_step(29, "Audit log for failed removal from non-membership")
        self.assert_audit_log_contains("Failed Group removal", node_id=node_id, group_id=group_id)

        # Step 30: Rapid consecutive Node/Group modifications
        self.print_step(30, "Perform rapid consecutive modifications to Node/Group")
        for i in range(5):
            mod_conf = {"alias": f"node{i}"}
            await self.modify_node(node_id, mod_conf)
        log_records = self.get_audit_logs("Node modified", node_id=node_id)
        assert len(log_records) >= 5, f"Not all modifications logged, found {len(log_records)}"
        timestamps = [rec["timestamp"] for rec in log_records[-5:]]
        asserts.assert_true(all(timestamps[i] < timestamps[i+1] for i in range(4)), "Timestamps are not ordered")

        # Step 31: Unauthorized operation
        self.print_step(31, "Attempt administrative operation with invalid credentials")
        try:
            await self.add_node(VALID_NODE_CONFIG, credentials=INVALID_CREDENTIALS)
            asserts.fail("Unauthorized operation succeeded")
        except InteractionModelError as e:
            asserts.assert_true(e.status == Status.AccessDenied or "unauthorized" in str(e))

        # Step 32: Audit log for unauthorized op
        self.print_step(32, "Audit log for unauthorized operation attempt")
        self.assert_audit_log_contains("Unauthorized operation", user=DUMMY_USER, reason_contains="access denied")

    # --- The following are STUB methods for demonstration purposes only ---
    # In a real test harness, these would interact with Matter API/clusters and parse responses.

    async def add_node(self, node_config: Dict[str, Any], credentials: Dict = None):
        """
        Simulate API/UI call to add Node, returns NodeID.
        """
        # Placeholder for add_node logic; would call Matter admin API
        return DUMMY_NODE_ID + 1

    async def is_node_in_directory(self, node_id):
        """
        Simulate check for Node in directory.
        """
        return True

    async def modify_node(self, node_id, config: Dict[str, Any]):
        """
        Simulate configuration update for Node.
        """
        return None

    async def is_node_config_updated(self, node_id, new_config):
        """
        Simulate check that configuration is updated.
        """
        return True

    async def remove_node(self, node_id):
        """
        Simulate removing a Node.
        """
        return None

    async def create_group(self, group_id):
        """
        Simulate creation of a Group.
        """
        return group_id

    async def delete_group(self, group_id):
        """
        Simulate deletion of a Group.
        """
        return None

    async def is_group_in_listing(self, group_id):
        """
        Simulate check if Group exists.
        """
        return True

    async def assign_node_to_group(self, node_id, group_id):
        """
        Simulate assigning a Node to a Group.
        """
        return None

    async def is_node_in_group(self, node_id, group_id):
        return True

    async def remove_node_from_group(self, node_id, group_id):
        """
        Simulate removing Node from Group.
        """
        return None

    def get_audit_logs(self, action: str = None, **kwargs) -> list:
        # Placeholder for audit log querying
        return [{"action": action, "timestamp": i, **kwargs} for i in range(5)]

    def assert_audit_log_contains(self, action: str, **fields):
        """
        Assert that the audit log contains a record matching action and fields.
        """
        logs = self.get_audit_logs(action, **fields)
        for log in logs:
            if all(str(log.get(k, '')).startswith(str(v)) or str(log.get(k, '')) == str(v)
                   for k, v in fields.items() if not k.endswith("reason_contains")) and \
                all(fields[k] in str(log.get("reason", "")) for k in fields if k.endswith("reason_contains")):
                return
        asserts.fail(f"Audit log does not contain expected record: {action}, {fields}")


if __name__ == "__main__":
    default_matter_test_main()
```
