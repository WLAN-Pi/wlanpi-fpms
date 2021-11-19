# -*- coding: utf-8 -*-

import os
from codecs import open

from setuptools import find_packages, setup

# load the package's __version__.py module as a dictionary
metadata = {}

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "fpms", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), metadata)

# fmt: off
# Pillow must be on its own line otherwise Debian packaging will fail
setup(
    name=metadata["__title__"],
    version=metadata["__version__"],
    description=metadata["__description__"],
    long_description=metadata["__description__"],
    author=metadata["__author__"],
    author_email=metadata["__author_email__"],
    url=metadata["__url__"],
    python_requires="~=3.7,",
    license=metadata["__license__"],
    platforms=["linux"],
    packages=find_packages(),
    install_requires=[
        "luma.oled==3.8.1",
        "gpiozero==1.6.2",
        "Pillow==8.4.0", 
    ],
    project_urls={
        "Documentation": "https://docs.wlanpi.com",
        "Source": metadata["__url__"],
    },
    classifiers=[
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: System Administrators",
        "Topic :: Utilities",
    ],
    keywords="FPMS",
    include_package_data=True,
    entry_points={"console_scripts": ["fpms=fpms.__main__:main"]},
)
