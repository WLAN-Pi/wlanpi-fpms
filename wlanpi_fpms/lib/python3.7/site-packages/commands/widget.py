"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import click

@click.group(help='A widget is comprised of widget-versions. You can share widgets with other orgs giving them access to use the associated versions.')
def widget():
    pass