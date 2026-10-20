/*
 * fpms-splash [file]: draw a frame fpms saved (default /var/lib/wlanpi-fpms/boot-splash).
 *
 * Runs as soon as systemd starts, long before fpms (Python) can. The file is
 * "<panel> <gpiochip>\n" followed by a 128x128 RGB565 frame; fpms writes it
 * (fpms/boot_splash.py) for the panel and orientation in use. Panel init
 * mirrors fpms/modules/screen/st7735.py and luma.oled's ssd1351.
 */
#include <fcntl.h>
#include <linux/gpio.h>
#include <linux/spi/spidev.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define SPLASH_FILE "/var/lib/wlanpi-fpms/boot-splash"
#define SPI_DEV "/dev/spidev0.0"
#define FRAME_BYTES (128 * 128 * 2)
#define END 0xFFFF

static const uint16_t st7735_init[] = {
	0x1B1, 0x01, 0x2C, 0x2D,
	0x1B2, 0x01, 0x2C, 0x2D,
	0x1B3, 0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D,
	0x1B4, 0x07,
	0x1C0, 0xA2, 0x02, 0x84,
	0x1C1, 0xC5,
	0x1C2, 0x0A, 0x00,
	0x1C3, 0x8A, 0x2A,
	0x1C4, 0x8A, 0xEE,
	0x1C5, 0x0E,
	0x1E0, 0x0F, 0x1A, 0x0F, 0x18, 0x2F, 0x28, 0x20, 0x22,
	       0x1F, 0x1B, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10,
	0x1E1, 0x0F, 0x1B, 0x0F, 0x17, 0x33, 0x2C, 0x29, 0x2E,
	       0x30, 0x30, 0x39, 0x3F, 0x00, 0x07, 0x03, 0x10,
	0x1F0, 0x01,
	0x1F6, 0x00,
	0x13A, 0x05,
	0x136, 0x68,
	END,
};

/* luma.oled ssd1351 128x128 BGR, fpms contrast 128. */
static const uint16_t ssd1351_init[] = {
	0x1FD, 0x12, 0x1FD, 0xB1, 0x1AE, 0x1B3, 0xF1, 0x1CA, 0x7F,
	0x115, 0x00, 0x7F, 0x175, 0x00, 0x7F, 0x1A0, 0x74, 0x1A1, 0x00,
	0x1A2, 0x00, 0x1B5, 0x00, 0x1AB, 0x01, 0x1B1, 0x32,
	0x1B4, 0xA0, 0xB5, 0x55, 0x1BE, 0x05, 0x1C7, 0x0F, 0x1B6, 0x01,
	0x1A6, 0x1C1, 0x80, 0x80, 0x80, 0x15C,
	END,
};

/* Commands are tagged 0x100 so data bytes and commands share one table. */
static const uint16_t st7735_window[] = {
	0x12A, 0, 1, 0, 128, 0x12B, 0, 2, 0, 129, 0x12C, END,
};

static int spi, lines, dc_idx;

static void msleep(int ms)
{
	struct timespec ts = { ms / 1000, (ms % 1000) * 1000000L };
	nanosleep(&ts, NULL);
}

static void set_line(int idx, int on)
{
	struct gpio_v2_line_values v = { .bits = (uint64_t)on << idx, .mask = 1ULL << idx };
	ioctl(lines, GPIO_V2_LINE_SET_VALUES_IOCTL, &v);
}

static void spi_write(const uint8_t *buf, size_t len)
{
	/* spidev's default bufsiz is 4096. */
	while (len) {
		size_t n = len > 4096 ? 4096 : len;
		if (write(spi, buf, n) < 0)
			return;
		buf += n;
		len -= n;
	}
}

static void send(const uint16_t *seq)
{
	for (; *seq != END; seq++) {
		uint8_t b = *seq & 0xFF;
		set_line(dc_idx, !(*seq & 0x100));
		spi_write(&b, 1);
	}
}

int main(int argc, char **argv)
{
	static uint8_t buf[256 + FRAME_BYTES];
	char panel[16], chip[64];
	int st7735, fd, n, i;
	ssize_t len;

	fd = open(argc > 1 ? argv[1] : SPLASH_FILE, O_RDONLY);
	if (fd < 0)
		return 0;
	len = read(fd, buf, sizeof(buf));
	close(fd);
	if (len <= 0 || sscanf((char *)buf, "%15s %63s%n", panel, chip, &n) != 2 ||
	    len != n + 1 + FRAME_BYTES)
		return 0;
	st7735 = !strcmp(panel, "st7735");
	if (!st7735 && strcmp(panel, "ssd1351"))
		return 0;

	/* spidev has no systemd device unit to order on. */
	for (i = 0; (spi = open(SPI_DEV, O_WRONLY)) < 0; i++) {
		if (i == 100)
			return 0;
		msleep(20);
	}
	uint8_t mode = SPI_MODE_0;
	uint32_t speed = st7735 ? 40000000 : 8000000;
	ioctl(spi, SPI_IOC_WR_MODE, &mode);
	ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, &speed);

	/* Line index order: rst, dc, then the ST7735 backlight. */
	struct gpio_v2_line_request req = {
		.offsets = { st7735 ? 27 : 25, st7735 ? 25 : 24, 24 },
		.num_lines = st7735 ? 3 : 2,
		.config.flags = GPIO_V2_LINE_FLAG_OUTPUT,
	};
	strcpy(req.consumer, "fpms-splash");
	fd = open(chip, O_RDWR);
	if (fd < 0 || ioctl(fd, GPIO_V2_GET_LINE_IOCTL, &req) < 0)
		return 0;
	close(fd);
	lines = req.fd;
	dc_idx = 1;

	set_line(0, 1);
	msleep(10);
	set_line(0, 0);
	msleep(10);
	set_line(0, 1);
	msleep(10);

	if (st7735) {
		send(st7735_init);
		send((const uint16_t[]){ 0x111, END });
		msleep(120);
		send((const uint16_t[]){ 0x129, END });
		send(st7735_window);
	} else {
		send(ssd1351_init);
	}
	set_line(dc_idx, 1);
	spi_write(buf + n + 1, FRAME_BYTES);
	if (st7735)
		set_line(2, 1); /* backlight last: blank controller RAM is white */
	else
		send((const uint16_t[]){ 0x1AF, END });
	return 0;
}
