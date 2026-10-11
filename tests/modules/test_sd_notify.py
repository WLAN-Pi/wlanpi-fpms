import socket

from fpms.modules.utils import sd_notify_ready


def test_sd_notify_ready_sends_ready(tmp_path, monkeypatch):
    path = str(tmp_path / "notify")
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
        server.bind(path)
        monkeypatch.setenv("NOTIFY_SOCKET", path)
        sd_notify_ready()
        assert server.recv(64) == b"READY=1"


def test_sd_notify_ready_abstract_socket(monkeypatch):
    name = f"fpms-test-{id(monkeypatch)}"
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
        server.bind("\0" + name)
        monkeypatch.setenv("NOTIFY_SOCKET", "@" + name)
        sd_notify_ready()
        assert server.recv(64) == b"READY=1"


def test_sd_notify_ready_without_systemd(monkeypatch):
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    sd_notify_ready()
