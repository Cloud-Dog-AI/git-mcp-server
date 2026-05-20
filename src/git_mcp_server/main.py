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

import argparse

from git_mcp_server.a2a_server import run_a2a
from git_mcp_server.api_server import run_api
from git_mcp_server.mcp_server import run_mcp
from git_mcp_server.web_server import run_web

# W28A-654: Patch cloud_dog_logging ContextVar defaults at module import time.
# ContextVars are task-scoped in asyncio — set_environment() in one task does NOT
# propagate to AuditMiddleware in another. Patching defaults ensures all tasks inherit.
try:
    import contextvars as _ctxvars
    from cloud_dog_logging import correlation as _cmod
    _cmod._environment_var = _ctxvars.ContextVar(
        "environment", default="unknown")
    _cmod._service_name_var = _ctxvars.ContextVar(
        "service_name", default="git-mcp-server")
    _cmod._service_instance_var = _ctxvars.ContextVar(
        "service_instance", default="git-mcp-local")
    del _ctxvars, _cmod
except Exception:
    pass  # cloud_dog_logging not installed or incompatible version



def parse_args() -> argparse.Namespace:
    """Parse entrypoint CLI arguments."""
    parser = argparse.ArgumentParser(description="git-mcp-server entrypoint")
    parser.add_argument("--env", action="append", default=[], help="Optional env file(s) passed to cloud_dog_config")
    parser.add_argument("--server", choices=["api", "web", "mcp", "a2a"], default="api", help="Server mode to run")
    return parser.parse_args()


def main() -> None:
    """Run selected server."""
    args = parse_args()
    env_files = list(args.env) if args.env else None
    if args.server == "web":
        run_web(env_files=env_files)
        return
    if args.server == "mcp":
        run_mcp(env_files=env_files)
        return
    if args.server == "a2a":
        run_a2a(env_files=env_files)
        return
    run_api(env_files=env_files)


if __name__ == "__main__":
    main()
