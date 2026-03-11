# Copyright 2025 Vijaykumar Singh <singhvjd@gmail.com>
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

"""Victor SDK Protocol implementations for victor-coding.

This module provides protocol implementations that can be discovered via
the victor-sdk entry point system, enabling the coding vertical to
register capabilities with the framework without direct dependencies.

Entry Points:
    [project.entry-points."victor.sdk.protocols"]
    coding-tools = "victor_coding.protocols:CodingToolProvider"
    coding-safety = "victor_coding.protocols:CodingSafetyProvider"
    coding-prompts = "victor_coding.protocols:CodingPromptProvider"
    coding-workflows = "victor_coding.protocols:CodingWorkflowProvider"

    [project.entry-points."victor.sdk.capabilities"]
    coding-lsp = "victor_coding.protocols:LSPCapabilityProvider"
    coding-git = "victor_coding.protocols:GitCapabilityProvider"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Import victor-sdk protocols (NO runtime dependency on victor-ai!)
try:
    from victor_sdk.verticals.protocols import (
        ToolProvider,
        ToolSelectionStrategy,
        SafetyProvider,
        PromptProvider,
        WorkflowProvider,
    )
except ImportError:
    # For backward compatibility during transition
    try:
        from victor.core.verticals.protocols import (
            ToolProviderProtocol as ToolProvider,
            SafetyProviderProtocol as SafetyProvider,
            PromptProviderProtocol as PromptProvider,
            WorkflowProviderProtocol as WorkflowProvider,
        )
    except ImportError:
        # Create stub protocols if nothing is available
        from typing import Protocol

        class ToolProvider(Protocol):
            def get_tools(self) -> List[str]: ...

        class SafetyProvider(Protocol):
            def get_extensions(self) -> List[Any]: ...
            def get_bash_patterns(self) -> List[Any]: ...
            def get_file_patterns(self) -> List[Any]: ...
            def get_tool_restrictions(self) -> Dict[str, List[str]]: ...

        class PromptProvider(Protocol):
            def get_system_prompt_sections(self) -> Dict[str, str]: ...
            def get_task_type_hints(self) -> Dict[str, Any]: ...
            def get_prompt_contributors(self) -> List[Any]: ...

        class WorkflowProvider(Protocol):
            def get_workflows(self) -> Dict[str, Any]: ...
            def get_workflow(self, name: str) -> Optional[Any]: ...
            def list_workflows(self) -> List[str]: ...

# Try to import existing victor-coding implementations (may not exist in older versions)
try:
    from victor_coding.safety import CodingSafetyExtension
except ImportError:
    CodingSafetyExtension = None

try:
    from victor_coding.prompts import (
        CodingPromptContributor,
        CODING_TASK_TYPE_HINTS,
    )
except ImportError:
    CodingPromptContributor = None
    CODING_TASK_TYPE_HINTS = {}

try:
    from victor_coding.workflows.provider import CodingWorkflowProviderImpl
except ImportError:
    CodingWorkflowProviderImpl = None

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Provider
# =============================================================================


class CodingToolProvider(ToolProvider):
    """Tool provider for coding vertical.

    Provides the list of tools available to the coding assistant.
    """

    def get_tools(self) -> List[str]:
        """Return list of tool names for coding vertical."""
        return [
            # Core filesystem tools
            "read",
            "write",
            "edit",
            "search",
            "grep",
            "ls",
            "find",
            "tree",
            # Git tools
            "git_status",
            "git_diff",
            "git_log",
            "git_blame",
            "git_show",
            "git_branch",
            # Code analysis
            "symbol",
            "code_search",
            "ast_inspect",
            "lint",
            "format",
            # Testing
            "test",
            "test_coverage",
            # Execution
            "shell",
            "run_python",
            # Documentation
            "doc_gen",
            # Refactoring
            "rename",
            "extract",
            "inline",
        ]


class CodingToolSelectionStrategy(ToolSelectionStrategy):
    """Stage-aware tool selection for coding tasks."""

    def get_tools_for_stage(self, stage: str, task_type: str) -> List[str]:
        """Return optimized tools for given stage and task type."""
        # Stage-based tool selection
        stage_tools: Dict[str, List[str]] = {
            "understand": ["read", "grep", "ls", "code_search", "symbol"],
            "plan": ["read", "grep", "tree"],
            "implement": ["write", "edit", "shell"],
            "test": ["test", "test_coverage", "read"],
            "deploy": ["shell", "git_status", "git_diff"],
        }

        # Task-type enhancements
        task_enhancements: Dict[str, List[str]] = {
            "bug": ["lint", "git_blame", "git_show"],
            "feature": ["test", "doc_gen"],
            "refactor": ["rename", "extract", "inline"],
            "review": ["read", "lint", "format"],
        }

        tools = stage_tools.get(stage, [])

        # Add task-specific tools
        if task_type in task_enhancements:
            tools.extend(task_enhancements[task_type])

        return list(set(tools))  # Deduplicate


# =============================================================================
# Safety Provider
# =============================================================================


class CodingSafetyProvider(SafetyProvider):
    """Safety provider for coding vertical.

    Provides coding-specific safety patterns and extensions.
    """

    def __init__(self):
        self._extension = None
        if CodingSafetyExtension is not None:
            try:
                self._extension = CodingSafetyExtension()
            except Exception:
                pass

    def get_extensions(self) -> List[Any]:
        """Return safety extensions for coding."""
        if self._extension:
            return [self._extension]
        return []

    def get_bash_patterns(self) -> List[Any]:
        """Return bash command patterns to monitor."""
        if self._extension:
            try:
                return self._extension.get_bash_patterns()
            except Exception:
                pass
        return []

    def get_file_patterns(self) -> List[Any]:
        """Return file operation patterns to monitor."""
        if self._extension:
            try:
                return self._extension.get_file_patterns()
            except Exception:
                pass
        return []

    def get_tool_restrictions(self) -> Dict[str, List[str]]:
        """Return tool-specific restrictions."""
        if self._extension:
            try:
                return self._extension.get_tool_restrictions()
            except Exception:
                pass
        return {}


# =============================================================================
# Prompt Provider
# =============================================================================


class CodingPromptProvider(PromptProvider):
    """Prompt provider for coding vertical.

    Provides system prompt sections and task-type hints.
    """

    def __init__(self):
        self._contributor = None
        if CodingPromptContributor is not None:
            try:
                self._contributor = CodingPromptContributor()
            except Exception:
                pass

    def get_system_prompt_sections(self) -> Dict[str, str]:
        """Return system prompt sections."""
        if self._contributor:
            try:
                return self._contributor.get_system_prompt_sections()
            except Exception:
                pass

        # Default system prompt sections
        return {
            "role": "You are a coding assistant specializing in software development, debugging, and code generation.",
            "expertise": "You have expertise in Python, TypeScript, JavaScript, and many other programming languages.",
            "safety": "Always follow git safety best practices. Never force push to main branches without review.",
            "best_practices": "Follow clean code principles: meaningful names, small functions, DRY, SOLID.",
        }

    def get_task_type_hints(self) -> Dict[str, Any]:
        """Return task type hints for coding."""
        if CODING_TASK_TYPE_HINTS:
            return CODING_TASK_TYPE_HINTS

        # Default task type hints
        return {
            "code_generation": {
                "hint": "[GENERATE] Write code directly. No exploration needed.",
                "tool_budget": 3,
            },
            "create": {
                "hint": "[CREATE] Create new file. Minimal exploration.",
                "tool_budget": 3,
            },
            "edit": {
                "hint": "[EDIT] Read target file first, then modify.",
                "tool_budget": 5,
            },
            "search": {
                "hint": "[SEARCH] Use grep/ls for exploration.",
                "tool_budget": 6,
            },
            "test": {
                "hint": "[TEST] Run tests and verify functionality.",
                "tool_budget": 10,
            },
            "debug": {
                "hint": "[DEBUG] Investigate issues, check logs, fix bugs.",
                "tool_budget": 15,
            },
        }

    def get_prompt_contributors(self) -> List[Any]:
        """Return prompt contributors for coding."""
        if self._contributor:
            return [self._contributor]
        return []


# =============================================================================
# Workflow Provider
# =============================================================================


class CodingWorkflowProvider(WorkflowProvider):
    """Workflow provider for coding vertical.

    Provides coding-specific workflow definitions.
    """

    def __init__(self):
        self._provider = None
        if CodingWorkflowProviderImpl is not None:
            try:
                self._provider = CodingWorkflowProviderImpl()
            except Exception:
                pass

    def get_workflows(self) -> Dict[str, Any]:
        """Return workflow specifications."""
        if self._provider:
            try:
                return self._provider.get_workflows()
            except Exception:
                pass

        # Default workflow specifications
        return {
            "feature": {
                "name": "Feature Development",
                "description": "Implement a new feature",
                "stages": ["understand", "plan", "implement", "test"],
            },
            "bugfix": {
                "name": "Bug Fix",
                "description": "Fix a reported bug",
                "stages": ["understand", "plan", "implement", "test"],
            },
            "review": {
                "name": "Code Review",
                "description": "Review code changes",
                "stages": ["understand", "analyze"],
            },
            "refactor": {
                "name": "Refactoring",
                "description": "Refactor existing code",
                "stages": ["understand", "plan", "implement", "test"],
            },
        }

    def get_workflow(self, name: str) -> Optional[Any]:
        """Get a specific workflow by name."""
        workflows = self.get_workflows()
        return workflows.get(name)

    def list_workflows(self) -> List[str]:
        """List available workflow names."""
        return list(self.get_workflows().keys())


# =============================================================================
# Capability Providers (for victor.sdk.capabilities entry point)
# =============================================================================


class LSPCapabilityProvider:
    """LSP capability provider for coding vertical.

    Provides LSP (Language Server Protocol) capabilities.
    """

    def get_capability_name(self) -> str:
        return "lsp"

    def get_capability_config(self) -> Dict[str, Any]:
        return {
            "languages": ["python", "typescript", "javascript", "rust", "go"],
            "features": {
                "hover": True,
                "references": True,
                "symbols": True,
                "completion": True,
                "diagnostics": True,
            },
        }

    def configure_capability(self, orchestrator: Any) -> None:
        """Configure LSP capability on orchestrator."""
        # Implementation would configure LSP features
        pass


class GitCapabilityProvider:
    """Git capability provider for coding vertical.

    Provides Git operation capabilities.
    """

    def get_capability_name(self) -> str:
        return "git"

    def get_capability_config(self) -> Dict[str, Any]:
        return {
            "block_force_push": True,
            "block_main_push": True,
            "require_tests_before_commit": False,
        }

    def configure_capability(self, orchestrator: Any) -> None:
        """Configure Git capability on orchestrator."""
        # Implementation would configure Git safety rules
        pass


class CodeStyleCapabilityProvider:
    """Code style capability provider for coding vertical.

    Provides code formatting and linting capabilities.
    """

    def get_capability_name(self) -> str:
        return "code_style"

    def get_capability_config(self) -> Dict[str, Any]:
        return {
            "formatter": "black",
            "linter": "ruff",
            "max_line_length": 100,
            "enforce_type_hints": True,
        }

    def configure_capability(self, orchestrator: Any) -> None:
        """Configure code style capability on orchestrator."""
        # Implementation would configure code style settings
        pass


class TestingCapabilityProvider:
    """Testing capability provider for coding vertical.

    Provides testing and coverage capabilities.
    """

    def get_capability_name(self) -> str:
        return "testing"

    def get_capability_config(self) -> Dict[str, Any]:
        return {
            "min_coverage": 0.0,
            "required_patterns": [],
            "framework": "pytest",
            "run_on_edit": False,
        }

    def configure_capability(self, orchestrator: Any) -> None:
        """Configure testing capability on orchestrator."""
        # Implementation would configure testing settings
        pass


class RefactoringCapabilityProvider:
    """Refactoring capability provider for coding vertical.

    Provides code refactoring capabilities.
    """

    def get_capability_name(self) -> str:
        return "refactoring"

    def get_capability_config(self) -> Dict[str, Any]:
        return {
            "operations": {
                "rename": True,
                "extract": True,
                "inline": True,
            },
            "require_tests": True,
        }

    def configure_capability(self, orchestrator: Any) -> None:
        """Configure refactoring capability on orchestrator."""
        # Implementation would configure refactoring settings
        pass


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Tool providers
    "CodingToolProvider",
    "CodingToolSelectionStrategy",
    # Safety providers
    "CodingSafetyProvider",
    # Prompt providers
    "CodingPromptProvider",
    # Workflow providers
    "CodingWorkflowProvider",
    # Capability providers
    "LSPCapabilityProvider",
    "GitCapabilityProvider",
    "CodeStyleCapabilityProvider",
    "TestingCapabilityProvider",
    "RefactoringCapabilityProvider",
]
