# Git MCP Use Cases

## UC-CFG-01 New Repository Profile With Branch Restrictions

1. Create a new repository profile pointing at a test repository path.
2. Configure allowed refs or branch restrictions for the profile.
3. Open the repository through the profile and verify file and git operations work.
4. Update the profile to change repository source or ref policy.
5. Verify the updated policy is enforced for subsequent workspace operations.
6. Delete the profile and confirm it is no longer returned by admin/profile endpoints.

Current status:
- API admin profile lifecycle is delivered.
- MCP parity is present for admin/profile operations.
- A2A change broadcast and clearer WebUI parity remain incomplete.
