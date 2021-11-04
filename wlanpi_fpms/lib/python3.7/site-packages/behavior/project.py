"""
    This behavior file contains the logic for a subset of commands. Logic specific to
    commands should be implamented in corresponding behavior files.
"""

import pyqrcode as qrc
from cli import pyke
import requests
import urllib3
import click
import json
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
else:
  verify_tls = None

class ProjectBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')

  def read_config(self):
    pass

  def write_config(self):
    pass

  def init(self):
    ts = pyke.Tarsum()
    tarfile = ts.make_tarfile('mon_tar.tar', '/home/dev/Code/monitor')
    ts.gzip_file(tarfile)
    click.echo(ts.get_checksum(f'{os.getcwd()}/mon_tar.tar'))

  def display_qr(self):
    url = qrc.create('https://google.com')
    url.svg('qr-activation.svg', scale=8)
    click.echo(url.terminal(quiet_zone=2))
