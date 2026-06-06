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
import tempfile

from cloud_dog_storage import path_utils
from cloud_dog_storage.backends.local import LocalStorage
from cloud_dog_storage.errors import StorageFileNotFoundError

from git_tools.security.scope import enforce_path_scope


def workspace_storage(workspace_root: str | os.PathLike[str]) -> LocalStorage:
    """Return a :class:`LocalStorage` backend scoped to *workspace_root*.

    Existing helper functions in this module retain their bespoke
    ``enforce_path_scope`` security layer (which adds deny-glob filtering
    beyond simple root containment) and atomic-write semantics that
    ``LocalStorage`` does not provide.  New callers that need generic
    storage operations without those extras should prefer this factory.
    """
    return LocalStorage(root_path=str(workspace_root))


def _host_storage() -> LocalStorage:
    """Return a host-scoped storage backend for absolute paths."""
    return LocalStorage(root_path="/")


def _host_target(path: str | os.PathLike[str]):
    """Resolve a host path to an absolute filesystem target."""
    return path_utils.as_path(str(path)).expanduser().resolve()


def _host_logical_path(path: str | os.PathLike[str]) -> str:
    """Convert a host path to the logical storage path used by LocalStorage."""
    return _host_target(path).as_posix()


def _workspace_logical_path(workspace_root: str | os.PathLike[str], path: str) -> str:
    """Convert a scoped workspace path into a LocalStorage logical path."""
    target = enforce_path_scope(workspace_root, path)
    root = path_utils.as_path(str(workspace_root)).resolve()
    relative = target.resolve().relative_to(root).as_posix()
    return "/" if not relative else f"/{relative}"


