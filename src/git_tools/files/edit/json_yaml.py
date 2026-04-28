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

from __future__ import annotations

import json
from typing import Any

import yaml
from cloud_dog_storage import path_utils

from git_tools.files.io import load_host_text, store_host_text


def _split_pointer(pointer: str) -> list[str]:
    if pointer in {"", "/"}:
        return []
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer.lstrip("/").split("/")]


def set_json_pointer(data: Any, pointer: str, value: Any) -> Any:
    """Set a JSON pointer value on a mutable mapping/list tree."""
    parts = _split_pointer(pointer)
    if not parts:
        return value

    node = data
    for part in parts[:-1]:
        if isinstance(node, dict):
            node = node.setdefault(part, {})
        elif isinstance(node, list):
            index = int(part)
            while len(node) <= index:
                node.append({})
            node = node[index]
        else:
            raise TypeError("Unsupported pointer target")

    leaf = parts[-1]
    if isinstance(node, dict):
        node[leaf] = value
    elif isinstance(node, list):
        index = int(leaf)
        while len(node) <= index:
            node.append(None)
        node[index] = value
    else:
        raise TypeError("Unsupported pointer target")
    return data


def edit_json_file(path: str | object, pointer: str, value: Any) -> Any:
    """Apply JSON Pointer update to a JSON file."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    data = json.loads(load_host_text(file_path))
    updated = set_json_pointer(data, pointer, value)
    store_host_text(file_path, json.dumps(updated, indent=2, ensure_ascii=True) + "\n")
    return updated


def edit_yaml_file(path: str | object, pointer: str, value: Any) -> Any:
    """Apply JSON Pointer update to a YAML file."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    data = yaml.safe_load(load_host_text(file_path))
    updated = set_json_pointer(data, pointer, value)
    store_host_text(file_path, yaml.safe_dump(updated, sort_keys=False))
    return updated
