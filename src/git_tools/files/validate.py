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

import yaml
from bs4 import BeautifulSoup
from cloud_dog_storage import path_utils
from lxml import etree

from git_tools.files.io import load_host_text


def validate_file(path: str | object) -> dict[str, object]:
    """Validate a file according to extension and return structured result."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    ext = file_path.suffix.lower()
    text = load_host_text(file_path)
    errors: list[str] = []

    try:
        if ext == ".json":
            json.loads(text)
        elif ext in {".yaml", ".yml"}:
            yaml.safe_load(text)
        elif ext == ".xml":
            etree.fromstring(text.encode("utf-8"))
        elif ext == ".html":
            BeautifulSoup(text, "html.parser")
        elif ext == ".md":
            if "\x00" in text:
                raise ValueError("NUL bytes are not valid markdown content")
        else:
            return {"valid": True, "type": "unknown", "errors": []}
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))

    return {
        "valid": len(errors) == 0,
        "type": ext.lstrip("."),
        "errors": errors,
    }
