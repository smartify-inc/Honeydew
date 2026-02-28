"""Tests that install.sh and start.sh --check-only succeed (integration)."""

import os
import subprocess
import sys


def _repo_root():
    """Repository root (parent of backend/)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_install_script_succeeds():
    """Run install.sh; expect exit 0."""
    root = _repo_root()
    install = os.path.join(root, "install.sh")
    if not os.path.isfile(install):
        raise FileNotFoundError(f"install.sh not found at {install}")
    env = os.environ.copy()
    # Ensure config exists so install is non-interactive
    config = os.path.join(root, "config.json")
    example = os.path.join(root, "config.example.json")
    if not os.path.isfile(config) and os.path.isfile(example):
        import shutil
        shutil.copy(example, config)
    result = subprocess.run(
        [os.path.join(root, "install.sh")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"install.sh failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_start_check_only_succeeds():
    """Run start.sh --check-only; expect exit 0. Assumes install has been run (e.g. test_install_script_succeeds)."""
    root = _repo_root()
    start = os.path.join(root, "start.sh")
    if not os.path.isfile(start):
        raise FileNotFoundError(f"start.sh not found at {start}")
    result = subprocess.run(
        [start, "--check-only"],
        cwd=root,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"start.sh --check-only failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_install_then_start_check_only():
    """Run install.sh then start.sh --check-only in one flow (full integration)."""
    root = _repo_root()
    config = os.path.join(root, "config.json")
    example = os.path.join(root, "config.example.json")
    if not os.path.isfile(config) and os.path.isfile(example):
        import shutil
        shutil.copy(example, config)
    env = os.environ.copy()
    r1 = subprocess.run([os.path.join(root, "install.sh")], cwd=root, env=env, capture_output=True, text=True, timeout=120)
    assert r1.returncode == 0, f"install.sh failed: {r1.stderr}"
    r2 = subprocess.run([os.path.join(root, "start.sh"), "--check-only"], cwd=root, env=env, capture_output=True, text=True, timeout=30)
    assert r2.returncode == 0, f"start.sh --check-only failed: {r2.stderr}"
