"""Tests for TASK-003: Kimi CLI invocation, JSONL parsing, and background job support."""

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


class TestKimiCliModuleExists:
    """Tests that the kimi_cli module exists and is importable."""

    def test_kimi_cli_module_file_exists(self):
        path = PROJECT_ROOT / "scripts" / "lib" / "kimi_cli.py"
        assert path.is_file(), f"{path} does not exist"

    def test_kimi_cli_module_is_valid_python(self):
        path = PROJECT_ROOT / "scripts" / "lib" / "kimi_cli.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestBuildKimiCommand:
    """Tests for building the Kimi CLI command line."""

    def test_build_command_includes_print_flag(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import build_kimi_command
            cmd = build_kimi_command(
                agent_file="/path/to/agent.yaml",
                prompt="test prompt",
            )
            assert "--print" in cmd
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_build_command_includes_agent_file(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import build_kimi_command
            cmd = build_kimi_command(
                agent_file="/path/to/agent.yaml",
                prompt="test prompt",
            )
            assert "--agent-file" in cmd
            idx = cmd.index("--agent-file")
            assert cmd[idx + 1] == "/path/to/agent.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_build_command_includes_output_format(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import build_kimi_command
            cmd = build_kimi_command(
                agent_file="/path/to/agent.yaml",
                prompt="test prompt",
            )
            assert "--output-format" in cmd
            idx = cmd.index("--output-format")
            assert cmd[idx + 1] == "stream-json"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_build_command_includes_prompt(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import build_kimi_command
            cmd = build_kimi_command(
                agent_file="/path/to/agent.yaml",
                prompt="do the thing",
            )
            assert "-p" in cmd
            idx = cmd.index("-p")
            assert cmd[idx + 1] == "do the thing"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_build_command_no_work_dir_flag(self):
        """Kimi CLI does not support --work-dir. Working directory is set via subprocess cwd."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import build_kimi_command
            cmd = build_kimi_command(
                agent_file="/path/to/agent.yaml",
                prompt="test",
            )
            assert "--work-dir" not in cmd
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestParseJsonlStream:
    """Tests for JSONL stream parsing — extracting the final assistant message."""

    def test_parse_extracts_final_assistant_message(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import parse_jsonl_stream
            lines = [
                '{"type":"message","role":"assistant","content":"thinking..."}',
                '{"type":"tool_use","name":"Shell","input":{}}',
                '{"type":"tool_result","output":"ok"}',
                '{"type":"message","role":"assistant","content":"The answer is 42."}',
            ]
            stream = "\n".join(lines)
            result = parse_jsonl_stream(stream)
            assert result == "The answer is 42."
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_parse_returns_none_for_empty_stream(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import parse_jsonl_stream
            result = parse_jsonl_stream("")
            assert result is None
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_parse_skips_malformed_lines(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import parse_jsonl_stream
            lines = [
                'not valid json',
                '{"type":"message","role":"assistant","content":"valid"}',
                '',
            ]
            stream = "\n".join(lines)
            result = parse_jsonl_stream(stream)
            assert result == "valid"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_parse_handles_json_content_in_message(self):
        """When the final assistant message content is valid JSON, it should be returned as-is (string)."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import parse_jsonl_stream
            json_content = json.dumps({"status": "complete", "summary": "all done"})
            lines = [
                json.dumps({"type": "message", "role": "assistant", "content": json_content}),
            ]
            stream = "\n".join(lines)
            result = parse_jsonl_stream(stream)
            assert result == json_content
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestRunForeground:
    """Tests for foreground (--wait) Kimi CLI execution."""

    def test_run_foreground_returns_structured_result(self):
        """run_foreground should return a dict with exit_code and output."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import run_foreground
            # Use a simple echo command to simulate Kimi CLI output
            result = run_foreground(
                cmd=[sys.executable, "-c",
                     'import json; print(json.dumps({"type":"message","role":"assistant","content":"hello"}))'],
                cwd=str(PROJECT_ROOT),
            )
            assert isinstance(result, dict)
            assert "exit_code" in result
            assert result["exit_code"] == 0
            assert "output" in result
            assert result["output"] == "hello"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_run_foreground_captures_failure(self):
        """run_foreground with a failing command should return non-zero exit code."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import run_foreground
            result = run_foreground(
                cmd=[sys.executable, "-c", "import sys; sys.exit(1)"],
                cwd=str(PROJECT_ROOT),
            )
            assert result["exit_code"] == 1
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_run_foreground_retryable_exit_code(self):
        """Exit code 75 should be captured as retryable."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import run_foreground
            result = run_foreground(
                cmd=[sys.executable, "-c", "import sys; sys.exit(75)"],
                cwd=str(PROJECT_ROOT),
            )
            assert result["exit_code"] == 75
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestRunBackground:
    """Tests for background Kimi CLI execution."""

    def test_run_background_returns_pid(self):
        """run_background should return a dict with pid."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import run_background
            # Use a simple sleep command as a long-running process
            result = run_background(
                cmd=[sys.executable, "-c", "import time; time.sleep(0.1)"],
                cwd=str(PROJECT_ROOT),
            )
            assert isinstance(result, dict)
            assert "pid" in result
            assert isinstance(result["pid"], int)
            assert result["pid"] > 0
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_run_background_process_is_detached(self):
        """Background process should be detached (returns immediately)."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            import time
            from lib.kimi_cli import run_background
            start = time.time()
            result = run_background(
                cmd=[sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=str(PROJECT_ROOT),
            )
            elapsed = time.time() - start
            # Should return almost immediately (< 2 seconds), not wait for the 5-second sleep
            assert elapsed < 2.0, f"run_background took {elapsed}s — should be immediate"
            # Clean up the background process
            pid = result["pid"]
            try:
                import signal
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestRunAgentHandler:
    """Tests for the generic run_agent handler in the companion script."""

    def test_agent_command_rescue_requires_task(self):
        """rescue without a task description should error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "rescue", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1
            assert len(stderr) > 0

    def test_agent_command_build_ui_requires_args(self):
        """build-ui without arguments should error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "build-ui", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1
            assert len(stderr) > 0

    def test_agent_command_rescue_errors_no_agent_yaml(self):
        """rescue should error when the agent YAML doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "rescue", "fix the bug",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1
            # Should mention agent file not found
            assert "agent" in stderr.lower() or "not found" in stderr.lower() or "not yet" in stderr.lower()

    def test_agent_command_review_errors_no_agent_yaml(self):
        """review should error when the agent YAML doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "review",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_agent_command_research_errors_no_agent_yaml(self):
        """research should error when the agent YAML doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "research", "how does auth work",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_agent_command_audit_errors_no_agent_yaml(self):
        """audit should error when the agent YAML doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "audit",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_agent_command_review_ui_errors_no_agent_yaml(self):
        """review-ui should error when the agent YAML doesn't exist yet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "review-ui", "http://localhost:3000",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1


class TestAgentConfig:
    """Tests for the agent configuration mapping."""

    def test_agent_configs_map_exists(self):
        """Each agent command should have a configuration entry."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert "rescue" in AGENT_CONFIGS
            assert "review" in AGENT_CONFIGS
            assert "research" in AGENT_CONFIGS
            assert "review-ui" in AGENT_CONFIGS
            assert "build-ui" in AGENT_CONFIGS
            assert "audit" in AGENT_CONFIGS
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_agent_config_has_yaml_filename(self):
        """Each agent config should specify the YAML file name."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            for name, config in AGENT_CONFIGS.items():
                assert "agent_yaml" in config, f"{name} missing agent_yaml"
                assert config["agent_yaml"].endswith(".yaml"), f"{name} agent_yaml should end with .yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_agent_config_has_default_mode(self):
        """Each agent config should specify a default mode (wait or background)."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            for name, config in AGENT_CONFIGS.items():
                assert "default_mode" in config, f"{name} missing default_mode"
                assert config["default_mode"] in ("wait", "background"), \
                    f"{name} default_mode must be 'wait' or 'background'"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_rescue_defaults_to_wait(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["rescue"]["default_mode"] == "wait"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_build_ui_defaults_to_wait(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["build-ui"]["default_mode"] == "wait"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_review_defaults_to_background(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["review"]["default_mode"] == "background"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_research_defaults_to_background(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["research"]["default_mode"] == "background"
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

    def test_review_ui_defaults_to_background(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["review-ui"]["default_mode"] == "background"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_rescue_agent_yaml_is_rescuer(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["rescue"]["agent_yaml"] == "rescuer.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_review_agent_yaml_is_swarm_reviewer(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["review"]["agent_yaml"] == "swarm-reviewer.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_research_agent_yaml_is_swarm_researcher(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.kimi_cli import AGENT_CONFIGS
            assert AGENT_CONFIGS["research"]["agent_yaml"] == "swarm-researcher.yaml"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
