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

import difflib

from cloud_dog_storage import path_utils

from git_tools.files.io import load_host_text


def diff_text(before: str, after: str, fromfile: str = "before", tofile: str = "after") -> str:
    """Return unified diff string between two text inputs."""
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=fromfile,
        tofile=tofile,
    )
    return "".join(diff)


def diff_files(left: str | object, right: str | object) -> str:
    """Return unified diff between two files."""
    left_path = path_utils.as_path(str(left)).expanduser().resolve()
    right_path = path_utils.as_path(str(right)).expanduser().resolve()
    return diff_text(
        load_host_text(left_path),
        load_host_text(right_path),
        fromfile=str(left_path),
        tofile=str(right_path),
    )
