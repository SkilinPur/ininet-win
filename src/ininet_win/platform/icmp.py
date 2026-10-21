"""Host discovery via ICMP ping (Windows)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable


async def ping_host(
    ip: str, timeout: float = 1.0, semaphore: asyncio.Semaphore | None = None
) -> bool:
    """Ping a single host. Returns True if it responds."""
    if semaphore is None:
        semaphore = asyncio.Semaphore(1)
    async with semaphore:
        args = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(proc.wait(), timeout=timeout + 2)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                return False
            return proc.returncode == 0
        except (OSError, FileNotFoundError):
            return False


async def ping_sweep(
    hosts: Iterable[str],
    concurrency: int = 128,
    timeout: float = 1.0,
) -> list[str]:
    """Ping many hosts concurrently, returning those that respond."""
    semaphore = asyncio.Semaphore(concurrency)
    host_list = list(hosts)
    tasks = [ping_host(ip, timeout=timeout, semaphore=semaphore) for ip in host_list]
    results = await asyncio.gather(*tasks)
    return [ip for ip, alive in zip(host_list, results) if alive]
