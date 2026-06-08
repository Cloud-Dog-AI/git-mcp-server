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

import os
from collections.abc import Iterator
from contextlib import contextmanager

from cloud_dog_storage import path_utils
from filelock import FileLock


def lock_path_for_workspace(workspace_path: str | os.PathLike[str]):
    """Return lock file path for a workspace directory."""
    workspace = path_utils.as_path(str(workspace_path))
    return workspace / ".workspace.lock"


@contextmanager
def workspace_lock(workspace_path: str | os.PathLike[str], timeout_seconds: float = 5.0) -> Iterator[FileLock]:
    """Acquire and release a per-workspace file lock."""
    lock = FileLock(str(lock_path_for_workspace(workspace_path)), timeout=timeout_seconds)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()
