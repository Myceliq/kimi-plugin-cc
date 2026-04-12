"""Tests for TASK-001: Plugin metadata, internal skills, and project scaffolding."""

import json
import os
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestPluginJson:
    """Tests for .claude-plugin/plugin.json."""

    def test_plugin_json_exists(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        assert path.is_file(), f"{path} does not exist"

    def test_plugin_json_is_valid_json(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_plugin_json_name(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        with open(path) as f:
            data = json.load(f)
        assert data["name"] == "kimi"

    def test_plugin_json_has_version(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        with open(path) as f:
            data = json.load(f)
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_plugin_json_has_description(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        with open(path) as f:
            data = json.load(f)
        assert "description" in data
        assert isinstance(data["description"], str)
        assert len(data["description"]) > 0

    def test_plugin_json_has_author(self):
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        with open(path) as f:
            data = json.load(f)
        assert "author" in data
        assert "name" in data["author"]
        assert data["author"]["name"] == "Thomas Lestum"


class TestMarketplaceJson:
    """Tests for .claude-plugin/marketplace.json."""

    def test_marketplace_json_exists(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        assert path.is_file(), f"{path} does not exist"

    def test_marketplace_json_is_valid_json(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_marketplace_json_has_name(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        with open(path) as f:
            data = json.load(f)
        assert "name" in data
        assert isinstance(data["name"], str)

    def test_marketplace_json_has_owner(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        with open(path) as f:
            data = json.load(f)
        assert "owner" in data
        assert "name" in data["owner"]
        assert data["owner"]["name"] == "Thomas Lestum"

    def test_marketplace_json_has_plugins_array(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        with open(path) as f:
            data = json.load(f)
        assert "plugins" in data
        assert isinstance(data["plugins"], list)
        assert len(data["plugins"]) == 1

    def test_marketplace_json_plugin_entry(self):
        path = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        with open(path) as f:
            data = json.load(f)
        plugin = data["plugins"][0]
        assert plugin["name"] == "kimi"
        assert "description" in plugin
        assert "version" in plugin
        assert plugin["source"] == "./"


class TestKimiCliRuntimeSkill:
    """Tests for skills/kimi-cli-runtime/SKILL.md."""

    def test_skill_file_exists(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        assert path.is_file(), f"{path} does not exist"

    def test_skill_has_frontmatter(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        # Must have closing frontmatter delimiter
        parts = content.split("---")
        assert len(parts) >= 3, "SKILL.md must have opening and closing --- delimiters"

    def test_skill_not_user_invocable(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        assert "user-invocable: false" in content

    def test_skill_name(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        assert "name: kimi-cli-runtime" in content

    def test_skill_documents_invocation_path(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        assert "kimi-companion.py" in content
        assert "CLAUDE_PLUGIN_ROOT" in content

    def test_skill_documents_env_vars(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        assert "KIMI_PLUGIN_ROOT" in content
        assert "KIMI_COMPANION_SESSION_ID" in content

    def test_skill_documents_exit_codes(self):
        path = PROJECT_ROOT / "skills" / "kimi-cli-runtime" / "SKILL.md"
        content = path.read_text()
        # Must document exit code conventions
        assert "exit" in content.lower() or "Exit" in content


class TestKimiResultHandlingSkill:
    """Tests for skills/kimi-result-handling/SKILL.md."""

    def test_skill_file_exists(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        assert path.is_file(), f"{path} does not exist"

    def test_skill_has_frontmatter(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        parts = content.split("---")
        assert len(parts) >= 3, "SKILL.md must have opening and closing --- delimiters"

    def test_skill_not_user_invocable(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert "user-invocable: false" in content

    def test_skill_name(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert "name: kimi-result-handling" in content

    def test_skill_documents_severity_ordering(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert "severity" in content.lower()

    def test_skill_documents_no_auto_apply(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        # Must instruct not to auto-apply fixes
        assert "auto" in content.lower() or "approval" in content.lower()

    def test_skill_documents_visual_handling(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert "screenshot" in content.lower()

    def test_skill_documents_audit_display(self):
        path = PROJECT_ROOT / "skills" / "kimi-result-handling" / "SKILL.md"
        content = path.read_text()
        assert "audit" in content.lower()


class TestGitignore:
    """Tests for .gitignore."""

    def test_gitignore_exists(self):
        path = PROJECT_ROOT / ".gitignore"
        assert path.is_file(), f"{path} does not exist"

    def test_gitignore_has_kimi_jobs(self):
        path = PROJECT_ROOT / ".gitignore"
        content = path.read_text()
        assert ".kimi-jobs/" in content

    def test_gitignore_has_env(self):
        path = PROJECT_ROOT / ".gitignore"
        content = path.read_text()
        assert ".env" in content

    def test_gitignore_has_pycache(self):
        path = PROJECT_ROOT / ".gitignore"
        content = path.read_text()
        assert "__pycache__/" in content

    def test_gitignore_has_pyc(self):
        path = PROJECT_ROOT / ".gitignore"
        content = path.read_text()
        assert "*.pyc" in content


class TestDirectoryStructure:
    """Tests that target directories exist."""

    def test_claude_plugin_dir_exists(self):
        path = PROJECT_ROOT / ".claude-plugin"
        assert path.is_dir()

    def test_skills_dir_exists(self):
        path = PROJECT_ROOT / "skills"
        assert path.is_dir()

    def test_scripts_dir_exists(self):
        path = PROJECT_ROOT / "scripts"
        assert path.is_dir()

    def test_agents_dir_exists(self):
        path = PROJECT_ROOT / "agents"
        assert path.is_dir()

    def test_commands_dir_exists(self):
        path = PROJECT_ROOT / "commands"
        assert path.is_dir()

    # hooks/ directory is created in TASK-004 when hooks.json is written
