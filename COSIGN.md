# Container image signing

Public release images are published to `ghcr.io/cloud-dog-ai/git-mcp-server` and
signed with [cosign](https://github.com/sigstore/cosign). Verify a pulled image
against the published public key `cosign.pub`:

```
cosign verify --key cosign.pub ghcr.io/cloud-dog-ai/git-mcp-server:w28a-865-r17
```

The signature is also recorded in the Sigstore public transparency log (Rekor).
