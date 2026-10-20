import subprocess

from fpms.modules import reg_domain


def test_set_reg_domain_reports_success(monkeypatch):
    calls = []
    monkeypatch.setattr(reg_domain.subprocess, "check_output", calls.append)
    monkeypatch.setattr(reg_domain.time, "sleep", lambda _: None)

    assert reg_domain.RegDomain({}).set_reg_domain({}, "AU")
    assert calls == [[reg_domain.REG_DOMAIN_FILE, "set", "AU", "--no-prompt"]]


def test_set_reg_domain_failure_returns_to_menu(monkeypatch):
    def fail(cmd):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(reg_domain.subprocess, "check_output", fail)
    g_vars = {}

    assert not reg_domain.RegDomain(g_vars).set_reg_domain(g_vars, "AU")
    assert g_vars["display_state"] == "menu"
