"""
    These are the sub-commands for a top level object added to the CLI group in 'cli.py'.
    The commands and options are implemented here and the logic behind them resides in the corresponding behavior file.
"""

import behavior
import click
import pyke

@click.group(help='Commands related to developing, managing and publishing experiences.')
def project():
  pass

@click.command('init', help="Initializes the current directory as a lumavate project")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
def init(**kwargs):
  #behavior.ProjectBehavior(**kwargs).init()
  pass

@click.command('get-qr', help="Display the QR activation code in the terminal")
@click.option('--profile', '-p', help=pyke.helptxt.PROFILE, callback=pyke.select_profile, autocompletion=pyke.auth.get_profile_names)
def get_qr(**kwargs):
  #behavior.ProjectBehavior(**kwargs).display_qr()
  pass


project.add_command(init)
project.add_command(get_qr)
