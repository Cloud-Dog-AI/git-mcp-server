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

"""Git change-watch criteria matching (PS-102 CSTREAM-GIT-001/002).

The criteria matcher is a *pure* function over a proposed :class:`ChangeCandidate`
(a single observed repository change — a commit, a branch/tag movement, or a
file add/modify/delete within a commit) and a watch's declarative ``criteria``
mapping. It decides whether an observed change matches a watch and, when it does,
returns the ``criteria_match`` provenance the common
:class:`cloud_dog_api_kit.change_stream.ChangeEvent` envelope requires so a
consumer can prove the event is not a false positive (PS-102 §4).

Supported criteria fields (CSTREAM-GIT-001):

* ``ref`` — glob or ``re:`` regex over the fully-qualified ref (``refs/heads/main``,
  ``refs/tags/v1.2.0``) OR the short ref name (``main`` / ``v1.2.0``).
* ``branch`` — exact branch short-name (or list); matches only branch refs.
* ``tag`` — exact tag short-name (or list); matches only tag refs.
* ``path`` — glob or ``re:`` regex over any changed file path in the change.
* ``author`` — glob or ``re:`` regex over the commit author (name or email).
* ``action`` — one action verb or a list of verbs from the canonical set
  (``created`` = add, ``updated`` = modify, ``deleted``, ``force_updated``,
  ``metadata_changed`` = branch/tag movement, ``moved`` = rename).

No criterion means "match everything" (an unfiltered watch). This module owns NO
journal / cursor / queue logic — that all lives in the common foundation
(RULES §1.4).
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from cloud_dog_api_kit.change_stream import ACTIONS
from cloud_dog_api_kit.change_stream.errors import InvalidCriteria

_REGEX_PREFIX = "re:"

# Criteria keys this service understands (CSTREAM-GIT-001). Unknown keys are a
# hard InvalidCriteria at watch-create time rather than a silent no-op.
_KNOWN_CRITERIA = frozenset(
    {
        "ref",
        "branch",
        "tag",
        "path",
        "author",
        "action",
    }
)

# Canonical ref namespaces (short-name derivation is namespace-aware).
_HEADS_PREFIX = "refs/heads/"
_TAGS_PREFIX = "refs/tags/"


@dataclass(frozen=True)
class ChangeCandidate:
    """A proposed git repository change evaluated against a watch's criteria.

    A candidate represents a single observed change keyed by commit/ref identity
    (PS-102 CSTREAM-GIT-002). ``ref`` carries the fully-qualified ref the change
    was observed on (``refs/heads/main`` / ``refs/tags/v1``); ``ref_type`` is one
    of ``branch`` | ``tag`` | ``other``. ``paths`` are the file paths touched by
    the underlying commit(s). The candidate carries no secrets.
    """

    action: str
    object_ref: str
    ref: str = ""
    ref_type: str = "other"
    object_version: str = ""
    author: str = ""
    paths: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def short_ref(self) -> str:
        """Namespace-stripped short ref name (``main`` / ``v1.2.0``)."""
        if self.ref.startswith(_HEADS_PREFIX):
            return self.ref[len(_HEADS_PREFIX):]
        if self.ref.startswith(_TAGS_PREFIX):
            return self.ref[len(_TAGS_PREFIX):]
        return self.ref


def validate_criteria(criteria: Mapping[str, Any]) -> None:
    """Validate a watch's criteria mapping, raising ``InvalidCriteria`` on error.

    Called at watch-create time so an unsupported field / bad regex / unknown
    action verb is rejected *before* the watch starts (PS-102 §5.1).
    """
    if not isinstance(criteria, Mapping):
        raise InvalidCriteria("criteria must be a mapping")
    unknown = set(criteria) - _KNOWN_CRITERIA
    if unknown:
        raise InvalidCriteria(
            f"unsupported criteria field(s): {', '.join(sorted(unknown))}; "
            f"supported: {', '.join(sorted(_KNOWN_CRITERIA))}"
        )
    # action verbs must be from the canonical set
    actions = criteria.get("action")
    if actions is not None:
        for verb in _as_list(actions):
            if verb not in ACTIONS:
                raise InvalidCriteria(
                    f"unknown action verb {verb!r}; valid: {', '.join(sorted(ACTIONS))}"
                )
    # compile any regex patterns eagerly to surface bad patterns now
    for pattern_field in ("ref", "path", "author"):
        raw = criteria.get(pattern_field)
        if isinstance(raw, str) and raw.startswith(_REGEX_PREFIX):
            _compile_regex(raw)


def match(criteria: Mapping[str, Any], candidate: ChangeCandidate) -> dict[str, Any] | None:
    """Return a ``criteria_match`` mapping if the candidate matches, else ``None``.

    An empty ``criteria`` mapping matches everything and returns ``{"all": True}``
    so the envelope's ``criteria_match`` is never empty (CSTREAM-004). When any
    criterion fails, the whole watch does NOT match and ``None`` is returned.
    """
    if not criteria:
        return {"all": True}

    matched: dict[str, Any] = {}

    # action verb — single or list
    if "action" in criteria:
        wanted = _as_list(criteria["action"])
        if candidate.action not in wanted:
            return None
        matched["action"] = candidate.action

    # branch — exact short-name; must be a branch ref
    if "branch" in criteria:
        wanted = {str(b) for b in _as_list(criteria["branch"])}
        if candidate.ref_type != "branch" or candidate.short_ref not in wanted:
            return None
        matched["branch"] = candidate.short_ref

    # tag — exact short-name; must be a tag ref
    if "tag" in criteria:
        wanted = {str(t) for t in _as_list(criteria["tag"])}
        if candidate.ref_type != "tag" or candidate.short_ref not in wanted:
            return None
        matched["tag"] = candidate.short_ref

    # ref — glob or regex over fully-qualified OR short ref
    if "ref" in criteria:
        pattern = str(criteria["ref"])
        hit = _text_match(pattern, candidate.ref) or _text_match(pattern, candidate.short_ref)
        if hit is None:
            return None
        matched["ref"] = hit

    # author — glob or regex over commit author (name or email)
    if "author" in criteria:
        hit = _text_match(str(criteria["author"]), candidate.author or "")
        if hit is None:
            return None
        matched["author"] = hit

    # path — glob or regex; ANY changed path in the change must match
    if "path" in criteria:
        pattern = str(criteria["path"])
        hit_path = _first_path_match(pattern, candidate.paths)
        if hit_path is None:
            return None
        matched["path"] = hit_path

    return matched


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _compile_regex(raw: str) -> re.Pattern[str]:
    pattern = raw[len(_REGEX_PREFIX):]
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise InvalidCriteria(f"invalid regex {pattern!r}: {exc}") from exc


def _text_match(pattern: str, value: str) -> str | None:
    """Return the matched value/substring when ``pattern`` matches ``value``.

    ``re:`` prefix -> regex ``search``; otherwise a case-sensitive ``fnmatch``
    glob. Returns ``None`` on no match.
    """
    if pattern.startswith(_REGEX_PREFIX):
        compiled = _compile_regex(pattern)
        m = compiled.search(value or "")
        return m.group(0) if m is not None else None
    if fnmatch.fnmatchcase(value or "", pattern):
        return value
    return None


def _first_path_match(pattern: str, paths: Sequence[str]) -> str | None:
    """Return the first changed path matching ``pattern`` (glob or ``re:`` regex)."""
    for path in paths:
        hit = _text_match(pattern, str(path))
        if hit is not None:
            return str(path)
    return None
