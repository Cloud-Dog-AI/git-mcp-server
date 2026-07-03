# External Build

Build the public container from the repository root:

```bash
docker build -f Dockerfile.public -t git-mcp-server:public .
```

Run with local environment values from [.env.example](.env.example). Do not put
private tokens or runtime secrets in committed files.
