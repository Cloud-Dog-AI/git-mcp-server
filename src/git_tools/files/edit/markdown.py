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

import re

from cloud_dog_storage import path_utils

from git_tools.files.io import load_host_text, store_host_text


def replace_markdown_section(path: str | object, heading: str, replacement: str) -> str:
    """Replace section content for a top-level heading in markdown file."""
    file_path = path_utils.as_path(str(path)).expanduser().resolve()
    text = load_host_text(file_path)

    pattern = re.compile(
        rf"(^##?\s+{re.escape(heading)}\s*$)(.*?)(?=^##?\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if not pattern.search(text):
        text = text.rstrip() + f"\n\n## {heading}\n\n{replacement.strip()}\n"
    else:
        text = pattern.sub(lambda m: f"{m.group(1)}\n\n{replacement.strip()}\n", text)

    store_host_text(file_path, text)
    return text
