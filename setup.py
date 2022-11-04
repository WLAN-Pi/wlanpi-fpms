# -*- coding: utf-8 -*-

import os
from codecs import open

from setuptools import find_packages, setup

# load the package's __version__.py module as a dictionary
metadata = {}

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "fpms", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), metadata)


def parse_requires(_list):
    requires = list()
    trims = ["#", "piwheels.org"]
    for require in _list:
        if any(match in require for match in trims):
            continue
        requires.append(require)
    requires = list(filter(None, requires))  # remove "" from list
    return requires


with open("extras.txt") as f:
    testing = f.read().splitlines()

testing = parse_requires(testing)

extras = {"testing": testing}

with open("requirements.txt") as f:
    requires = f.read().splitlines()

requires = parse_requires(requires)

setup(
    name=metadata["__title__"],
    version=metadata["__version__"],
    description=metadata["__description__"],
    long_description=metadata["__description__"],
    author=metadata["__author__"],
    author_email=metadata["__author_email__"],
    url=metadata["__url__"],
    python_requires="~=3.9,",
    license=metadata["__license__"],
    platforms=["linux"],
    packages=find_packages(),
    install_requires=requires,
    extras_require=extras,
    project_urls={
        "Documentation": "https://docs.wlanpi.com",
        "Source": metadata["__url__"],
    },
    classifiers=[
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: System Administrators",
        "Topic :: Utilities",
    ],
    keywords="FPMS",
    include_package_data=True,
    entry_points={"console_scripts": ["fpms=fpms.__main__:main"]},
)
