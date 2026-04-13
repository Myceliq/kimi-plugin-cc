"""Tests for TASK-008: Swarm researcher agent and swarm-research command."""

import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestSwarmResearcherYaml:
    """Tests for agents/swarm-researcher.yaml."""

    def test_yaml_exists(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        assert path.is_file(), f"{path} does not exist"

    def test_yaml_version_1(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "version: 1" in content

    def test_yaml_name(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "name: swarm-researcher" in content

    def test_yaml_system_prompt_path(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "system_prompt_path:" in content
        assert "swarm-researcher-system.md" in content

    def test_yaml_has_agent_tool(self):
        """Root agent that launches subagents."""
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.agent:Agent" in content

    def test_yaml_has_readfile_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:ReadFile" in content

    def test_yaml_has_shell_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.shell:Shell" in content

    def test_yaml_has_glob_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Glob" in content

    def test_yaml_has_grep_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.file:Grep" in content

    def test_yaml_has_searchweb_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.web:SearchWeb" in content

    def test_yaml_has_fetchurl_tool(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "kimi_cli.tools.web:FetchURL" in content

    def test_yaml_no_create_subagent(self):
        """Must NOT use CreateSubagent (non-existent in v1.31.0)."""
        path = PROJECT_ROOT / "agents" / "swarm-researcher.yaml"
        content = path.read_text()
        assert "CreateSubagent" not in content


class TestSwarmResearcherSystemPrompt:
    """Tests for agents/swarm-researcher-system.md."""

    def test_system_prompt_exists(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        assert path.is_file(), f"{path} does not exist"

    def test_system_prompt_mentions_decompose(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "decompose" in content.lower() or "work package" in content.lower() or "break" in content.lower()

    def test_system_prompt_mentions_3_to_10(self):
        """Should decompose into 3-10 work packages."""
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "3" in content and "10" in content

    def test_system_prompt_mentions_explore_subagents(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "explore" in content.lower()

    def test_system_prompt_mentions_parallel(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "parallel" in content.lower() or "background" in content.lower()

    def test_system_prompt_mentions_citations(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "citation" in content.lower() or "file:line" in content

    def test_system_prompt_mentions_synthesize(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "synthesize" in content.lower() or "consolidat" in content.lower()

    def test_system_prompt_mentions_verdict(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "verdict" in content

    def test_system_prompt_mentions_findings(self):
        path = PROJECT_ROOT / "agents" / "swarm-researcher-system.md"
        content = path.read_text()
        assert "findings" in content


class TestSwarmResearchCommand:
    """Tests for commands/swarm-research.md."""

    def test_command_exists(self):
        path = PROJECT_ROOT / "commands" / "swarm-research.md"
        assert path.is_file(), f"{path} does not exist"

    def test_command_has_description(self):
        path = PROJECT_ROOT / "commands" / "swarm-research.md"
        content = path.read_text()
        assert "description:" in content

    def test_command_has_argument_hint(self):
        path = PROJECT_ROOT / "commands" / "swarm-research.md"
        content = path.read_text()
        assert "argument-hint:" in content

    def test_command_has_context_fork(self):
        path = PROJECT_ROOT / "commands" / "swarm-research.md"
        content = path.read_text()
        assert "context: fork" in content

    def test_command_has_allowed_tools(self):
        path = PROJECT_ROOT / "commands" / "swarm-research.md"
        content = path.read_text()
        assert "allowed-tools:" in content


class TestResearchSubcommand:
    """Tests for the research subcommand."""

    def test_research_resolves_agent_yaml(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import resolve_agent_file
            agent_path = resolve_agent_file("research")
            assert agent_path.is_file()
            assert agent_path.name == "swarm-researcher.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
