"""Kimi CLI invocation, JSONL parsing, and background job support.

Provides functions to build Kimi CLI commands, parse JSONL output streams,
and run agents in foreground or background mode.
"""

import json
import os
import subprocess
import sys


# Agent configuration mapping: command name -> agent YAML file + default mode
AGENT_CONFIGS = {
    "rescue": {
        "agent_yaml": "rescuer.yaml",
        "default_mode": "wait",
    },
    "build-ui": {
        "agent_yaml": "visual-builder.yaml",
        "default_mode": "wait",
    },
    "review": {
        "agent_yaml": "swarm-reviewer.yaml",
        "default_mode": "background",
    },
    "research": {
        "agent_yaml": "swarm-researcher.yaml",
        "default_mode": "background",
    },
    "review-ui": {
        "agent_yaml": "review-ui.yaml",
        "default_mode": "background",
    },
    "audit": {
        "agent_yaml": "audit-coordinator.yaml",
        "default_mode": "background",
    },
    "refine-ui": {
        "agent_yaml": "refine-ui.yaml",
        "default_mode": "wait",
    },
    "fix": {
        "agent_yaml": "bulk-fixer.yaml",
        "default_mode": "wait",
    },
}


def build_kimi_command(agent_file, prompt):
    """Build the command-line arguments for a Kimi CLI invocation in print mode.

    Args:
        agent_file: Absolute path to the agent YAML file.
        prompt: The prompt string to pass to the agent.

    Returns:
        List of command-line arguments (strings).
    """
    return [
        "kimi",
        "--print",
        "--agent-file", str(agent_file),
        "--output-format", "stream-json",
        "-p", prompt,
    ]


def parse_jsonl_stream(stream_text):
    """Parse JSONL output from Kimi CLI and extract the final assistant message content.

    Args:
        stream_text: Raw JSONL text (newline-separated JSON objects).

    Returns:
        The content string from the last assistant message, or None if no
        assistant message was found.
    """
    last_content = None
    for line in stream_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "message" and obj.get("role") == "assistant":
            content = obj.get("content")
            if content is not None:
                last_content = content
    return last_content


def run_foreground(cmd, cwd):
    """Run a command in the foreground and capture its output.

    Blocks until the command completes, parses JSONL stdout, and returns
    a structured result.

    Args:
        cmd: List of command-line arguments.
        cwd: Working directory for the subprocess.

    Returns:
        Dict with keys:
            exit_code (int): Process exit code (0=success, 1=failure, 75=retryable).
            output (str or None): Parsed final assistant message content, or None.
            stderr (str): Captured stderr text.
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    output = parse_jsonl_stream(result.stdout)
    return {
        "exit_code": result.returncode,
        "output": output,
        "stderr": result.stderr,
    }


def run_background(cmd, cwd):
    """Run a command as a detached background process.

    Returns immediately with the PID of the spawned process.

    Args:
        cmd: List of command-line arguments.
        cwd: Working directory for the subprocess.

    Returns:
        Dict with keys:
            pid (int): Process ID of the spawned background process.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {"pid": proc.pid}


def resolve_agent_file(command_name, plugin_root=None):
    """Resolve the absolute path to an agent YAML file.

    Args:
        command_name: The agent command name (e.g., 'rescue', 'review').
        plugin_root: Absolute path to the plugin root directory. If None,
            reads from CLAUDE_PLUGIN_ROOT env var, falling back to the
            repo root derived from this file's location.

    Returns:
        pathlib.Path to the agent YAML file.

    Raises:
        FileNotFoundError: If the agent YAML file does not exist.
    """
    import pathlib

    if plugin_root is None:
        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root is None:
        # Fallback: derive from this file's location (scripts/lib/kimi_cli.py -> repo root)
        plugin_root = str(pathlib.Path(__file__).resolve().parent.parent.parent)

    config = AGENT_CONFIGS.get(command_name)
    if config is None:
        raise ValueError(f"Unknown agent command: {command_name}")

    agent_path = pathlib.Path(plugin_root) / "agents" / config["agent_yaml"]
    if not agent_path.is_file():
        raise FileNotFoundError(f"Agent file not found: {agent_path}")

    return agent_path
