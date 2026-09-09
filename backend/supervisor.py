"""Lifecycle seguro do processo local do backend."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from backend.config import RuntimeSettings, get_runtime_settings


class BackendStartupError(RuntimeError):
    """Falha controlada durante a inicializacao do backend."""


class BackendStartupTimeout(BackendStartupError):
    pass


class BackendProcessExited(BackendStartupError):
    pass


class BackendAlreadyRunning(BackendStartupError):
    pass


class BackendPortInUse(BackendStartupError):
    pass


@dataclass(frozen=True)
class ProcessOwnership:
    pid: int
    command: tuple[str, ...]
    started_at: float


def health_url(settings: RuntimeSettings) -> str:
    return f"http://{settings.host}:{settings.port}/health"


def is_healthy(url: str, *, request_timeout: float = 0.5) -> bool:
    try:
        with urlopen(url, timeout=request_timeout) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return False


def is_port_open(host: str, port: int, *, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class BackendSupervisor:
    def __init__(
        self,
        settings: RuntimeSettings | None = None,
        *,
        startup_timeout: float = 20.0,
        shutdown_timeout: float = 8.0,
        poll_interval: float = 0.1,
        process_factory: Callable[..., subprocess.Popen] = subprocess.Popen,
        health_probe: Callable[[str], bool] = is_healthy,
        port_probe: Callable[[str, int], bool] = is_port_open,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        command: tuple[str, ...] | None = None,
    ):
        self.settings = settings or get_runtime_settings()
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.poll_interval = poll_interval
        self._process_factory = process_factory
        self._health_probe = health_probe
        self._port_probe = port_probe
        self._clock = clock
        self._sleep = sleeper
        self._command = command or (sys.executable, "-m", "backend.main")
        self._process: subprocess.Popen | None = None
        self.ownership: ProcessOwnership | None = None

    @property
    def process(self) -> subprocess.Popen | None:
        return self._process

    def start(self) -> ProcessOwnership:
        if self._process is not None:
            raise BackendAlreadyRunning("Este supervisor ja iniciou um backend.")

        url = health_url(self.settings)
        if self._health_probe(url):
            raise BackendAlreadyRunning(
                "Ja existe um backend saudavel no endereco configurado; ownership nao adquirido."
            )
        if self._port_probe(self.settings.host, self.settings.port):
            raise BackendPortInUse(
                f"A porta {self.settings.host}:{self.settings.port} ja esta ocupada."
            )

        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        process = self._process_factory(self._command, creationflags=creationflags)
        self._process = process
        self.ownership = ProcessOwnership(process.pid, tuple(self._command), self._clock())

        deadline = self._clock() + self.startup_timeout
        try:
            while self._clock() < deadline:
                exit_code = process.poll()
                if exit_code is not None:
                    raise BackendProcessExited(
                        f"Backend encerrou durante a inicializacao (codigo {exit_code})."
                    )
                if self._health_probe(url):
                    return self.ownership
                self._sleep(self.poll_interval)
            raise BackendStartupTimeout(
                f"Backend nao ficou pronto em {self.startup_timeout:.1f}s."
            )
        except BackendStartupError:
            self.stop()
            raise

    def stop(self) -> bool:
        """Encerra somente o Popen criado por esta instancia; retorna se houve fallback."""
        process = self._process
        if process is None or self.ownership is None:
            return False
        if process.poll() is not None:
            self._clear_ownership()
            return False

        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        used_fallback = False
        try:
            process.wait(timeout=self.shutdown_timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=self.shutdown_timeout)
            used_fallback = True
        finally:
            self._clear_ownership()
        return used_fallback

    def run_dependent(
        self,
        command: tuple[str, ...],
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> int:
        """Executa um processo dependente enquanto preserva ownership do backend."""
        if not command:
            raise ValueError("O comando dependente nao pode ser vazio.")
        self.start()
        try:
            completed = runner(command, check=False)
            return completed.returncode
        finally:
            self.stop()

    def _clear_ownership(self) -> None:
        self._process = None
        self.ownership = None


def wait_until_healthy(
    settings: RuntimeSettings | None = None,
    *,
    timeout: float = 20.0,
    poll_interval: float = 0.1,
) -> None:
    runtime = settings or get_runtime_settings()
    url = health_url(runtime)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_healthy(url):
            return
        time.sleep(poll_interval)
    raise BackendStartupTimeout(f"Backend nao ficou pronto em {timeout:.1f}s.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Supervisiona o backend local.")
    parser.add_argument(
        "action", choices=("run", "wait", "run-with"), nargs="?", default="run"
    )
    parser.add_argument("--startup-timeout", type=float, default=20.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == "wait":
            wait_until_healthy(timeout=args.startup_timeout)
            return 0
        supervisor = BackendSupervisor(startup_timeout=args.startup_timeout)
        if args.action == "run-with":
            command = tuple(args.command[1:] if args.command[:1] == ["--"] else args.command)
            if not command:
                parser.error("run-with requer um comando depois de --")
            return supervisor.run_dependent(command)
        ownership = supervisor.start()
        print(f"Backend pronto em {health_url(supervisor.settings)} (PID {ownership.pid}).")
        try:
            return supervisor.process.wait() if supervisor.process else 0
        except KeyboardInterrupt:
            supervisor.stop()
            return 0
    except BackendStartupError as exc:
        print(f"Falha ao iniciar backend: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Falha ao executar processo dependente: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
