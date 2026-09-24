import os
import sys
import types

from fpms.modules.env_utils import EnvUtils


def fake_gpiod(labels):
    """gpiod stand-in: labels maps a gpiochip file name to its kernel label."""

    class Chip:
        def __init__(self, path):
            name = os.path.basename(path)
            if name not in labels:
                raise OSError("not a gpiochip")
            self.label = labels[name]

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get_info(self):
            return types.SimpleNamespace(label=self.label)

    return types.SimpleNamespace(Chip=Chip)


def make_chips(tmp_path, monkeypatch, labels):
    for name in labels:
        (tmp_path / name).touch()
    monkeypatch.setitem(sys.modules, "gpiod", fake_gpiod(labels))


def test_pi5_rp1_header_chip_is_not_gpiochip0(tmp_path, monkeypatch):
    # 7.x kernel on a Pi 5: brcmstb chips first, RP1 header last
    make_chips(
        tmp_path,
        monkeypatch,
        {
            "gpiochip11": "gpio-brcmstb@107d517c00",
            "gpiochip13": "gpio-brcmstb@107d508500",
            "gpiochip15": "pinctrl-rp1",
        },
    )
    assert EnvUtils().get_gpiochip(str(tmp_path)) == str(tmp_path / "gpiochip15")


def test_cm4_header_chip_stays_gpiochip0(tmp_path, monkeypatch):
    make_chips(
        tmp_path,
        monkeypatch,
        {"gpiochip0": "pinctrl-bcm2711", "gpiochip1": "raspberrypi-exp-gpio"},
    )
    assert EnvUtils().get_gpiochip(str(tmp_path)) == str(tmp_path / "gpiochip0")


def test_unknown_labels_fall_back_to_gpiochip0(tmp_path, monkeypatch):
    make_chips(tmp_path, monkeypatch, {"gpiochip3": "some-expander"})
    assert EnvUtils().get_gpiochip(str(tmp_path)) == str(tmp_path / "gpiochip0")


def test_missing_gpiod_falls_back_to_gpiochip0(tmp_path, monkeypatch):
    (tmp_path / "gpiochip15").touch()
    monkeypatch.setitem(sys.modules, "gpiod", None)  # import raises ImportError
    assert EnvUtils().get_gpiochip(str(tmp_path)) == str(tmp_path / "gpiochip0")
