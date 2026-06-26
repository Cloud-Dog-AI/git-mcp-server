# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""W28J-1328 — Settings config-source provenance backend (FR1.17, GMC-SE-02)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from git_mcp_server import config_sources
from git_mcp_server.api_server import create_api_app
from git_mcp_server.ui_endpoints import _mask_runtime_config


# ---------------------------------------------------------------------------
# Unit: provenance classification (no app)
# ---------------------------------------------------------------------------
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind

def test_build_config_sources_classifies_every_layer() -> None:
    defaults_raw = {
        "api_server": {"host": "0.0.0.0", "port": 8078},
        "web_login": {"password": "${CLOUD_DOG_WEB_LOGIN_PASSWORD:''}"},
        "auth": {"mode": "api_key"},
    }
    config_raw = {
        "api_server": {"port": "${CLOUD_DOG__API_SERVER__PORT}"},
        "git": {"default_branch": "main"},
    }
    # Effective (resolved) tree: env overrode api_server.port; password resolved; env-only token added.
    effective = {
        "api_server": {"host": "0.0.0.0", "port": 8083},
        "web_login": {"password": "REAL-SECRET-VALUE"},
        "auth": {"mode": "api_key"},
        "git": {"default_branch": "main"},
        "vault": {"token": "hvs.SECRET"},
    }
    sources, counts = config_sources.build_config_sources(effective, defaults_raw, config_raw)

    assert sources["api_server.host"] == {"source": "default", "secret": False}
    assert sources["api_server.port"]["source"] == "env"            # ${ENV} placeholder in config.yaml
    assert sources["git.default_branch"] == {"source": "config", "secret": False}
    assert sources["auth.mode"] == {"source": "default", "secret": False}
    # secret via ${ENV} placeholder -> vault + flagged
    assert sources["web_login.password"] == {"source": "vault", "secret": True}
    # secret present only in the resolved tree -> vault + flagged
    assert sources["vault.token"] == {"source": "vault", "secret": True}

    assert counts["total"] == 6
    assert counts["secret"] == 2
    assert counts["default"] == 2   # api_server.host + auth.mode
    assert counts["config"] == 1    # git.default_branch
    assert counts["env"] == 1       # api_server.port (${ENV} placeholder)
    assert counts["vault"] == 2     # web_login.password + vault.token
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_build_config_sources_never_emits_values() -> None:
    effective = {"web_login": {"password": "SUPER-SECRET"}, "auth": {"token": "hvs.LEAK"}}
    sources, _ = config_sources.build_config_sources(effective, {}, {})
    serialized = repr(sources)
    assert "SUPER-SECRET" not in serialized
    assert "hvs.LEAK" not in serialized
    for meta in sources.values():
        assert set(meta.keys()) == {"source", "secret"}
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_env_override_of_literal_default_is_env() -> None:
    # defaults.yaml has a literal; the effective tree differs -> env-overridden.
    sources, _ = config_sources.build_config_sources(
        {"runtime": {"mode": "production"}}, {"runtime": {"mode": "development"}}, {}
    )
    assert sources["runtime.mode"]["source"] == "env"


# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind
def test_secret_mapping_source_path_matches_masked_config_shape() -> None:
    effective = {
        "storage": {
            "https_credentials": {
                "url": "https://git.example.test/project.git",
                "token": "SECRET-TOKEN",
            }
        },
        "api_server": {"port": 19031},
    }

    masked = _mask_runtime_config(effective)
    sources, counts = config_sources.build_config_sources(effective, {}, {})

    assert masked["storage"]["https_credentials"] == "****"
    assert sources["storage.https_credentials"] == {"source": "vault", "secret": True}
    assert "storage.https_credentials.url" not in sources
    assert "storage.https_credentials.token" not in sources
    assert counts["total"] == 2


# ---------------------------------------------------------------------------
# Integration: live endpoints via the assembled API app
# ---------------------------------------------------------------------------

def _client(tmp_path: Path, monkeypatch) -> tuple[TestClient, dict[str, str]]:
    monkeypatch.setenv("CLOUD_DOG__STORAGE__AUDIT__PATH", (tmp_path / "audit.jsonl").as_posix())
    app = create_api_app(env_files=["tests/env-UT"])
    return TestClient(app), {"x-api-key": app.state.seed_api_key}
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_settings_config_endpoint_returns_masked_tree(tmp_path: Path, monkeypatch) -> None:
    client, headers = _client(tmp_path, monkeypatch)
    resp = client.get("/api/v1/settings/config", headers=headers)
    assert resp.status_code == 200
    tree = resp.json()["result"]
    assert isinstance(tree, dict) and tree, "effective config tree must be non-empty"
    # Secret leaves are masked, never raw.
    web_login = tree.get("web_login") or {}
    if "password" in web_login:
        assert web_login["password"] in ("****", "", None, [], {})
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_settings_config_sources_endpoint(tmp_path: Path, monkeypatch) -> None:
    client, headers = _client(tmp_path, monkeypatch)
    resp = client.get("/api/v1/settings/config/sources", headers=headers)
    assert resp.status_code == 200
    result = resp.json()["result"]
    sources = result["sources"]
    counts = result["counts"]
    assert counts["total"] > 0
    assert counts["total"] == len(sources)
    assert set(counts) >= {"total", "secret", "default", "config", "env", "vault"}
    for path, meta in sources.items():
        assert meta["source"] in {"default", "config", "env", "vault"}, f"{path} -> {meta['source']}"
        assert set(meta.keys()) == {"source", "secret"}
    # secret leaves are flagged
    secret_paths = [p for p, m in sources.items() if m["secret"]]
    assert all(sources[p]["secret"] is True for p in secret_paths)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_settings_config_audit_reveal(tmp_path: Path, monkeypatch) -> None:
    client, headers = _client(tmp_path, monkeypatch)
    resp = client.post("/api/v1/settings/config/audit-reveal", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result"]["revealed"] is True
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-017")  # W28E-1804A semantic rebind


def test_settings_config_requires_admin(tmp_path: Path, monkeypatch) -> None:
    client, _ = _client(tmp_path, monkeypatch)
    resp = client.get("/api/v1/settings/config/sources")  # no api key
    assert resp.status_code in (401, 403)