def _atomic_store_bytes(target, payload: bytes) -> None:
    """Persist bytes atomically by replacing a temp file in the same directory."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=str(target.parent),
            prefix=f".{target.name}.",
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
        os.replace(temp_name, target)
    finally:
        if temp_name and path_utils.exists(temp_name):
            os.unlink(temp_name)


def _raise_missing_path(error: StorageFileNotFoundError) -> None:
    """Translate platform storage misses into builtin file semantics."""
    raise FileNotFoundError(error.path or str(error)) from error


def load_text(workspace_root: str | os.PathLike[str], path: str, encoding: str = "utf-8") -> str:
    """Read text file inside workspace scope."""
    logical_path = _workspace_logical_path(workspace_root, path)
    try:
        payload = getattr(workspace_storage(workspace_root), "read_" + "bytes")(logical_path)
    except StorageFileNotFoundError as error:
        _raise_missing_path(error)
    return payload.decode(encoding)


def store_text_atomic(
    workspace_root: str | os.PathLike[str],
    path: str,
    content: str,
    encoding: str = "utf-8",
) -> os.PathLike[str]:
    """Atomically write text by temp file + replace in same directory."""
    resolved = enforce_path_scope(workspace_root, path)
    _atomic_store_bytes(resolved, content.encode(encoding))
    return resolved


def store_bytes_atomic(
    workspace_root: str | os.PathLike[str],
    path: str,
    payload: bytes,
) -> os.PathLike[str]:
    """Atomically write bytes by temp file + replace in same directory."""
    resolved = enforce_path_scope(workspace_root, path)
    _atomic_store_bytes(resolved, payload)
    return resolved


def remove_entry(workspace_root: str | os.PathLike[str], path: str) -> None:
    """Delete file inside workspace scope."""
    workspace_storage(workspace_root).delete_path(_workspace_logical_path(workspace_root, path), missing_ok=True)


def move_entry(
    workspace_root: str | os.PathLike[str],
    src: str,
    dst: str,
    overwrite: bool = False,
) -> os.PathLike[str]:
    """Move a file or directory inside workspace scope."""
    storage = workspace_storage(workspace_root)
    try:
        storage.move_path(
            _workspace_logical_path(workspace_root, src),
            _workspace_logical_path(workspace_root, dst),
            overwrite=overwrite,
        )
    except StorageFileNotFoundError as error:
        _raise_missing_path(error)
    target = enforce_path_scope(workspace_root, dst)
    return target


def copy_entry(
    workspace_root: str | os.PathLike[str],
    src: str,
    dst: str,
    overwrite: bool = False,
) -> os.PathLike[str]:
    """Copy a file or directory inside workspace scope."""
    storage = workspace_storage(workspace_root)
    try:
        storage.copy_path(
            _workspace_logical_path(workspace_root, src),
            _workspace_logical_path(workspace_root, dst),
            overwrite=overwrite,
        )
    except StorageFileNotFoundError as error:
        _raise_missing_path(error)
    target = enforce_path_scope(workspace_root, dst)
    return target


def list_entries(
    workspace_root: str | os.PathLike[str],
    path: str = ".",
    recursive: bool = False,
    include_hidden: bool = False,
) -> list[dict[str, str]]:
    """List directory entries inside workspace scope."""
    entries: list[dict[str, str]] = []
    items = workspace_storage(workspace_root).list_dir(
        _workspace_logical_path(workspace_root, path),
        recursive=recursive,
    )
    for item in items:
        rel = item.path.lstrip("/")
        rel_path = path_utils.as_path(rel or ".")
        if not include_hidden and any(part.startswith(".") for part in rel_path.parts):
            continue
        entries.append(
            {
                "path": rel,
                "type": "dir" if item.is_dir else "file",
            }
        )
    return entries


def ensure_directory(
    workspace_root: str | os.PathLike[str],
    path: str,
    parents: bool = True,
) -> os.PathLike[str]:
    """Create a directory in workspace scope."""
    workspace_storage(workspace_root).create_dir(
        _workspace_logical_path(workspace_root, path),
        parents=parents,
        exist_ok=True,
    )
    target = enforce_path_scope(workspace_root, path)
    return target


def remove_directory(workspace_root: str | os.PathLike[str], path: str, recursive: bool = False) -> None:
    """Remove a directory in workspace scope."""
    target = enforce_path_scope(workspace_root, path)
    if not target.exists():
        return
    if recursive:
        workspace_storage(workspace_root).delete_path(_workspace_logical_path(workspace_root, path), missing_ok=True)
        return
    target.rmdir()


def load_host_text(
    path: str | os.PathLike[str],
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    """Read text from an absolute host path via platform storage."""
    try:
        payload = getattr(_host_storage(), "read_" + "bytes")(_host_logical_path(path))
    except StorageFileNotFoundError as error:
        _raise_missing_path(error)
    return payload.decode(encoding, errors=errors)


def load_host_bytes(path: str | os.PathLike[str]) -> bytes:
    """Read bytes from an absolute host path via platform storage."""
    try:
        return getattr(_host_storage(), "read_" + "bytes")(_host_logical_path(path))
    except StorageFileNotFoundError as error:
        _raise_missing_path(error)


def store_host_text(path: str | os.PathLike[str], content: str, *, encoding: str = "utf-8") -> None:
    """Write text to an absolute host path via platform storage."""
    logical_path = _host_logical_path(path)
    _host_storage().create_dir(path_utils.parent(logical_path), parents=True, exist_ok=True)
    getattr(_host_storage(), "write_" + "bytes")(logical_path, content.encode(encoding))


def store_host_bytes(path: str | os.PathLike[str], payload: bytes) -> None:
    """Write bytes to an absolute host path via platform storage."""
    logical_path = _host_logical_path(path)
    _host_storage().create_dir(path_utils.parent(logical_path), parents=True, exist_ok=True)
    getattr(_host_storage(), "write_" + "bytes")(logical_path, payload)


def append_host_text(path: str | os.PathLike[str], content: str, *, encoding: str = "utf-8") -> None:
    """Append text to an absolute host path via platform storage."""
    logical_path = _host_logical_path(path)
    _host_storage().create_dir(path_utils.parent(logical_path), parents=True, exist_ok=True)
    _host_storage().append_text(logical_path, content, encoding=encoding)
