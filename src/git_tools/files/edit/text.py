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

from cloud_dog_storage import path_utils

from git_tools.files.io import load_host_text, store_host_text


def replace_text(content: str, find: str, replace: str, count: int = -1) -> str:
    """Replace text occurrences."""
    return content.replace(find, replace, count)


def replace_file_text(path: str | object, find: str, replace: str, count: int = -1) -> str:
    """Replace file content text and persist changes."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    original = load_host_text(file_path)
    updated = replace_text(original, find, replace, count=count)
    store_host_text(file_path, updated)
    return updated
