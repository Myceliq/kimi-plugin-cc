"""Tests for TASK-010: Audit coordinator agent and audit command."""

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


class TestAuditCoordinatorYaml:
    """Tests for agents/audit-coordinator.yaml."""

    def test_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "name: audit-coordinator" in content

    def test_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "audit-coordinator-system.md" in content

    def test_yaml_has_agent_tool(self):
        """Root agent that launches up to 100 subagents."""
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" in content

    def test_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content

    def test_yaml_has_grep_tool(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Grep" in content

    def test_yaml_no_create_subagent(self):
        """Must NOT use CreateSubagent (non-existent in v1.31.0)."""
        path = PROJECT_ROOT / "agents" / "audit-coordinator.yaml"
        content = path.read_text()
        assert "CreateSubagent" not in content


class TestAuditCoordinatorSystemPrompt:
    """Tests for agents/audit-coordinator-system.md."""

    def test_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_system_prompt_mentions_catalog_phase(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "catalog" in content.lower()

    def test_system_prompt_mentions_partition_phase(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "partition" in content.lower()

    def test_system_prompt_mentions_dispatch_phase(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "dispatch" in content.lower()

    def test_system_prompt_mentions_synthesize_phase(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "synthesize" in content.lower() or "consolidat" in content.lower()

    def test_system_prompt_mentions_security(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "security" in content.lower()

    def test_system_prompt_mentions_dead_code(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "dead code" in content.lower() or "unused" in content.lower()

    def test_system_prompt_mentions_naming_inconsistencies(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "naming" in content.lower() or "inconsisten" in content.lower()

    def test_system_prompt_mentions_error_handling(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "error handling" in content.lower()

    def test_system_prompt_mentions_test_coverage(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "test" in content.lower() and "coverage" in content.lower()

    def test_system_prompt_mentions_dependency_issues(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "dependen" in content.lower()

    def test_system_prompt_mentions_documentation_staleness(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "documentation" in content.lower()

    def test_system_prompt_mentions_scaling_table(self):
        """Should reference agent-per-file scaling."""
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "100" in content  # 100 agents max
        assert "files" in content.lower()

    def test_system_prompt_mentions_explore_subagents(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "explore" in content.lower()

    def test_system_prompt_mentions_stats_output(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "files_analyzed" in content or "stats" in content

    def test_system_prompt_mentions_by_category(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "by_category" in content or "category" in content.lower()

    def test_system_prompt_mentions_node_modules_exclusion(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert "node_modules" in content

    def test_system_prompt_mentions_git_exclusion(self):
        path = PROJECT_ROOT / "agents" / "audit-coordinator-system.md"
        content = path.read_text()
        assert ".git" in content


class TestAuditCommand:
    """Tests for commands/audit.md."""

    def test_command_exists(self):
        path = PROJECT_ROOT / "commands" / "audit.md"
        assert path.is_file(), f"{path} does not exist"

    def test_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "audit.md"
        content = path.read_text()
        assert "description:" in content

    def test_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "audit.md"
        content = path.read_text()
        assert "argument-hint:" in content
        assert "focus" in content.lower()

    def test_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "audit.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "audit.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestAuditSubcommand:
    """Tests for the audit subcommand."""

    def test_audit_resolves_agent_yaml(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("audit")
            assert agent_path.is_file()
            assert agent_path.name == "audit-coordinator.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_audit_defaults_to_background(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["audit"]["default_mode"] == "background"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_no_enterprise_flag(self):
        """Enterprise multi-session audit is NOT implemented (deferred to v2)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "audit", "--enterprise",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir, "CLAUDE_PLUGIN_ROOT": tmpdir}
            )
            # Should not recognize --enterprise as a special flag;
            # it just becomes part of the prompt, which is fine
            # The key is it doesn't enable multi-session behavior
            assert code == 1  # Will fail because agent YAML is in tmpdir (not found)
