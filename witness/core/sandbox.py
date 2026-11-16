"""Run one command in a disposable, network-less, read-only Docker container."""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from pathlib import Path


def run_isolated(path: Path, image: str, args: list[str], stdin: str = "",
                 timeout: float = 12) -> dict:
    name = "witness-probe-" + uuid.uuid4().hex
    command = [
        "docker", "run", "--rm", "--name", name, "-i", "--network", "none",
        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "64", "--memory", "256m", "--cpus", "1",
        "--ulimit", "fsize=65536:65536",
        "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
        "--mount", f"type=bind,src={path},dst=/workspace,readonly",
        "--workdir", "/workspace", "--env", "PYTHONDONTWRITEBYTECODE=1",
        image, *args,
    ]
    started = time.monotonic()
    # Drain excess output without retaining it in memory or temporary host files.
    proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    captures = [bytearray(), bytearray()]
    totals = [0, 0]

    def drain(pipe, index, limit):
        try:
            while chunk := pipe.read(65536):
                totals[index] += len(chunk)
                captures[index].extend(chunk[:max(0, limit-len(captures[index]))])
        finally:
            pipe.close()

    def feed():
        try:
            proc.stdin.write(stdin.encode())
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    threads = [threading.Thread(target=drain, args=(proc.stdout, 0, 6000), daemon=True),
               threading.Thread(target=drain, args=(proc.stderr, 1, 2000), daemon=True),
               threading.Thread(target=feed, daemon=True)]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        proc.kill()
        proc.wait()
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        for thread in threads:
            thread.join(timeout=5)
    out, err = captures
    return {
        "exit_code": proc.returncode, "timed_out": timed_out,
        "stdout": out[:6000].decode(errors="replace"),
        "stderr": err[:2000].decode(errors="replace"),
        "output_truncated": totals[0] > 6000 or totals[1] > 2000,
        "elapsed_seconds": round(time.monotonic() - started, 4),
    }
