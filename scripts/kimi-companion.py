#!/usr/bin/env python3
"""Kimi companion script — runtime engine for the Kimi Claude Code plugin.

Entry point for all Kimi CLI invocations. Handles job lifecycle, subcommand
routing, and structured JSON output.

Usage:
    python3 kimi-companion.py <command> [args]

Exit codes:
    0  — Success
    1  — Non-retryable failure
    75 — Retryable failure (rate limits, server errors, timeouts)
"""

import json
import os
import signal
import sys
import time

# Add scripts/ to path so lib/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.state import (
    resolve_state_dir,
    generate_job_id,
    read_job,
    write_job,
    list_jobs,
    delete_job,
)
from lib.kimi_cli import (
    AGENT_CONFIGS,
    build_kimi_command,
    resolve_agent_file,
    run_foreground,
    run_background,
)


def error_exit(message, code=1):
    """Print an error message to stderr and exit.

    Args:
        message: Error message string.
        code: Exit code (default 1).
    """
    sys.stderr.write(f"{message}\n")
    sys.exit(code)


def json_output(data):
    """Print structured JSON to stdout.

    Args:
        data: Dict or list to serialize as JSON.
    """
    print(json.dumps(data, indent=2))


def get_state_dir():
    """Resolve the state directory from environment.

    Returns:
        pathlib.Path to the state directory.
    """
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    return resolve_state_dir(plugin_data)


def handle_status(args):
    """Handle the 'status' subcommand.

    Args:
        args: List of remaining CLI arguments after 'status'.
    """
    state_dir = get_state_dir()

    # Parse flags
    include_all = "--all" in args
    wait = "--wait" in args
    timeout_ms = None

    clean_args = []
    i = 0
    while i < len(args):
        if args[i] == "--all":
            i += 1
            continue
        elif args[i] == "--wait":
            i += 1
            continue
        elif args[i] == "--timeout-ms" and i + 1 < len(args):
            timeout_ms = int(args[i + 1])
            i += 2
            continue
        else:
            clean_args.append(args[i])
            i += 1

    # If a job ID was provided, show that specific job
    if clean_args:
        job_id = clean_args[0]
        job = read_job(state_dir, job_id)
        if job is None:
            error_exit(f"Job not found: {job_id}")

        if wait and job.get("status") == "running":
            start = time.time()
            while job.get("status") == "running":
                if timeout_ms and (time.time() - start) * 1000 > timeout_ms:
                    error_exit(f"Timeout waiting for job {job_id}")
                time.sleep(1)
                job = read_job(state_dir, job_id)
                if job is None:
                    error_exit(f"Job disappeared: {job_id}")

        json_output(job)
        return

    # No job ID — list jobs
    jobs = list_jobs(state_dir, include_all=include_all)
    json_output({"jobs": jobs})


def handle_result(args):
    """Handle the 'result' subcommand.

    Args:
        args: List of remaining CLI arguments after 'result'.
    """
    state_dir = get_state_dir()

    if args:
        job_id = args[0]
        job = read_job(state_dir, job_id)
        if job is None:
            error_exit(f"Job not found: {job_id}")
        if job.get("status") not in ("complete", "failed"):
            error_exit(f"Job {job_id} has status '{job.get('status')}' — not yet complete")
        output = job.get("output")
        if output is None:
            error_exit(f"Job {job_id} has no output stored")
        json_output(output)
        return

    # No job ID — find most recently completed job
    all_jobs = list_jobs(state_dir, include_all=True)
    completed = [j for j in all_jobs if j.get("status") in ("complete", "failed")]
    if not completed:
        error_exit("No completed jobs found")

    # Sort by completed_at descending
    completed.sort(key=lambda j: j.get("completed_at", ""), reverse=True)
    output = completed[0].get("output")
    if output is None:
        error_exit(f"Job {completed[0]['job_id']} has no output stored")
    json_output(output)


