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

"""Branch-scoped file operations and editors."""

from cloud_dog_storage import decode_base64, encode_base64, path_utils

from git_tools.files.diff import diff_files, diff_text
from git_tools.files.io import (
    copy_entry,
    ensure_directory,
    list_entries,
    load_host_bytes,
    load_text,
    move_entry,
    remove_directory,
    remove_entry,
    store_host_bytes,
    store_bytes_atomic,
    store_text_atomic,
)
from git_tools.files.search import search_content, search_files
from git_tools.files.validate import validate_file


def file_to_base64(path: str | object) -> str:
    """Encode file bytes as base64 text."""
    payload = load_host_bytes(str(path))
    return encode_base64(payload)


def base64_to_file(encoded: str, path: str | object):
    """Decode base64 payload into file path."""
    store_host_bytes(str(path), decode_base64(encoded))
    return path_utils.as_path(str(path)).expanduser().resolve()

__all__ = [
    "base64_to_file",
    "copy_entry",
    "diff_files",
    "diff_text",
    "ensure_directory",
    "file_to_base64",
    "list_entries",
    "load_text",
    "move_entry",
    "remove_directory",
    "remove_entry",
    "search_content",
    "search_files",
    "store_bytes_atomic",
    "store_text_atomic",
    "validate_file",
]
