"""
    This behavior file contains the logic for a subset of commands. Logic specific to
    commands should be implamented in corresponding behavior files.
"""

import click
import pyke
import json

class ExperienceCollectionBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')

    self.json           = kwargs.get('json')
    self.format         = kwargs.get('format')
    self.filter         = kwargs.get('filter')
    self.page           = kwargs.get('page')
    self.pagesize       = kwargs.get('pagesize')
    self.name           = kwargs.get('name')

  def list(self):
    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize}
    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/experience-collections?page={page}&pagesize={pagesize}&{filter}', {**data} ))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table(resp.get('payload', {}).get('data', {}), self.format)
    self.util.print_record_count(resp)


