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

"""W28J-1328 — per-leaf configuration source provenance for the Settings UI.

Computes, for every leaf of the resolved (effective) runtime configuration, which
layer it came from — ``default`` (defaults.yaml literal), ``config`` (config.yaml
literal), ``env`` (environment variable / placeholder), or ``vault`` (secret material
resolved via an environment placeholder). Secret values are NEVER emitted: the source
map carries only ``{source, secret}`` per leaf, and secret leaves are flagged so the UI
masks them. Path keys match the PS-81 JsonExplorer scheme: dot-joined object keys with
array indices as ``[i]`` and no synthetic ``root`` prefix.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

from cloud_dog_config.errors import YAMLLoadError
from cloud_dog_config.yaml_loader import load_yaml

# Mirrors git_mcp_server.ui_endpoints._mask_runtime_config secret heuristic for consistency.
_SECRET_FRAGMENTS = (
    "password", "secret", "token", "api_key", "apikey", "credential", "private_key", "key_hash",
)
_TEMPLATE_RE = re.compile(r"\$\{[^}]*\}")
_VAULT_HINT_RE = re.compile(r"vault", re.IGNORECASE)
_ARRAY_IDX_RE = re.compile(r"\[\d+\]$")

SourceMeta = dict[str, Any]


def is_secret_key(key: str) -> bool:
    """True when a leaf key name indicates secret material."""
    lowered = str(key).lower()
    return any(fragment in lowered for fragment in _SECRET_FRAGMENTS)


def _leaf_key(path: str) -> str:
    seg = path.split(".")[-1]
    return _ARRAY_IDX_RE.sub("", seg)


def flatten(value: Any, parent: str = "") -> dict[str, Any]:
    """Flatten a config tree to ``{dot.path[i]: scalar}`` (JsonExplorer scheme, no root)."""
    out: dict[str, Any] = {}
    if parent and is_secret_key(_leaf_key(parent)) and isinstance(value, (Mapping, list, tuple)):
        out[parent] = value
        return out
    if isinstance(value, Mapping):
        for key, item in value.items():
            path = f"{parent}.{key}" if parent else str(key)
            if isinstance(item, (Mapping, list, tuple)):
                out.update(flatten(item, path))
            else:
                out[path] = item
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            path = f"{parent}[{index}]"
            if isinstance(item, (Mapping, list, tuple)):
                out.update(flatten(item, path))
            else:
                out[path] = item
    elif parent:
        out[parent] = value
    return out


def _classify(path: str, eff_val: Any, cfg: dict[str, Any], dft: dict[str, Any], secret: bool) -> str:
    in_cfg = path in cfg
    in_dft = path in dft
    if not in_cfg and not in_dft:
        # Present only in the resolved tree -> set by an environment variable.
        return "vault" if secret else "env"
    raw = cfg[path] if in_cfg else dft[path]
    if isinstance(raw, str) and _TEMPLATE_RE.search(raw):
        # ${ENV_VAR} placeholder: secret material (or an explicit vault reference) -> vault.
        return "vault" if (secret or _VAULT_HINT_RE.search(raw)) else "env"
    if str(raw) == str(eff_val):
        # Literal that survived to the effective tree unchanged.
        return "config" if in_cfg else "default"
    # A literal default/config value that the environment overrode at runtime.
    return "vault" if secret else "env"


def build_config_sources(
    effective: Any,
    defaults_raw: Any,
    config_raw: Any,
) -> tuple[dict[str, SourceMeta], dict[str, int]]:
    """Return ``(sources, counts)`` for the effective config. No secret values are emitted."""
    eff = flatten(effective)
    cfg = flatten(config_raw or {})
    dft = flatten(defaults_raw or {})
    sources: dict[str, SourceMeta] = {}
    counts: dict[str, int] = {"total": 0, "secret": 0, "default": 0, "config": 0, "env": 0, "vault": 0}
    for path in sorted(eff):
        secret = is_secret_key(_leaf_key(path))
        source = _classify(path, eff[path], cfg, dft, secret)
        sources[path] = {"source": source, "secret": bool(secret)}
        counts["total"] += 1
        if secret:
            counts["secret"] += 1
        counts[source] = counts.get(source, 0) + 1
    return sources, counts


def _load_yaml(path: str) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return load_yaml(path, missing_ok=True)
    except (OSError, YAMLLoadError):
        return {}


def load_layers(
    defaults_yaml: str = "defaults.yaml",
    config_yaml: str = "config.yaml",
    base_dir: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the raw (unresolved) defaults.yaml and config.yaml layers from the service CWD.

    Returns ``(defaults_raw, config_raw)``; a missing config.yaml yields ``{}`` (env-only deploy).
    """
    root = base_dir or os.getcwd()
    return (
        _load_yaml(defaults_yaml if os.path.isabs(defaults_yaml) else os.path.join(root, defaults_yaml)),
        _load_yaml(config_yaml if os.path.isabs(config_yaml) else os.path.join(root, config_yaml)),
    )
