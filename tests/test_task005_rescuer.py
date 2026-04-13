"""Tests for TASK-005: Rescuer agent, rescue command, and companion handler."""

import json
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


class TestRescuerYaml:
    """Tests for agents/rescuer.yaml."""

    def test_rescuer_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_rescuer_yaml_is_valid_yaml(self):
        import importlib
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        # Basic YAML validation: must contain key fields
        assert "version:" in content
        assert "agent:" in content

    def test_rescuer_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_rescuer_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "name: rescuer" in content

    def test_rescuer_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "rescuer-system.md" in content

    def test_rescuer_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_rescuer_yaml_has_writefile_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:WriteFile" in content

    def test_rescuer_yaml_has_strreplacefile_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:StrReplaceFile" in content

    def test_rescuer_yaml_has_shell_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.shell:Shell" in content

    def test_rescuer_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content

    def test_rescuer_yaml_has_grep_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Grep" in content

    def test_rescuer_yaml_has_searchweb_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.web:SearchWeb" in content

    def test_rescuer_yaml_has_fetchurl_tool(self):
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.web:FetchURL" in content

    def test_rescuer_yaml_no_agent_tool(self):
        """Rescuer is single-agent — should NOT have the Agent tool."""
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" not in content

    def test_rescuer_yaml_no_subagents(self):
        """Rescuer is single-agent — should have no subagents block."""
        path = PROJECT_ROOT / "agents" / "rescuer.yaml"
        content = path.read_text()
        assert "subagents:" not in content


class TestRescuerSystemPrompt:
    """Tests for agents/rescuer-system.md."""

    def test_rescuer_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_rescuer_system_prompt_mentions_agents_md(self):
        """System prompt should instruct reading AGENTS.md/CLAUDE.md if present."""
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "AGENTS.md" in content or "CLAUDE.md" in content

    def test_rescuer_system_prompt_mentions_json_output(self):
        """System prompt should instruct returning structured JSON."""
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "json" in content.lower() or "JSON" in content

    def test_rescuer_system_prompt_mentions_status_field(self):
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "status" in content

    def test_rescuer_system_prompt_mentions_summary_field(self):
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "summary" in content

    def test_rescuer_system_prompt_mentions_files_changed(self):
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "files_changed" in content

    def test_rescuer_system_prompt_mentions_remaining_issues(self):
        path = PROJECT_ROOT / "agents" / "rescuer-system.md"
        content = path.read_text()
        assert "remaining_issues" in content


class TestRescueCommand:
    """Tests for commands/rescue.md."""

    def test_rescue_command_exists(self):
        path = PROJECT_ROOT / "commands" / "rescue.md"
        assert path.is_file(), f"{path} does not exist"

    def test_rescue_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "rescue.md"
        content = path.read_text()
        assert "description:" in content

    def test_rescue_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "rescue.md"
        content = path.read_text()
        assert "argument-hint:" in content
        assert "--background" in content or "--wait" in content

    def test_rescue_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "rescue.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_rescue_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "rescue.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestRescueSubcommand:
    """Tests for the rescue subcommand in the companion script."""

    def test_rescue_no_args_errors(self):
        """rescue without a task description should error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "rescue", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1
            assert len(stderr) > 0

    def test_rescue_missing_task_description_gives_usage(self):
        """rescue without args should mention usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "rescue", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_rescue_resolves_agent_yaml(self):
        """rescue should resolve the rescuer.yaml agent file."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("rescue")
            assert agent_path.is_file()
            assert agent_path.name == "rescuer.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
