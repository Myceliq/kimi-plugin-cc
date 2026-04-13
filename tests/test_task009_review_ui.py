"""Tests for TASK-009: Review-UI agent and review-ui command."""

import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestReviewUiYaml:
    """Tests for agents/review-ui.yaml."""

    def test_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "name: review-ui" in content

    def test_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "review-ui-system.md" in content

    def test_yaml_has_agent_tool(self):
        """Root agent that launches visual reviewer subagents."""
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" in content

    def test_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_yaml_has_shell_tool(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.shell:Shell" in content

    def test_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "review-ui.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content


class TestReviewUiSystemPrompt:
    """Tests for agents/review-ui-system.md."""

    def test_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_system_prompt_mentions_visual_polish(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "visual" in content.lower()

    def test_system_prompt_mentions_accessibility(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "accessibility" in content.lower()

    def test_system_prompt_mentions_responsiveness(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "responsiv" in content.lower()

    def test_system_prompt_mentions_ux_heuristics(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "ux" in content.lower() or "heuristic" in content.lower()

    def test_system_prompt_mentions_viewport_widths(self):
        """Should mention mobile/tablet/desktop viewport widths."""
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "375" in content or "mobile" in content.lower()
        assert "768" in content or "tablet" in content.lower()
        assert "1440" in content or "desktop" in content.lower()

    def test_system_prompt_mentions_explore_subagents(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "explore" in content.lower()

    def test_system_prompt_mentions_screenshots(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "screenshot" in content.lower()

    def test_system_prompt_mentions_moonvit(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "moonvit" in content.lower() or "vision" in content.lower()

    def test_system_prompt_mentions_severity(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "severity" in content

    def test_system_prompt_mentions_findings(self):
        path = PROJECT_ROOT / "agents" / "review-ui-system.md"
        content = path.read_text()
        assert "findings" in content


class TestReviewUiCommand:
    """Tests for commands/review-ui.md."""

    def test_command_exists(self):
        path = PROJECT_ROOT / "commands" / "review-ui.md"
        assert path.is_file(), f"{path} does not exist"

    def test_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "review-ui.md"
        content = path.read_text()
        assert "description:" in content

    def test_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "review-ui.md"
        content = path.read_text()
        assert "argument-hint:" in content

    def test_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "review-ui.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "review-ui.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestReviewUiSubcommand:
    """Tests for the review-ui subcommand."""

    def test_review_ui_resolves_agent_yaml(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("review-ui")
            assert agent_path.is_file()
            assert agent_path.name == "review-ui.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
