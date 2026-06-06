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

REQUIREMENT_TRACEABILITY: dict[str, dict[str, object]] = {
    "UC-01": {"modules": ["git_tools.tools.registry", "git_tools.git.operations"], "tests": ["AT1.1"]},
    "UC-02": {"modules": ["git_tools.files.search", "git_tools.files.edit.text"], "tests": ["UT1.22", "AT1.1"]},
    "UC-03": {"modules": ["git_tools.workspaces.ref_context", "git_tools.security.scope"], "tests": ["AT1.2"]},
    "UC-04": {"modules": ["git_tools.git.operations", "git_tools.tools.registry"], "tests": ["ST1.4", "AT1.2"]},
    "UC-05": {"modules": ["git_tools.git.conflicts", "git_tools.git.operations"], "tests": ["AT1.3"]},
    "UC-06": {"modules": ["git_tools.git.recovery", "git_tools.audit.logger"], "tests": ["ST1.8", "AT1.5"]},
    "UC-07": {"modules": ["git_mcp_server.admin.endpoints", "git_tools.security.rbac"], "tests": ["AT1.4"]},
    "FR-01": {
        "modules": [
            "git_mcp_server.api_server",
            "git_mcp_server.jobs.endpoints",
            "git_mcp_server.mcp_server",
            "git_tools.jobs.runtime",
        ],
        "tests": ["IT1.1", "IT1.5", "IT1.6", "IT1.15", "UT1.55"],
    },
    "FR-02": {
        "modules": ["git_mcp_server.logging", "git_tools.config.loader", "git_tools.config.models"],
        "tests": ["UT1.1", "UT1.2", "UT1.3"],
    },
    "FR-03": {
        "modules": ["git_tools.workspaces.manager", "git_tools.config.models"],
        "tests": ["UT1.4", "ST1.1", "ST1.2"],
    },
    "FR-04": {
        "modules": ["git_mcp_server.auth.middleware", "git_mcp_server.api_server"],
        "tests": ["UT1.26", "IT1.2", "IT1.3", "IT1.11", "AT1.6"],
    },
    "FR-05": {
        "modules": ["git_tools.security.rbac", "git_mcp_server.admin.endpoints"],
        "tests": ["UT1.10", "UT1.11", "IT1.4", "AT1.4"],
    },
    "FR-06": {
        "modules": ["git_tools.security.git_auth", "git_tools.audit.logger"],
        "tests": ["QT1.1", "IT1.9", "IT1.10", "IT1.16"],
    },
    "FR-07": {
        "modules": ["git_tools.workspaces.ref_context", "git_tools.security.scope"],
        "tests": ["UT1.5", "UT1.6", "UT1.7", "IT1.7", "AT1.2"],
    },
    "FR-08": {
        "modules": ["git_tools.files", "git_tools.files.io", "git_tools.files.search"],
        "tests": ["UT1.21", "UT1.22", "AT1.1"],
    },
    "FR-09": {"modules": ["git_tools.files.edit.json_yaml", "git_tools.files.validate"], "tests": ["UT1.23", "UT1.24"]},
    "FR-10": {
        "modules": ["git_tools.git.operations", "git_tools.git.repo"],
        "tests": [
            "UT1.14",
            "UT1.15",
            "UT1.16",
            "UT1.17",
            "UT1.18",
            "UT1.19",
            "UT1.20",
            "ST1.3",
            "ST1.5",
            "ST1.6",
            "ST1.7",
            "IT1.9",
            "IT1.10",
            "IT1.16",
        ],
    },
    "FR-11": {"modules": ["git_tools.git.tags", "git_tools.tools.definitions"], "tests": ["UT1.17", "ST1.4"]},
    "FR-12": {
        "modules": ["git_tools.git.conflicts", "git_tools.git.operations"],
        "tests": ["UT1.18", "UT1.19", "AT1.3"],
    },
    "FR-13": {
        "modules": ["git_tools.git.recovery", "git_tools.workspaces.manager"],
        "tests": ["UT1.20", "ST1.8", "AT1.5"],
    },
    "FR-14": {
        "modules": ["git_mcp_server.logging", "git_tools.audit.events", "git_tools.audit.logger", "git_tools.jobs.runtime"],
        "tests": ["UT1.12", "UT1.13", "UT1.55", "ST1.10", "IT1.8", "IT1.15"],
    },
    "FR-15": {"modules": ["git_mcp_server.admin.endpoints", "git_tools.security.rbac"], "tests": ["AT1.4"]},
    "FR-16": {
        "modules": ["git_mcp_server.admin.endpoints", "git_mcp_server.api_server", "git_mcp_server.web_ui"],
        "tests": ["AT1.4", "QT2.5", "UT1.56"],
    },
    "FR-17": {
        "modules": ["git_mcp_server.admin.endpoints", "git_mcp_server.web_ui", "git_tools.db.runtime"],
        "tests": ["UT1.27", "UT1.56", "ST1.11a", "ST1.11b", "QT2.5"],
    },
    "CFG-06": {
        "modules": ["git_mcp_server.api_server", "git_tools.admin.runtime"],
        "tests": ["IT1.13", "QT2.5"],
    },
    "CFG-07": {
        "modules": ["git_mcp_server.admin.endpoints", "git_mcp_server.api_server"],
        "tests": ["IT1.14", "QT2.5"],
    },
    "CFG-08": {
        "modules": ["git_mcp_server.admin.endpoints", "git_tools.admin.runtime", "git_tools.tools.registry"],
        "tests": ["UT1.54", "IT1.14", "QT2.5"],
    },
    "CFG-09": {
        "modules": ["git_mcp_server.admin.endpoints", "git_tools.admin.runtime", "git_tools.tools.registry"],
        "tests": ["UT1.54", "IT1.14", "QT2.5"],
    },
    "CFG-10": {
        "modules": ["git_mcp_server.admin.endpoints", "git_tools.admin.runtime", "git_tools.tools.registry"],
        "tests": ["UT1.54", "IT1.14", "QT2.5"],
    },
    "CFG-11": {
        "modules": ["git_mcp_server.api_server", "git_tools.admin.runtime", "git_tools.tools.registry"],
        "tests": ["UT1.54", "IT1.13", "IT1.14", "QT2.5"],
    },
    "NFR-01": {"modules": ["git_tools.files.io"], "tests": ["UT1.21"]},
    "NFR-02": {"modules": ["git_tools.security.scope", "git_tools.security.rbac"], "tests": ["QT1.2", "UT1.9"]},
    "NFR-03": {"modules": ["git_tools.files.edit.json_yaml"], "tests": ["UT1.23", "UT1.35", "UT1.36"]},
    "NFR-04": {"modules": ["git_tools.config.models", "git_tools.git.operations"], "tests": ["UT1.15", "IT1.9"]},
    "NFR-05": {"modules": ["git_tools.audit.logger", "git_mcp_server.api_server"], "tests": ["ST1.10", "IT1.8"]},
    "NFR-06": {
        "modules": ["git_tools.tools.registry", "git_mcp_server.api_server", "git_mcp_server.mcp_server"],
        "tests": ["QT2.6"],
    },
    "NFR-07": {"modules": ["git_tools.config.loader", "git_mcp_server.api_server"], "tests": ["UT1.1", "QT2.5"]},
}
