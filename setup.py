from setuptools import setup, find_packages

# fmt: off
setup(
    name="wlanpi-fpms",
    version="1.0.4",
    description="Front Panel Menu System for the WLAN Pi",
    long_description="Front Panel Menu System for the WLAN Pi",
    author="Jiri Brejcha",
    packages=find_packages(),
    install_requires=[
        "luma.oled==3.8.1",
        "gpiozero==1.6.2",
        "Pillow==8.4.0",
    ],
    author_email="jirka@jiribrejcha.net",
    keywords="FPMS",
    include_package_data=True,
    entry_points={"console_scripts": ["fpms=wlanpi_fpms.__main__:main"]},
)
