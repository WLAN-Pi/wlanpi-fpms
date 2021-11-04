from setuptools import setup

setup(name='wlanpi-fpms',
      version='1.0.4',
      description='Front Panel Menu System for the WLAN Pi',
      long_description='Front Panel Menu System for the WLAN Pi',
      author='Jiri Brejcha',
      packages=['wlanpi_fpms'],
      install_requires=[
            'luma',
            'gpiozero',
            'pillow'
      ],
      author_email='jirka@jiribrejcha.net',
      keywords="FPMS"
#      entry_points={
#          'console_scripts': ['wlanpi-fpms = wlanpi-fpms:main']}
      )
