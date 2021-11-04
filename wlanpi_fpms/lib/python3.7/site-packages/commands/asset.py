"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import click

@click.group('asset', help='Assets are studio level features. You can share them with other orgs giving them access to use the associated versions.')
def asset():
    pass
