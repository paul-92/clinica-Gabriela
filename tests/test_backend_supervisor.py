import signal
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from backend.config import RuntimeSettings
from backend.supervisor import (
    BackendAlreadyRunning,
    BackendPortInUse,
    BackendProcessExited,
    BackendStartupTimeout,
    BackendSupervisor,
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeProcess:
    def __init__(self, *, polls=None, graceful=True, pid=4321):
        self.pid = pid
        self.polls = list(polls or [None])
        self.graceful = graceful
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.polls.pop(0) if len(self.polls) > 1 else self.polls[0]

    def terminate(self):
        self.terminated = True

    def send_signal(self, sent_signal):
        assert sent_signal == signal.CTRL_BREAK_EVENT
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        if self.terminated and not self.graceful and not self.killed:
            raise subprocess.TimeoutExpired("backend", timeout)
        return 0


@pytest.fixture
def settings():
    data_dir = Path("test-data").resolve()
    return RuntimeSettings(data_dir, data_dir / "api.db", "127.0.0.1", 8123, False)


def make_supervisor(settings, process, health_values, **kwargs):
    clock = FakeClock()
    values = iter(health_values)
    return BackendSupervisor(
        settings,
        startup_timeout=kwargs.pop("startup_timeout", 1.0),
        shutdown_timeout=0.1,
        poll_interval=0.1,
        process_factory=lambda *args, **factory_kwargs: process,
        health_probe=lambda _url: next(values, False),
        port_probe=kwargs.pop("port_probe", lambda _host, _port: False),
        clock=clock,
        sleeper=clock.sleep,
        **kwargs,
    )


def test_startup_normal_registra_ownership(settings):
    process = FakeProcess()
    supervisor = make_supervisor(settings, process, [False, False, True])

    ownership = supervisor.start()

    assert ownership.pid == process.pid
    assert supervisor.ownership == ownership
    assert supervisor.process is process


def test_startup_so_conclui_quando_health_fica_disponivel(settings):
    process = FakeProcess()
    supervisor = make_supervisor(settings, process, [False, False, False, True])

    supervisor.start()

    assert supervisor.ownership is not None


def test_timeout_encerra_somente_processo_criado(settings):
    process = FakeProcess()
    supervisor = make_supervisor(settings, process, [False], startup_timeout=0.2)

    with pytest.raises(BackendStartupTimeout):
        supervisor.start()

    assert process.terminated is True
    assert supervisor.ownership is None


def test_processo_encerra_antes_de_ficar_pronto(settings):
    process = FakeProcess(polls=[7])
    supervisor = make_supervisor(settings, process, [False, False])

    with pytest.raises(BackendProcessExited, match="codigo 7"):
        supervisor.start()

    assert process.terminated is False


def test_porta_ocupada_nao_cria_nem_encerra_processo(settings):
    external = FakeProcess(pid=9000)
    created = []
    supervisor = BackendSupervisor(
        settings,
        process_factory=lambda *args, **kwargs: created.append(True),
        health_probe=lambda _url: False,
        port_probe=lambda _host, _port: True,
    )

    with pytest.raises(BackendPortInUse):
        supervisor.start()

    assert created == []
    assert external.terminated is False
    assert external.killed is False


def test_shutdown_gracioso(settings):
    process = FakeProcess(graceful=True)
    supervisor = make_supervisor(settings, process, [False, True])
    supervisor.start()

    used_fallback = supervisor.stop()

    assert used_fallback is False
    assert process.terminated is True
    assert process.killed is False


def test_shutdown_faz_fallback_apenas_no_processo_owned(settings):
    process = FakeProcess(graceful=False)
    supervisor = make_supervisor(settings, process, [False, True])
    supervisor.start()

    used_fallback = supervisor.stop()

    assert used_fallback is True
    assert process.terminated is True
    assert process.killed is True


def test_backend_existente_nao_adquire_ownership_nem_cria_processo(settings):
    external = FakeProcess(pid=9001)
    created = []
    supervisor = BackendSupervisor(
        settings,
        process_factory=lambda *args, **kwargs: created.append(True),
        health_probe=lambda _url: True,
        port_probe=lambda _host, _port: True,
    )

    with pytest.raises(BackendAlreadyRunning, match="ownership nao adquirido"):
        supervisor.start()

    assert created == []
    assert supervisor.ownership is None
    assert external.terminated is False
    assert external.killed is False


def test_configuracao_de_host_e_port_e_usada_no_health(settings):
    configured = replace(settings, host="127.0.0.2", port=9456)
    urls = []
    process = FakeProcess()
    supervisor = BackendSupervisor(
        configured,
        process_factory=lambda *args, **kwargs: process,
        health_probe=lambda url: urls.append(url) or len(urls) > 1,
        port_probe=lambda host, port: False,
    )

    supervisor.start()

    assert urls == ["http://127.0.0.2:9456/health"] * 2


def test_run_with_mantem_ownership_ate_frontend_terminar(settings):
    backend = FakeProcess()
    observed = []
    supervisor = make_supervisor(settings, backend, [False, True])

    def run_frontend(command, check):
        observed.append((command, check, supervisor.ownership.pid))
        return subprocess.CompletedProcess(command, 0)

    result = supervisor.run_dependent(("frontend", "dev"), runner=run_frontend)

    assert result == 0
    assert observed == [(("frontend", "dev"), False, backend.pid)]
    assert backend.terminated is True
    assert supervisor.ownership is None


def test_run_with_propaga_falha_do_frontend_e_encerra_backend(settings):
    backend = FakeProcess()
    supervisor = make_supervisor(settings, backend, [False, True])

    result = supervisor.run_dependent(
        ("frontend",),
        runner=lambda command, check: subprocess.CompletedProcess(command, 23),
    )

    assert result == 23
    assert backend.terminated is True
    assert backend.killed is False


def test_run_with_encerra_backend_se_frontend_lancar_erro(settings):
    backend = FakeProcess()
    supervisor = make_supervisor(settings, backend, [False, True])

    with pytest.raises(OSError, match="frontend indisponivel"):
        supervisor.run_dependent(
            ("frontend",),
            runner=lambda command, check: (_ for _ in ()).throw(
                OSError("frontend indisponivel")
            ),
        )

    assert backend.terminated is True
    assert supervisor.ownership is None


def test_run_with_nao_inicia_frontend_se_backend_externo_existir(settings):
    external = FakeProcess(pid=9002)
    backend_created = []
    frontend_started = []
    supervisor = BackendSupervisor(
        settings,
        process_factory=lambda *args, **kwargs: backend_created.append(True),
        health_probe=lambda _url: True,
        port_probe=lambda _host, _port: True,
    )

    with pytest.raises(BackendAlreadyRunning):
        supervisor.run_dependent(
            ("frontend",),
            runner=lambda *args, **kwargs: frontend_started.append(True),
        )

    assert backend_created == []
    assert frontend_started == []
    assert external.terminated is False
    assert external.killed is False
