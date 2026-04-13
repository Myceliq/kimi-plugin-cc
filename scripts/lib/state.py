"""Job state management for the Kimi companion script.

Handles state directory resolution, job ID generation, and CRUD operations
on per-job JSON files stored under the plugin data directory.
"""

import hashlib
import json
import os
import pathlib
import random
import string
import time


FALLBACK_STATE_ROOT = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "kimi-companion"


def resolve_state_dir(plugin_data_dir=None):
    """Resolve the state directory for job files.

    Args:
        plugin_data_dir: Explicit plugin data directory. If None, reads from
            CLAUDE_PLUGIN_DATA env var. Falls back to a temp directory.

    Returns:
        pathlib.Path to the state directory (created if it does not exist).
    """
    if plugin_data_dir is None:
        plugin_data_dir = os.environ.get("CLAUDE_PLUGIN_DATA")

    if plugin_data_dir:
        state_dir = pathlib.Path(plugin_data_dir) / "state"
    else:
        state_dir = FALLBACK_STATE_ROOT / "state"

    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def generate_job_id(prefix="job"):
    """Generate a unique job ID with the given prefix.

    Args:
        prefix: String prefix for the job ID (e.g., 'rescue', 'review').

    Returns:
        A string like 'prefix-<timestamp_hex>-<random>'.
    """
    timestamp = format(int(time.time() * 1000), 'x')
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{rand}"


def _job_path(state_dir, job_id):
    """Return the file path for a given job ID.

    Args:
        state_dir: pathlib.Path to the state directory.
        job_id: The job identifier.

    Returns:
        pathlib.Path to the job JSON file.
    """
    return pathlib.Path(state_dir) / f"{job_id}.json"


def write_job(state_dir, job_id, job_data):
    """Write a job record to disk.

    Args:
        state_dir: pathlib.Path to the state directory.
        job_id: The job identifier.
        job_data: Dict containing the job record.
    """
    path = _job_path(state_dir, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(job_data, f, indent=2)


def read_job(state_dir, job_id):
    """Read a job record from disk.

    Args:
        state_dir: pathlib.Path to the state directory.
        job_id: The job identifier.

    Returns:
        Dict containing the job record, or None if not found.
    """
    path = _job_path(state_dir, job_id)
    if not path.is_file():
        return None
    with open(path) as f:
        return json.load(f)


def list_jobs(state_dir, include_all=False, session_id=None):
    """List all job records in the state directory.

    Args:
        state_dir: pathlib.Path to the state directory.
        include_all: If True, include completed and cancelled jobs.
            If False, include only active (running) jobs.
        session_id: If provided, only return jobs matching this session ID.

    Returns:
        List of job record dicts, sorted by started_at descending.
    """
    state_dir = pathlib.Path(state_dir)
    if not state_dir.is_dir():
        return []

    jobs = []
    for path in state_dir.glob("*.json"):
        with open(path) as f:
            try:
                job = json.load(f)
            except json.JSONDecodeError:
                continue
        if not include_all and job.get("status") in ("complete", "cancelled", "failed"):
            continue
        if session_id is not None and job.get("session_id") != session_id:
            continue
        jobs.append(job)

    jobs.sort(key=lambda j: j.get("started_at", ""), reverse=True)
    return jobs


def delete_job(state_dir, job_id):
    """Delete a job record file.

    Args:
        state_dir: pathlib.Path to the state directory.
        job_id: The job identifier.
    """
    path = _job_path(state_dir, job_id)
    if path.is_file():
        path.unlink()
