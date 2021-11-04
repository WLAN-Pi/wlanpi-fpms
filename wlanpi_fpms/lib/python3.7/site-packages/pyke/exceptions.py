import click

class CliException(click.ClickException):
  def __init__(self, message, **kwargs):
    if 'fg' not in kwargs:
      kwargs['fg'] = 'red'

    click.ClickException.__init__(self, click.style(message, **kwargs))
