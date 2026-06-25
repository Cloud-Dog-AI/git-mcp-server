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

"""W28J-1329 — fixture-validation IT: proves the seeded catalog carries the REAL content the
deep-flow e2e (W28J-1330) will assert through the UI. Runs locally (no server/deploy): it builds
the catalog and exercises the git layer directly, so a green run here means the e2e has real,
non-empty data to assert against — not "a list renders". Covers GMC-C-09 / X-03 / M-04 / P-06 at
the data layer; the UI render of these + J-05/SE-02 is authored in w28j-1329-deep-flows.spec.ts."""

from __future__ import annotations

from pathlib import Path

import pytest
from git import GitCommandError, Repo

from tests.fixtures.seed_gitmcp_testdata import build_catalog


@pytest.fixture(scope="module")
def catalog(tmp_path_factory: pytest.TempPathFactory) -> dict:
    root = tmp_path_factory.mktemp("w28j1329-seed")
    return build_catalog(root)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_seed_covers_all_six_waived_gmc(catalog: dict) -> None:
    covered = {g for fx in catalog["fixtures"].values() for g in fx["gmc"]}
    assert covered == {"GMC-P-06", "GMC-C-09", "GMC-X-03", "GMC-M-04", "GMC-J-05", "GMC-SE-02"}
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_commits_history_real_content(catalog: dict) -> None:  # GMC-C-09
    fx = catalog["fixtures"]["commits_repo"]
    repo = Repo(fx["path"])
    log = list(repo.iter_commits("main"))
    assert len(log) == 4, "deterministic 4-commit history"
    # newest-first messages + author identity (real content, not render-only)
    assert [c.message.strip() for c in log] == [c["message"] for c in reversed(fx["expected_commits"])]
    assert {c.author.name for c in log} == {"Ada Lovelace"}
    # deterministic SHAs match the published catalog
    by_msg = {c.message.strip(): c.hexsha for c in log}
    for exp in fx["expected_commits"]:
        assert by_msg[exp["message"]] == exp["sha"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_diff_hunks_real_content(catalog: dict) -> None:  # GMC-X-03
    fx = catalog["fixtures"]["diff_repo"]
    repo = Repo(fx["path"])
    diff = repo.git.diff(fx["base_ref"], fx["change_ref"], "--name-status", "-M")
    assert "A\tadded.txt" in diff                      # add
    assert "M\tkeep.txt" in diff                       # modify
    assert "D\tremove.txt" in diff                     # delete
    assert any(line.startswith("R") and "old_name.txt" in line and "new_name.txt" in line
               for line in diff.splitlines())          # rename
    # binary modification carries no text hunk
    patch = repo.git.diff(fx["base_ref"], fx["change_ref"], "--", "logo.bin")
    assert "Binary files" in patch or "GIT binary patch" in patch
    # content-level assertion on the modify hunk
    keep_patch = repo.git.diff(fx["base_ref"], fx["change_ref"], "--", "keep.txt")
    assert "-line2" in keep_patch and "+line2-CHANGED" in keep_patch and "+line4-added" in keep_patch
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_merge_conflict_real_region(catalog: dict, tmp_path: Path) -> None:  # GMC-M-04
    fx = catalog["fixtures"]["conflict_repo"]
    # clone so the merge attempt does not mutate the shared fixture
    work = Repo.clone_from(fx["path"], tmp_path / "merge_work")
    work.git.config("user.email", "ci@cloud-dog.test")
    work.git.config("user.name", "Cloud-Dog CI")
    work.git.checkout("main")
    with pytest.raises(GitCommandError):
        work.git.merge("origin/feature/conflict")  # deterministic conflict
    conflicted = (tmp_path / "merge_work" / fx["conflict_file"]).read_text(encoding="utf-8")
    assert "<<<<<<<" in conflicted and ">>>>>>>" in conflicted
    assert "MAIN-EDIT" in conflicted and "FEATURE-EDIT" in conflicted  # the engineered region
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_source_variants_each_open(catalog: dict, tmp_path: Path) -> None:  # GMC-P-06
    fx = catalog["fixtures"]["source_variants"]
    profiles = fx["profiles"]
    assert {p["source_type"] for p in profiles.values()} == {"local-path", "file-remote", "http-remote"}
    # local-path + file-remote are seeded locally -> clone/open offline (http variant is exercised live in 1330)
    for name in ("seed_local_path", "seed_file_remote"):
        src = profiles[name]["repo"]["source"]
        clone = Repo.clone_from(src, tmp_path / name)
        assert clone.head.commit.message.strip() != ""
        assert (Path(clone.working_dir) / "README.md").exists()
