"""Tests for TASK-007: Swarm reviewer agent and swarm-review command."""

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


class TestSwarmReviewerYaml:
    """Tests for agents/swarm-reviewer.yaml."""

    def test_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "name: swarm-reviewer" in content

    def test_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "swarm-reviewer-system.md" in content

    def test_yaml_has_agent_tool(self):
        """Swarm reviewer is a root agent that launches subagents."""
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" in content

    def test_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content

    def test_yaml_has_grep_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Grep" in content

    def test_yaml_no_create_subagent(self):
        """Must NOT use CreateSubagent (non-existent in v1.31.0)."""
        path = PROJECT_ROOT / "agents" / "swarm-reviewer.yaml"
        content = path.read_text()
        assert "CreateSubagent" not in content


class TestSwarmReviewerSystemPrompt:
    """Tests for agents/swarm-reviewer-system.md."""

    def test_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_system_prompt_mentions_security(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "security" in content.lower() or "Security" in content

    def test_system_prompt_mentions_performance(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "performance" in content.lower() or "Performance" in content

    def test_system_prompt_mentions_correctness(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "correctness" in content.lower() or "Correctness" in content

    def test_system_prompt_mentions_maintainability(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "maintainability" in content.lower() or "Maintainability" in content

    def test_system_prompt_mentions_verdict(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "verdict" in content

    def test_system_prompt_mentions_findings(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "findings" in content

    def test_system_prompt_mentions_severity(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "severity" in content

    def test_system_prompt_mentions_explore_subagents(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "explore" in content.lower()

    def test_system_prompt_mentions_parallel(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "parallel" in content.lower() or "background" in content.lower()

    def test_system_prompt_mentions_deduplicate(self):
        path = PROJECT_ROOT / "agents" / "swarm-reviewer-system.md"
        content = path.read_text()
        assert "deduplic" in content.lower()


class TestSwarmReviewCommand:
    """Tests for commands/swarm-review.md."""

    def test_command_exists(self):
        path = PROJECT_ROOT / "commands" / "swarm-review.md"
        assert path.is_file(), f"{path} does not exist"

    def test_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "swarm-review.md"
        content = path.read_text()
        assert "description:" in content

    def test_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "swarm-review.md"
        content = path.read_text()
        assert "argument-hint:" in content
        assert "scope" in content.lower()

    def test_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "swarm-review.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "swarm-review.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestReviewSubcommand:
    """Tests for the review subcommand."""

    def test_review_resolves_agent_yaml(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("review")
            assert agent_path.is_file()
            assert agent_path.name == "swarm-reviewer.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
