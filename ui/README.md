# UI Build Output

`ui/dist/` is generated from the monorepo app:

- source app: `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo/apps/git-mcp/`
- local build: `npm run build --workspace=apps/git-mcp`
- local copy:

```bash
mkdir -p ui
rm -rf ui/dist
cp -r /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo/apps/git-mcp/dist ui/dist
```

`ui/dist/` is a generated artifact and is not committed.
