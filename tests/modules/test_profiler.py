"""Tests for the profiler front panel QR passphrase lookup."""

import json
import sys

import pytest


@pytest.fixture
def patch_imports():
    sys.modules["fpms.modules.wlanpi_oled"] = __import__("fakes")
    sys.modules["fpms.modules.pages.display"] = __import__("fakes")
    sys.modules["fpms.modules.pages.alert"] = __import__("fakes")
    sys.modules["fpms.modules.pages.pagedtable"] = __import__("fakes")
    sys.modules["fpms.modules.env_utils"] = __import__("fakes")


def test_passphrase_from_info_file(patch_imports, tmp_path, monkeypatch):
    from fpms.modules.apps import profiler

    info = tmp_path / "info.json"
    info.write_text(json.dumps({"ssid": "Profiler 573", "passphrase": "s3cret"}))
    monkeypatch.setattr(profiler, "PROFILER_INFO_FILE", str(info))
    monkeypatch.setattr(profiler, "PROFILER_CONFIG_FILE", str(tmp_path / "missing.ini"))

    assert profiler.read_profiler_passphrase() == "s3cret"


def test_passphrase_falls_back_to_config(patch_imports, tmp_path, monkeypatch):
    from fpms.modules.apps import profiler

    config = tmp_path / "config.ini"
    config.write_text("[GENERAL]\npassphrase: fromconfig\n")
    monkeypatch.setattr(profiler, "PROFILER_INFO_FILE", str(tmp_path / "missing.json"))
    monkeypatch.setattr(profiler, "PROFILER_CONFIG_FILE", str(config))

    assert profiler.read_profiler_passphrase() == "fromconfig"


def test_passphrase_unknown(patch_imports, tmp_path, monkeypatch):
    from fpms.modules.apps import profiler

    monkeypatch.setattr(profiler, "PROFILER_INFO_FILE", str(tmp_path / "missing.json"))
    monkeypatch.setattr(profiler, "PROFILER_CONFIG_FILE", str(tmp_path / "missing.ini"))

    assert profiler.read_profiler_passphrase() is None


def test_qrcode_uses_real_passphrase(patch_imports, tmp_path, monkeypatch):
    from fpms.modules.apps import profiler

    info = tmp_path / "info.json"
    info.write_text(json.dumps({"passphrase": "profiler"}))
    monkeypatch.setattr(profiler, "PROFILER_INFO_FILE", str(info))
    monkeypatch.setattr(profiler, "PROFILER_CONFIG_FILE", str(tmp_path / "missing.ini"))
    monkeypatch.setattr(
        profiler.Profiler, "profiler_beaconing_ssid", lambda self: "Profiler 573"
    )

    captured = {}

    def fake_qrcode(self, ssid, passphrase):
        captured["ssid"] = ssid
        captured["passphrase"] = passphrase
        return "/tmp/qr.png"

    monkeypatch.setattr(profiler.EnvUtils, "get_wifi_qrcode", fake_qrcode)

    obj = profiler.Profiler(g_vars={})
    assert obj.profiler_qrcode() == "/tmp/qr.png"
    assert captured == {"ssid": "Profiler 573", "passphrase": "profiler"}
