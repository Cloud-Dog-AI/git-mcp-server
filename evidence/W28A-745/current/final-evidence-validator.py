#!/usr/bin/env python3
"""Validate the W28A-745 git-mcp evidence packet."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing evidence file: {rel}")
    return path.read_text(encoding="utf-8", errors="replace")


def require(rel: str, *needles: str) -> None:
    text = read(rel)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{rel} missing: {missing}")


def main() -> int:
    failures: list[str] = []
    checks = [
        ("g1-greps/g1-bespoke-greps.txt", ["## direct yaml config loads", "## hardcoded /app/ in non-comments src"]),
        ("g3-pytest/qt-security.log", ["62 passed"]),
        ("g3-pytest/w28a-745-focused-t0-t3.log", ["5 passed"]),
        ("g3-pytest/unit.log", ["177 passed"]),
        ("g3-pytest/system.log", ["23 passed"]),
        ("g3-pytest/integration.log", ["28 passed"]),
        ("g3-pytest/application.log", ["9 passed"]),
        ("g2-local-service/local-health.log", ["http://127.0.0.1:19031/health", "http_code=200", "19034/health"]),
        ("g4-build/docker-build-dev.log", ["Build OK: cloud-dog/git-mcp-server:latest", "Tagged: registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest"]),
        ("g5-docker/local-docker-smoke.log", ["HEALTH CHECK PASSED", "git-mcp-server", "cloud-dog-idam"]),
        ("g6-git/source-push.log", ["ancestor_check=PASS", "e140800a7223139ab6fb5ba7319c6e1976ad69ea"]),
        ("g6-git/docker-push.log", ["sha256:25fba52d73c2b369e526f551881fb506945323d22694b5c15cb14ac7ef1f8e11"]),
        ("g7-deploy/terraform-targeted-apply.log", ["docker_container.gitmcpserver0", "Apply complete! Resources: 2 added, 0 changed, 2 destroyed."]),
        ("g8-live/remote-docker-proof.log", ["health=healthy", "sha256:25fba52d73c2b369e526f551881fb506945323d22694b5c15cb14ac7ef1f8e11"]),
        ("g8-live/live-current-pass.log", ["https://gitmcpserver0.cloud-dog.net/health -> http_code=200", "registry_latest_digest=sha256:25fba52d73c2b369e526f551881fb506945323d22694b5c15cb14ac7ef1f8e11", "digest_match=PASS"]),
        ("g8-live/live-mcp-current-pass.log", ["configured_git_api_key=REDACTED", "tools_list_http_code=200", "admin_api_key_list_http_code=200"]),
        ("g8-live/live-mcp-functional-proof.log", ["configured_git_api_key=REDACTED", "http_code=200", "w28a745-ping"]),
        ("g8-live/live-mcp-toolcall-audit.log", ["admin_api_key_list", "outcome\": \"success\"", "19 /app/data/git-mcp-tool-audit.jsonl"]),
        ("g8-live/browser-smoke-current/browser-smoke-current.tsv", ["target-gitmcpserver0", "sentinel-chatclient0", "sentinel-expertagent0", "sentinel-notificationagent0", "sentinel-filemcpserver0", "signed-in", "\t0\t0\t", "\tPASS"]),
        ("g8-live/estate/preprod-health-current.tsv", ["gitmcpserver0", "chatclient0", "expertagent0", "notificationagent0", "filemcpserver0", "\t200\t"]),
        ("vault-iac-parity/vault-iac-parity-summary.tsv", ["Vault dev/services contains gitmcpserver0", "IaC Vault service refs exactly web_password,web_username", "\tPASS"]),
        ("00-reading-proof.md", ["RULES_REREAD: YES", "AGENT-LESSONS-REREAD: YES", "AGENT_BOOTSTRAP_DIRECTIVE_REREAD: YES", "GATE_0_WARRANT_EMITTED: YES"]),
        ("00A-936-937-service-tail-classification.tsv", ["W28A-937", "READ_ONLY_CLASSIFIED", "FOLDED_LIVE"]),
        ("g8-live/remote-package-versions.log", ["cloud-dog-config", "cloud-dog-api-kit", "cloud-dog-idam", "git-mcp-server"]),
    ]
    for rel, needles in checks:
        try:
            require(rel, *needles)
        except AssertionError as exc:
            failures.append(str(exc))

    for rel in [
        "g3-pytest/qt-security.log",
        "g3-pytest/w28a-745-focused-t0-t3.log",
        "g3-pytest/unit.log",
        "g3-pytest/system.log",
        "g3-pytest/integration.log",
        "g3-pytest/application.log",
    ]:
        text = read(rel)
        if " skipped" in text or "SKIPPED" in text:
            failures.append(f"{rel} contains skipped tests")
        if " failed" in text or "FAILED" in text:
            failures.append(f"{rel} contains failed tests")

    active_fail_files = [
        "g8-live/browser-smoke-current/browser-smoke-current.tsv",
        "g8-live/estate/preprod-health-current.tsv",
        "vault-iac-parity/vault-iac-parity-summary.tsv",
        "requirements-map.tsv",
    ]
    for rel in active_fail_files:
        text = read(rel)
        if "\tFAIL" in text or "\tNO" in text:
            failures.append(f"{rel} contains non-passing active row")

    if failures:
        for failure in failures:
            print(f"VALIDATOR_FAILURE: {failure}")
        print(f"FINAL_EVIDENCE_VALIDATOR: FAIL failures={len(failures)}")
        return 1
    print("FINAL_EVIDENCE_VALIDATOR: PASS failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