def handle_cancel(args):
    """Handle the 'cancel' subcommand.

    Args:
        args: List of remaining CLI arguments after 'cancel'.
    """
    state_dir = get_state_dir()

    if args:
        job_id = args[0]
    else:
        # Cancel most recently started running job
        running = list_jobs(state_dir, include_all=False)
        running = [j for j in running if j.get("status") == "running"]
        if not running:
            error_exit("No running jobs to cancel")
        job_id = running[0]["job_id"]

    job = read_job(state_dir, job_id)
    if job is None:
        error_exit(f"Job not found: {job_id}")
    if job.get("status") != "running":
        error_exit(f"Job {job_id} is not running (status: {job.get('status')})")

    # Try to terminate the process: SIGTERM, wait up to 30s, then SIGKILL
    pid = job.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            # Wait up to 30 seconds for the process to exit
            for _ in range(30):
                time.sleep(1)
                try:
                    os.kill(pid, 0)  # Check if process is still alive
                except ProcessLookupError:
                    break  # Process exited
            else:
                # Process still alive after 30s — send SIGKILL
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        except ProcessLookupError:
            pass  # Process already dead
        except PermissionError:
            sys.stderr.write(f"Warning: no permission to signal PID {pid}\n")

    # Update job status
    job["status"] = "cancelled"
    job["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_job(state_dir, job_id, job)

    json_output({"status": "cancelled", "job_id": job_id})


def handle_session_start(args):
    """Handle the 'session-start' subcommand (invoked by SessionStart hook).

    Reads session context from stdin JSON and sets KIMI_COMPANION_SESSION_ID
    via the CLAUDE_ENV_FILE append pattern.

    Args:
        args: List of remaining CLI arguments (unused).
    """
    # Read session context from stdin
    stdin_text = sys.stdin.read().strip()
    if not stdin_text:
        return  # No input — nothing to do

    try:
        context = json.loads(stdin_text)
    except json.JSONDecodeError:
        return  # Malformed input — exit cleanly

    session_id = context.get("session_id", "")

    # Set KIMI_COMPANION_SESSION_ID via CLAUDE_ENV_FILE
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if env_file and session_id:
        with open(env_file, "a") as f:
            f.write(f"export KIMI_COMPANION_SESSION_ID={session_id}\n")


def handle_session_end(args):
    """Handle the 'session-end' subcommand (invoked by SessionEnd hook).

    Reads session context from stdin JSON, terminates running jobs for the
    session, and cleans up stale job files.

    Args:
        args: List of remaining CLI arguments (unused).
    """
    # Read session context from stdin
    stdin_text = sys.stdin.read().strip()
    session_id = None
    if stdin_text:
        try:
            context = json.loads(stdin_text)
            session_id = context.get("session_id")
        except json.JSONDecodeError:
            pass

    # Also check env var
    if not session_id:
        session_id = os.environ.get("KIMI_COMPANION_SESSION_ID")

    state_dir = get_state_dir()

    # Find running jobs for this session and cancel them
    running = list_jobs(state_dir, include_all=False, session_id=session_id)
    for job in running:
        if job.get("status") != "running":
            continue
        pid = job.get("pid")
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        job["status"] = "cancelled"
        job["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_job(state_dir, job["job_id"], job)


def collect_git_diff(scope="working-tree", base=None):
    """Collect git diff based on scope and base parameters.

    Args:
        scope: One of 'auto', 'working-tree', 'branch'
        base: Base ref for branch comparison (e.g., 'main', 'origin/main')

    Returns:
        String containing the git diff output.
    """
    import subprocess

    if scope == "working-tree":
        cmd = ["git", "diff", "HEAD"]
    elif scope == "branch":
        if base:
            cmd = ["git", "diff", f"{base}...HEAD"]
        else:
            # Try to detect default base branch
            for default_base in ["main", "master", "origin/main", "origin/master"]:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", default_base],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cmd = ["git", "diff", f"{default_base}...HEAD"]
                    break
            else:
                # Fallback to comparing with HEAD~1
                cmd = ["git", "diff", "HEAD~1..HEAD"]
    elif scope == "auto":
        # Auto-detect: if there are uncommitted changes, use working-tree
        # otherwise use branch comparison
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD"],
            capture_output=True
        )
        if result.returncode != 0:
            cmd = ["git", "diff", "HEAD"]
        else:
            # No uncommitted changes, compare with default base
            for default_base in ["main", "master", "origin/main", "origin/master"]:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", default_base],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    cmd = ["git", "diff", f"{default_base}...HEAD"]
                    break
            else:
                cmd = ["git", "diff", "HEAD~1..HEAD"]
    else:
        cmd = ["git", "diff", "HEAD"]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    return result.stdout if result.returncode == 0 else ""


def handle_review(args):
    """Handle the 'review' subcommand with git diff collection.

    Args:
        args: List of remaining CLI arguments after 'review'.
    """
    config = AGENT_CONFIGS.get("review")
    if config is None:
        error_exit("Review agent configuration not found")

    # Parse arguments
    mode = config["default_mode"]  # background by default
    scope = "auto"
    base = None
    focus = None
    clean_args = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--wait":
            mode = "wait"
            i += 1
        elif arg == "--background":
            mode = "background"
            i += 1
        elif arg == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif arg == "--base" and i + 1 < len(args):
            base = args[i + 1]
            i += 2
        elif arg == "--focus" and i + 1 < len(args):
            focus = args[i + 1]
            i += 2
        elif not arg.startswith("--"):
            clean_args.append(arg)
            i += 1
        else:
            i += 1

    # Resolve agent YAML
    try:
        agent_file = resolve_agent_file("review")
    except FileNotFoundError as e:
        error_exit(str(e))

    # Collect git diff
    diff = collect_git_diff(scope=scope, base=base)
    if not diff.strip():
        error_exit("No changes found to review. Make sure you have uncommitted changes or are on a branch with commits.")

    # Build the prompt with diff and any additional context
    prompt_parts = ["Review the following code changes:\n\n```diff\n", diff, "\n```"]
    if focus:
        prompt_parts.append(f"\n\nFocus areas: {focus}")
    if clean_args:
        prompt_parts.append(f"\n\nAdditional context: {' '.join(clean_args)}")
    prompt = "".join(prompt_parts)

    # Build Kimi CLI command
    cmd = build_kimi_command(agent_file=str(agent_file), prompt=prompt)

    # Create job record
    state_dir = get_state_dir()
    job_id = generate_job_id("review")
    session_id = os.environ.get("KIMI_COMPANION_SESSION_ID")
    job = {
        "job_id": job_id,
        "agent": config["agent_yaml"].replace(".yaml", ""),
        "status": "running",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pid": None,
        "args": ["review"] + args,
        "session_id": session_id,
    }

    cwd = os.getcwd()

    if mode == "background":
        bg_result = run_background(cmd=cmd, cwd=cwd)
        job["pid"] = bg_result["pid"]
        write_job(state_dir, job_id, job)
        json_output({"job_id": job_id, "status": "running", "pid": bg_result["pid"]})
    else:
        job["pid"] = os.getpid()
        write_job(state_dir, job_id, job)
        result = run_foreground(cmd=cmd, cwd=cwd)
        if result["exit_code"] == 0:
            job["status"] = "complete"
            job["output"] = result["output"]
        elif result["exit_code"] == 75:
            job["status"] = "failed"
            job["output"] = result.get("stderr", "Retryable failure")
            sys.stderr.write(f"Retryable failure (exit 75): {result.get('stderr', '')}\n")
        else:
            job["status"] = "failed"
            job["output"] = result.get("stderr", "Non-retryable failure")
            sys.stderr.write(f"Kimi CLI failed (exit {result['exit_code']}): {result.get('stderr', '')}\n")
        job["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_job(state_dir, job_id, job)
        if job["status"] == "failed":
            error_exit("Agent review failed")
        json_output({"job_id": job_id, "status": job["status"], "output": job["output"]})


def handle_agent(command, args):
    """Generic handler for agent subcommands.

    Resolves the agent YAML, constructs the prompt, selects foreground/background
    mode, invokes Kimi CLI, and stores the result via the state module.

    Args:
        command: The subcommand name (e.g., 'rescue', 'review').
        args: List of remaining CLI arguments.
    """
    config = AGENT_CONFIGS.get(command)
    if config is None:
        error_exit(f"Unknown agent command: {command}")

    # Parse mode flags
    mode = config["default_mode"]
    clean_args = []
    for arg in args:
        if arg == "--wait":
            mode = "wait"
        elif arg == "--background":
            mode = "background"
        else:
            clean_args.append(arg)

    # Commands that require arguments
    requires_args = {"rescue", "build-ui", "research", "review-ui"}
    if command in requires_args and not clean_args:
        error_exit(f"Usage: kimi-companion.py {command} <arguments>")

    # Resolve agent YAML
    try:
        agent_file = resolve_agent_file(command)
    except FileNotFoundError as e:
        error_exit(str(e))

    # Build prompt from remaining args
    prompt = " ".join(clean_args) if clean_args else command

    # Build Kimi CLI command
    cmd = build_kimi_command(agent_file=str(agent_file), prompt=prompt)

    # Determine working directory
    cwd = os.getcwd()

    # Create job record
    state_dir = get_state_dir()
    job_id = generate_job_id(command)
    session_id = os.environ.get("KIMI_COMPANION_SESSION_ID")
    job = {
        "job_id": job_id,
        "agent": config["agent_yaml"].replace(".yaml", ""),
        "status": "running",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pid": None,
        "args": [command] + clean_args,
        "session_id": session_id,
    }

    if mode == "background":
        bg_result = run_background(cmd=cmd, cwd=cwd)
        job["pid"] = bg_result["pid"]
        write_job(state_dir, job_id, job)
        json_output({"job_id": job_id, "status": "running", "pid": bg_result["pid"]})
    else:
        job["pid"] = os.getpid()
        write_job(state_dir, job_id, job)
        result = run_foreground(cmd=cmd, cwd=cwd)
        if result["exit_code"] == 0:
            job["status"] = "complete"
            job["output"] = result["output"]
        elif result["exit_code"] == 75:
            job["status"] = "failed"
            job["output"] = result.get("stderr", "Retryable failure")
            sys.stderr.write(f"Retryable failure (exit 75): {result.get('stderr', '')}\n")
        else:
            job["status"] = "failed"
            job["output"] = result.get("stderr", "Non-retryable failure")
            sys.stderr.write(f"Kimi CLI failed (exit {result['exit_code']}): {result.get('stderr', '')}\n")
        job["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_job(state_dir, job_id, job)
        if job["status"] == "failed":
            error_exit(f"Agent {command} failed")
        json_output({"job_id": job_id, "status": job["status"], "output": job["output"]})


def main():
    """Main entry point — parse subcommand and dispatch."""
    if len(sys.argv) < 2:
        error_exit("Usage: kimi-companion.py <command> [args]\n"
                   "Commands: status, result, cancel, research, review, "
                   "review-ui, refine-ui, build-ui, rescue, audit, fix, sprint")

    command = sys.argv[1]
    args = sys.argv[2:]

    dispatch = {
        "status": handle_status,
        "result": handle_result,
        "cancel": handle_cancel,
        "session-start": handle_session_start,
        "session-end": handle_session_end,
        "review": handle_review,
    }

    agent_commands = {"research", "review-ui", "refine-ui", "build-ui", "rescue", "audit", "fix", "sprint"}

    if command in dispatch:
        dispatch[command](args)
    elif command in agent_commands:
        handle_agent(command, args)
    else:
        error_exit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
