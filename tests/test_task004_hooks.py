"""Tests for TASK-004: Session lifecycle hooks."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

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


class TestHooksJsonExists:
    """Tests for hooks/hooks.json file."""

    def test_hooks_json_exists(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        assert path.is_file(), f"{path} does not exist"

    def test_hooks_json_is_valid_json(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_hooks_json_has_description(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        assert "description" in data

    def test_hooks_json_has_hooks_key(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        assert "hooks" in data

    def test_hooks_json_has_session_start(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        assert "SessionStart" in data["hooks"]

    def test_hooks_json_has_session_end(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        assert "SessionEnd" in data["hooks"]

    def test_hooks_json_session_start_invokes_companion(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        hooks = data["hooks"]["SessionStart"]
        hook_commands = str(hooks)
        assert "kimi-companion.py" in hook_commands
        assert "session-start" in hook_commands

    def test_hooks_json_session_end_invokes_companion(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        hooks = data["hooks"]["SessionEnd"]
        hook_commands = str(hooks)
        assert "kimi-companion.py" in hook_commands
        assert "session-end" in hook_commands

    def test_hooks_json_timeout_is_5(self):
        path = PROJECT_ROOT / "hooks" / "hooks.json"
        with open(path) as f:
            data = json.load(f)
        for event in ["SessionStart", "SessionEnd"]:
            hooks_list = data["hooks"][event]
            for entry in hooks_list:
                for hook in entry.get("hooks", []):
                    assert hook.get("timeout") == 5, \
                        f"{event} hook timeout should be 5, got {hook.get('timeout')}"


class TestSessionStartSubcommand:
    """Tests for the session-start subcommand."""

    def test_session_start_subcommand_exists(self):
        """session-start should be a recognized subcommand."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdin_data = json.dumps({
                "session_id": "test-session-001",
                "cwd": tmpdir,
                "hook_event_name": "SessionStart",
            })
            stdout, stderr, code = run_companion(
                "session-start",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir},
                stdin_data=stdin_data,
            )
            # Should not error with "unknown command"
            assert "unknown command" not in stderr.lower()

    def test_session_start_sets_env_via_env_file(self):
        """SessionStart should append KIMI_COMPANION_SESSION_ID to CLAUDE_ENV_FILE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, "env_vars")
            # Create the env file
            with open(env_file, "w") as f:
                f.write("")

            stdin_data = json.dumps({
                "session_id": "test-session-abc",
                "cwd": tmpdir,
                "hook_event_name": "SessionStart",
            })
            stdout, stderr, code = run_companion(
                "session-start",
                env_override={
                    "CLAUDE_PLUGIN_DATA": tmpdir,
                    "CLAUDE_ENV_FILE": env_file,
                },
                stdin_data=stdin_data,
            )
            assert code == 0
            with open(env_file) as f:
                contents = f.read()
            assert "KIMI_COMPANION_SESSION_ID" in contents
            assert "test-session-abc" in contents

    def test_session_start_handles_missing_stdin(self):
        """SessionStart with no stdin should not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "session-start",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir},
                stdin_data="",
            )
            # Should exit cleanly or with a handled error, not crash
            assert code in (0, 1)


class TestSessionEndSubcommand:
    """Tests for the session-end subcommand."""

    def test_session_end_subcommand_exists(self):
        """session-end should be a recognized subcommand."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdin_data = json.dumps({
                "session_id": "test-session-001",
                "cwd": tmpdir,
                "hook_event_name": "SessionEnd",
            })
            stdout, stderr, code = run_companion(
                "session-end",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir},
                stdin_data=stdin_data,
            )
            assert "unknown command" not in stderr.lower()

    def test_session_end_cleans_up_stale_jobs(self):
        """SessionEnd should mark running jobs for the session as cancelled."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, read_job, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                # Create a running job with a session ID
                job = {
                    "job_id": "sess-end-001",
                    "agent": "rescuer",
                    "status": "running",
                    "started_at": "2026-04-12T14:30:00Z",
                    "pid": 999999999,  # Dead PID
                    "args": ["rescue", "test"],
                    "session_id": "test-session-end",
                }
                write_job(state_dir, "sess-end-001", job)

                stdin_data = json.dumps({
                    "session_id": "test-session-end",
                    "cwd": tmpdir,
                    "hook_event_name": "SessionEnd",
                })
                stdout, stderr, code = run_companion(
                    "session-end",
                    env_override={
                        "CLAUDE_PLUGIN_DATA": tmpdir,
                        "KIMI_COMPANION_SESSION_ID": "test-session-end",
                    },
                    stdin_data=stdin_data,
                )
                assert code == 0
                # Job should now be cancelled
                updated = read_job(state_dir, "sess-end-001")
                assert updated["status"] == "cancelled"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_session_end_handles_no_running_jobs(self):
        """SessionEnd with no running jobs should succeed silently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdin_data = json.dumps({
                "session_id": "test-session-empty",
                "cwd": tmpdir,
                "hook_event_name": "SessionEnd",
            })
            stdout, stderr, code = run_companion(
                "session-end",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir},
                stdin_data=stdin_data,
            )
            assert code == 0

    def test_session_end_handles_missing_stdin(self):
        """SessionEnd with no stdin should not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout, stderr, code = run_companion(
                "session-end",
                env_override={"CLAUDE_PLUGIN_DATA": tmpdir},
                stdin_data="",
            )
            assert code in (0, 1)


class TestSessionAwareJobQuerying:
    """Tests for session-aware job filtering in the state module."""

    def test_list_jobs_by_session(self):
        """list_jobs should support filtering by session_id."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, list_jobs, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job1 = {
                    "job_id": "sess-001",
                    "agent": "rescuer",
                    "status": "running",
                    "started_at": "2026-04-12T14:30:00Z",
                    "pid": 111,
                    "args": [],
                    "session_id": "session-A",
                }
                job2 = {
                    "job_id": "sess-002",
                    "agent": "reviewer",
                    "status": "running",
                    "started_at": "2026-04-12T14:31:00Z",
                    "pid": 222,
                    "args": [],
                    "session_id": "session-B",
                }
                write_job(state_dir, "sess-001", job1)
                write_job(state_dir, "sess-002", job2)
                filtered = list_jobs(state_dir, include_all=True, session_id="session-A")
                assert len(filtered) == 1
                assert filtered[0]["job_id"] == "sess-001"
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]

    def test_list_jobs_no_session_filter_returns_all(self):
        """list_jobs without session_id returns all jobs."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        try:
            from lib.state import write_job, list_jobs, resolve_state_dir
            with tempfile.TemporaryDirectory() as tmpdir:
                state_dir = resolve_state_dir(tmpdir)
                job1 = {
                    "job_id": "no-filter-001",
                    "agent": "rescuer",
                    "status": "running",
                    "started_at": "2026-04-12T14:30:00Z",
                    "pid": 111,
                    "args": [],
                    "session_id": "session-A",
                }
                job2 = {
                    "job_id": "no-filter-002",
                    "agent": "reviewer",
                    "status": "running",
                    "started_at": "2026-04-12T14:31:00Z",
                    "pid": 222,
                    "args": [],
                    "session_id": "session-B",
                }
                write_job(state_dir, "no-filter-001", job1)
                write_job(state_dir, "no-filter-002", job2)
                all_jobs = list_jobs(state_dir, include_all=True)
                assert len(all_jobs) == 2
        finally:
            sys.path.pop(0)
            for mod_name in list(sys.modules):
                if mod_name.startswith("lib."):
                    del sys.modules[mod_name]
