"""Tests for TASK-002: Companion script core — entry point, state management, and job management commands."""

import json
import os
import pathlib
import subprocess
import sys
import shutil
import tempfile
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPANION = PROJECT_ROOT / "scripts" / "kimi-companion.py"


def run_companion(*args, env_override=None, stdin_data=None):
    """Run the companion script with given args, return (stdout, stderr, returncode)."""
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    result = subprocess.run(
        [sys.executable, str(COMPANION)] + list(args),
        capture_output=True,
        text=True,
        env=env,
        input=stdin_data,
        timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


class TestCompanionEntryPoint:
    """Tests for the companion script entry point and subcommand dispatcher."""

    def test_companion_script_exists(self):
        assert COMPANION.is_file(), f"{COMPANION} does not exist"

    def test_companion_script_is_valid_python(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(COMPANION)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_unknown_subcommand_exits_with_error(self):
        stdout, stderr, code = run_companion("nonexistent-command")
        assert code == 1
        assert len(stderr) > 0

    def test_no_args_exits_with_error(self):
        stdout, stderr, code = run_companion()
        assert code == 1
        assert len(stderr) > 0

    def test_status_subcommand_exists(self):
        """Status with no jobs should succeed and return valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "status", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 0
            data = json.loads(stdout)
            assert isinstance(data, dict)

    def test_result_subcommand_exists(self):
        """Result with no jobs should exit with error (no completed jobs)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "result", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_cancel_subcommand_exists(self):
        """Cancel with no jobs should exit with error (no running jobs)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "cancel", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_agent_commands_error_without_yaml(self):
        """Agent subcommands should error when agent YAML files don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for cmd in ["research", "review", "review-ui", "build-ui", "rescue", "audit"]:
                stdout, stderr, code = run_companion(
                    cmd, "dummy-arg",
                    env_override={"CLAUDE_PLUGIN_DATA": tmpdir, "CLAUDE_PLUGIN_ROOT": tmpdir}
                )
                assert code == 1, f"{cmd} should exit with error"
                assert len(stderr) > 0, f"{cmd} should produce an error message"


class TestStateModule:
    """Tests for scripts/lib/state.py — job state management."""

    def test_state_module_exists(self):
        path = PROJECT_ROOT / "scripts" / "lib" / "state.py"
        assert path.is_file(), f"{path} does not exist"

    def test_lib_init_exists(self):
        path = PROJECT_ROOT / "scripts" / "lib" / "__init__.py"
        assert path.is_file(), f"{path} does not exist"


class TestStateDirectoryResolution:
    """Tests for job state directory resolution."""

    def test_state_dir_uses_plugin_data_env(self):
        """State dir should be under CLAUDE_PLUGIN_DATA when set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "status", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 0
            # The state directory should have been created under tmpdir
            state_dir = pathlib.Path(tmpdir) / "state"
            assert state_dir.is_dir() or any(
                d.name == "state" for d in pathlib.Path(tmpdir).rglob("*") if d.is_dir()
            )

    def test_state_dir_fallback_when_no_env(self):
        """State dir should use a fallback when CLAUDE_PLUGIN_DATA is not set."""
        env = os.environ.copy()
        env.pop("CLAUDE_PLUGIN_DATA", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        result = subprocess.run(
            [sys.executable, str(COMPANION), "status"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        # Should still succeed (using fallback dir)
        assert result.returncode == 0


class TestJobIdGeneration:
    """Tests for job ID generation."""

    def test_job_id_has_prefix(self):
        """Job IDs should start with a prefix."""
        # We test this indirectly through the status command after creating a job.
        # For unit testing, we import the state module.
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import generate_job_id
            job_id = generate_job_id("test")
            assert job_id.startswith("test-")
        finally:
            sys.path.pop(0)
            # Clean up imported modules
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_job_id_uniqueness(self):
        """Two job IDs should be different."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import generate_job_id
            id1 = generate_job_id("job")
            id2 = generate_job_id("job")
            assert id1 != id2
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_job_id_format(self):
        """Job IDs should contain prefix, timestamp component, and random component."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import generate_job_id
            job_id = generate_job_id("review")
            parts = job_id.split("-")
            assert len(parts) >= 3, f"Job ID should have at least 3 parts: {job_id}"
            assert parts[0] == "review"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestJobCRUD:
    """Tests for job state read/write/list/delete operations."""

    def test_write_and_read_job(self):
        """Should be able to write a job and read it back."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, read_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {
                    "job_id": "test-abc123",
                    "agent": "rescuer",
                    "status": "running",
                    "started_at": "2026-04-12T14:30:00Z",
                    "pid": 12345,
                    "args": ["rescue", "fix the bug"],
                }
                write_job(state_dir, "test-abc123", job)
                result = read_job(state_dir, "test-abc123")
                assert result["job_id"] == "test-abc123"
                assert result["agent"] == "rescuer"
                assert result["status"] == "running"
                assert result["pid"] == 12345
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_list_jobs(self):
        """Should list all jobs."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, list_jobs, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job1 = {"job_id": "test-001", "agent": "rescuer", "status": "running",
                         "started_at": "2026-04-12T14:30:00Z", "pid": 111, "args": []}
                job2 = {"job_id": "test-002", "agent": "reviewer", "status": "complete",
                         "started_at": "2026-04-12T14:31:00Z", "pid": 222, "args": []}
                write_job(state_dir, "test-001", job1)
                write_job(state_dir, "test-002", job2)
                jobs = list_jobs(state_dir, include_all=True)
                ids = [j["job_id"] for j in jobs]
                assert "test-001" in ids
                assert "test-002" in ids
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_delete_job(self):
        """Should delete a job file."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, read_job, delete_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "test-del", "agent": "rescuer", "status": "running",
                       "started_at": "2026-04-12T14:30:00Z", "pid": 111, "args": []}
                write_job(state_dir, "test-del", job)
                delete_job(state_dir, "test-del")
                result = read_job(state_dir, "test-del")
                assert result is None
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestStatusSubcommand:
    """Tests for the status subcommand."""

    def test_status_no_jobs_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "status", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 0
            data = json.loads(stdout)
            assert "jobs" in data
            assert data["jobs"] == []

    def test_status_shows_active_jobs(self):
        """Create a job via state module, then check status sees it."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "stat-001", "agent": "rescuer", "status": "running",
                       "started_at": "2026-04-12T14:30:00Z", "pid": 99999, "args": ["rescue", "test"]}
                write_job(state_dir, "stat-001", job)
                stdout, stderr, code = run_companion(
                    "status", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                assert len(data["jobs"]) >= 1
                ids = [j["job_id"] for j in data["jobs"]]
                assert "stat-001" in ids
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_status_with_job_id_shows_details(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "stat-002", "agent": "rescuer", "status": "running",
                       "started_at": "2026-04-12T14:30:00Z", "pid": 88888, "args": ["rescue", "test"]}
                write_job(state_dir, "stat-002", job)
                stdout, stderr, code = run_companion(
                    "status", "stat-002", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                assert data["job_id"] == "stat-002"
                assert data["agent"] == "rescuer"
                assert data["status"] == "running"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_status_all_flag_includes_completed(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "stat-003", "agent": "rescuer", "status": "complete",
                       "started_at": "2026-04-12T14:30:00Z", "completed_at": "2026-04-12T14:35:00Z",
                       "pid": 77777, "args": ["rescue", "test"],
                       "output": {"status": "complete", "summary": "done"}}
                write_job(state_dir, "stat-003", job)
                # Without --all, completed jobs should still show by default in listing
                stdout, stderr, code = run_companion(
                    "status", "--all", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                ids = [j["job_id"] for j in data["jobs"]]
                assert "stat-003" in ids
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_status_nonexistent_job_id_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "status", "nonexistent-id", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1


class TestResultSubcommand:
    """Tests for the result subcommand."""

    def test_result_no_completed_jobs_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "result", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_result_returns_most_recent_completed_output(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "res-001", "agent": "rescuer", "status": "complete",
                       "started_at": "2026-04-12T14:30:00Z", "completed_at": "2026-04-12T14:35:00Z",
                       "pid": 11111, "args": ["rescue", "test"],
                       "output": {"status": "complete", "summary": "All fixed"}}
                write_job(state_dir, "res-001", job)
                stdout, stderr, code = run_companion(
                    "result", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                assert data["summary"] == "All fixed"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_result_with_job_id_returns_that_jobs_output(self):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job1 = {"job_id": "res-002", "agent": "rescuer", "status": "complete",
                        "started_at": "2026-04-12T14:30:00Z", "completed_at": "2026-04-12T14:35:00Z",
                        "pid": 11111, "args": [],
                        "output": {"status": "complete", "summary": "Job 2 output"}}
                job2 = {"job_id": "res-003", "agent": "reviewer", "status": "complete",
                        "started_at": "2026-04-12T14:31:00Z", "completed_at": "2026-04-12T14:36:00Z",
                        "pid": 22222, "args": [],
                        "output": {"status": "complete", "summary": "Job 3 output"}}
                write_job(state_dir, "res-002", job1)
                write_job(state_dir, "res-003", job2)
                stdout, stderr, code = run_companion(
                    "result", "res-002", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                assert data["summary"] == "Job 2 output"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_result_running_job_errors(self):
        """Requesting result of a still-running job should error."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job = {"job_id": "res-run", "agent": "rescuer", "status": "running",
                       "started_at": "2026-04-12T14:30:00Z", "pid": 11111, "args": []}
                write_job(state_dir, "res-run", job)
                stdout, stderr, code = run_companion(
                    "result", "res-run", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 1
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestCancelSubcommand:
    """Tests for the cancel subcommand."""

    def test_cancel_no_running_jobs_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "cancel", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_cancel_nonexistent_job_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "cancel", "nonexistent-id", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 1

    def test_cancel_updates_job_status(self):
        """Cancel a job with a dead PID — should update status to cancelled."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, read_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                # Use a PID that definitely doesn't exist (very high number)
                job = {"job_id": "can-001", "agent": "rescuer", "status": "running",
                       "started_at": "2026-04-12T14:30:00Z", "pid": 999999999, "args": ["rescue", "test"]}
                write_job(state_dir, "can-001", job)
                stdout, stderr, code = run_companion(
                    "cancel", "can-001", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
                )
                assert code == 0
                data = json.loads(stdout)
                assert data["status"] == "cancelled"
                # Verify the state file was updated
                updated = read_job(state_dir, "can-001")
                assert updated["status"] == "cancelled"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]


class TestCommandFiles:
    """Tests for the command markdown files."""

    def test_status_command_exists(self):
        path = PROJECT_ROOT / "commands" / "status.md"
        assert path.is_file()

    def test_status_command_frontmatter(self):
        path = PROJECT_ROOT / "commands" / "status.md"
        content = path.read_text()
        assert "disable-model-invocation: true" in content
        assert "allowed-tools:" in content
        assert "Bash" in content
        assert "argument-hint:" in content

    def test_status_command_invokes_companion(self):
        path = PROJECT_ROOT / "commands" / "status.md"
        content = path.read_text()
        assert "kimi-companion.py" in content
        assert "status" in content

    def test_result_command_exists(self):
        path = PROJECT_ROOT / "commands" / "result.md"
        assert path.is_file()

    def test_result_command_frontmatter(self):
        path = PROJECT_ROOT / "commands" / "result.md"
        content = path.read_text()
        assert "disable-model-invocation: true" in content
        assert "allowed-tools:" in content

    def test_result_command_invokes_companion(self):
        path = PROJECT_ROOT / "commands" / "result.md"
        content = path.read_text()
        assert "kimi-companion.py" in content
        assert "result" in content

    def test_cancel_command_exists(self):
        path = PROJECT_ROOT / "commands" / "cancel.md"
        assert path.is_file()

    def test_cancel_command_frontmatter(self):
        path = PROJECT_ROOT / "commands" / "cancel.md"
        content = path.read_text()
        assert "disable-model-invocation: true" in content
        assert "allowed-tools:" in content

    def test_cancel_command_invokes_companion(self):
        path = PROJECT_ROOT / "commands" / "cancel.md"
        content = path.read_text()
        assert "kimi-companion.py" in content
        assert "cancel" in content


class TestErrorHandling:
    """Tests for error handling conventions."""

    def test_errors_go_to_stderr(self):
        """All errors should be written to stderr, not stdout."""
        stdout, stderr, code = run_companion("nonexistent-command")
        assert code == 1
        assert len(stderr) > 0
        # stdout should be empty on error
        assert stdout.strip() == ""

    def test_status_output_is_json(self):
        """Structured output should be valid JSON to stdout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "status", env_override={"CLAUDE_PLUGIN_DATA": tmpdir}
            )
            assert code == 0
            data = json.loads(stdout)
            assert isinstance(data, dict)
