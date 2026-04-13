"""Tests for TASK-006: Visual builder agent and build-ui command."""

import os
import pathlib
import subprocess
import sys
import tempfile

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPANION = PROJECT_ROOT / "scripts" / "kimi-companion.py"


def run_companion(*args, env_override=None):
    """Run the companion script with given args, return (stdout, stderr, returncode)."""
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    result = subprocess.run(
        [sys.executable, str(COMPANION)] + list(args),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


class TestVisualBuilderYaml:
    """Tests for agents/visual-builder.yaml."""

    def test_visual_builder_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_visual_builder_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_visual_builder_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "name: visual-builder" in content

    def test_visual_builder_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "visual-builder-system.md" in content

    def test_visual_builder_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_visual_builder_yaml_has_writefile_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:WriteFile" in content

    def test_visual_builder_yaml_has_strreplacefile_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:StrReplaceFile" in content

    def test_visual_builder_yaml_has_shell_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.shell:Shell" in content

    def test_visual_builder_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content

    def test_visual_builder_yaml_has_grep_tool(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Grep" in content

    def test_visual_builder_yaml_no_agent_tool(self):
        """Visual builder is single-agent -- no Agent tool."""
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" not in content

    def test_visual_builder_yaml_no_subagents(self):
        path = PROJECT_ROOT / "agents" / "visual-builder.yaml"
        content = path.read_text()
        assert "subagents:" not in content


class TestVisualBuilderSystemPrompt:
    """Tests for agents/visual-builder-system.md."""

    def test_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_system_prompt_mentions_analyze_step(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "analyze" in content.lower() or "Analyze" in content

    def test_system_prompt_mentions_build_step(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "build" in content.lower() or "Build" in content

    def test_system_prompt_mentions_screenshot_step(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "screenshot" in content.lower() or "Screenshot" in content

    def test_system_prompt_mentions_compare_step(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "compare" in content.lower() or "Compare" in content

    def test_system_prompt_mentions_iterate_step(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "iterate" in content.lower() or "round" in content.lower()

    def test_system_prompt_mentions_5_rounds(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "5" in content

    def test_system_prompt_mentions_files_changed(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "files_changed" in content

    def test_system_prompt_mentions_screenshots(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "screenshots" in content or "screenshot" in content.lower()

    def test_system_prompt_mentions_localhost_constraint(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "localhost" in content

    def test_system_prompt_mentions_existing_stack(self):
        path = PROJECT_ROOT / "agents" / "visual-builder-system.md"
        content = path.read_text()
        assert "existing" in content.lower()


class TestBuildUiCommand:
    """Tests for commands/build-ui.md."""

    def test_build_ui_command_exists(self):
        path = PROJECT_ROOT / "commands" / "build-ui.md"
        assert path.is_file(), f"{path} does not exist"

    def test_build_ui_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "build-ui.md"
        content = path.read_text()
        assert "description:" in content

    def test_build_ui_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "build-ui.md"
        content = path.read_text()
        assert "argument-hint:" in content
        assert "image" in content.lower()

    def test_build_ui_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "build-ui.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_build_ui_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "build-ui.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestBuildUiSubcommand:
    """Tests for the build-ui subcommand."""

    def test_build_ui_no_args_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "build-ui", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1
            assert len(stderr) > 0

    def test_build_ui_resolves_agent_yaml(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("build-ui")
            assert agent_path.is_file()
            assert agent_path.name == "visual-builder.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
