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

import threading
from pathlib import Path

from git_tools.workspaces.locks import workspace_lock


def test_workspace_locking_serialises_access(tmp_path: Path) -> None:
    """Requirements: FR-01."""
    target = tmp_path / "events.txt"
    target.write_text("", encoding="utf-8")

    def worker(label: str) -> None:
        with workspace_lock(tmp_path):
            existing = target.read_text(encoding="utf-8")
            target.write_text(existing + label + "\n", encoding="utf-8")

    threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = [line for line in target.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 3
