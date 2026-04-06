from pathlib import Path
from unittest.mock import Mock

import tomllib

from victor_sdk import VictorPlugin

from victor_coding.assistant import CodingAssistant
from victor_coding.plugin import CodingPlugin, plugin


def _entry_points() -> dict:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["project"]["entry-points"]


def test_pyproject_registers_plugin_instance_entry_point() -> None:
    entry_points = _entry_points()

    assert entry_points["victor.plugins"]["coding"] == "victor_coding.plugin:plugin"


def test_pyproject_registers_canonical_runtime_extension_entry_points() -> None:
    entry_points = _entry_points()

    assert entry_points["victor.prompt_contributors"]["coding"] == (
        "victor_coding.prompts:CodingPromptContributor"
    )
    assert entry_points["victor.mode_configs"]["coding"] == (
        "victor_coding.mode_config:CodingModeConfigProvider"
    )
    assert entry_points["victor.workflow_providers"]["coding"] == (
        "victor_coding.workflows.provider:CodingWorkflowProvider"
    )
    assert entry_points["victor.capability_providers"]["coding"] == (
        "victor_coding.capabilities:CodingCapabilityProvider"
    )
    assert entry_points["victor.service_providers"]["coding"] == (
        "victor_coding.service_provider:CodingServiceProvider"
    )
    assert entry_points["victor.team_spec_providers"]["coding"] == (
        "victor_coding.teams:CodingTeamSpecProvider"
    )
    assert entry_points["victor.framework.teams.providers"]["coding"] == (
        "victor_coding.teams:CodingTeamSpecProvider"
    )


def test_plugin_implements_protocol_and_registers_vertical() -> None:
    context = Mock()

    assert isinstance(plugin, VictorPlugin)
    assert isinstance(plugin, CodingPlugin)
    assert plugin.name == "coding"

    plugin.register(context)

    context.register_vertical.assert_called_once_with(CodingAssistant)
