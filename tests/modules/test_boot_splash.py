from PIL import Image

from fpms import boot_splash


def test_rgb565_is_big_endian_565():
    image = Image.new("RGB", (2, 1))
    image.putpixel((0, 0), (0xFF, 0x00, 0x00))
    image.putpixel((1, 0), (0x00, 0x00, 0xFF))

    assert boot_splash.rgb565(image) == bytes([0xF8, 0x00, 0x00, 0x1F])


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "boot-splash")
    frame = bytes(range(256)) * 128

    boot_splash.save("st7735", "/dev/gpiochip0", frame, path=path)

    assert boot_splash.load(path) == ("st7735", "/dev/gpiochip0", frame)


def test_save_skips_unchanged_frame(tmp_path):
    path = tmp_path / "boot-splash"
    boot_splash.save("ssd1351", "/dev/gpiochip0", b"\x00" * 4, path=str(path))
    before = path.stat().st_mtime_ns

    boot_splash.save("ssd1351", "/dev/gpiochip0", b"\x00" * 4, path=str(path))

    assert path.stat().st_mtime_ns == before
