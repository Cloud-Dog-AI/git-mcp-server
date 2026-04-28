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

from tests.unit._tool_registry_harness import open_workspace_harness


def test_search_files_query_and_glob_filters(tmp_path) -> None:
    """Requirements: FR-08. UCs: UC-011."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "docs/match-one.txt", "content": "a\n"},
        )
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "docs/match-two.md", "content": "b\n"},
        )
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "other/unrelated.txt", "content": "c\n"},
        )

        only_txt = harness.registry.call(
            "search_files",
            {
                "workspace_id": harness.workspace_id,
                "query": "match",
                "globs": ["**/*.txt"],
            },
        )["results"]
        assert "docs/match-one.txt" in only_txt
        assert "docs/match-two.md" not in only_txt

        empty = harness.registry.call(
            "search_files",
            {"workspace_id": harness.workspace_id, "query": "does-not-exist"},
        )["results"]
        assert empty == []
    finally:
        harness.close()
