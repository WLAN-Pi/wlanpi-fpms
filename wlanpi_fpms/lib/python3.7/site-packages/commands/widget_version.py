"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import click

@click.group('widget-version', help="A widget-version is the docker image of widget, \
along with the details it needs to run such as, port number and Env variables.")
def widget_version():
  pass