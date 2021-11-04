"""
    This behavior file contains the logic for a subset of commands. Logic specific to
    commands should be implamented in corresponding behavior files.
"""

from pathlib import Path
import requests
import click
import pyke
import time
import json
import sys
import os

class ComponentSetVersionBehavior:
  def __init__(self, **kwargs):
    self.util            = kwargs.get('profile')
    self.version         = kwargs.get('version')
    self.component_set   = kwargs.get('component_set')
    self.json            = kwargs.get('json')
    self.filter          = kwargs.get('filter')
    self.page            = kwargs.get('page')
    self.pagesize        = kwargs.get('pagesize')
    self.format          = kwargs.get('format')
    self.label           = kwargs.get('label')
    self.from_version    = kwargs.get('from_version')
    self.version_bump    = kwargs.get('version_bump')
    self.css_includes    = kwargs.get('css_includes')
    self.direct_includes = kwargs.get('direct_includes')

    self.component_set_file_path  = kwargs.get('component_set_file_path')

  def list(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')

    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize}

    titles = {
          'directIncludes': '# Inc',
          'directCssIncludes': '# Css Inc',
          'expand__experiences': '# Exp',
          'expand__components': '# Comp',
    }

    handlers = {
          'directIncludes': lambda x: str(len(x)),
          'directCssIncludes': lambda x: str(len(x)),
          'expand__experiences': lambda x: str(len(x)),
          'expand__components': lambda x: str(len(x))
    }

    resp = self.util.cli_request('GET',
        self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions?expand=experiences&page={page}&pagesize={pagesize}&{filter}',
        {'component_set_id': component_set_id, **data}))

    if not self.json:
      self.util.print_table(resp['payload']['data'], self.format, titles=titles, handlers=handlers)
      self.util.print_record_count(resp)
    else:
      click.echo(json.dumps(resp))

  def list_components(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')

    version = self.util.get_component_set_version(component_set_id, self.version)
    version_id = version.get('id')

    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}?expand=components',\
      {'component_set_id': component_set_id, 'version_id': version_id}))

    comps = resp.get('payload', {}).get('data', {}).get('expand')
    click.echo(json.dumps(comps))

  def create(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')

    if self.from_version:
      version_data = self.util.get_component_set_version(component_set_id, self.from_version)

      if self.version:
        major, minor, patch = self.util.parse_version_number(self.version)

        version_data['major'] = major
        version_data['minor'] = minor
        version_data['patch'] = patch
      else:
        if self.version_bump == 'patch':
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions?major={major}&minor={minor}&sort=patch+desc',\
              { 'component_set_id': version_data['componentSetId'], 'major': version_data['major'], 'minor': version_data['minor'] }))['payload']['data']
        elif self.version_bump == 'minor':
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions?major={major}&sort=minor+desc',\
              { 'component_set_id': version_data['componentSetId'], 'major': version_data['major'] }))['payload']['data']
        else:
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions?sort=major+desc',\
              { 'component_set_id': version_data['componentSetId'] }))['payload']['data']

        if versions:
          latest_version = versions[0]

        version_data[self.version_bump] = latest_version[self.version_bump] + 1
        if self.version_bump in ['major', 'minor']:
          version_data['patch'] = 0
        if self.version_bump == 'major':
          version_data['minor'] = 0

    else:
      version_data = {}
      if not self.label:
        self.label = click.prompt(click.style("Label", fg="white"), type=click.Choice(['prod', 'dev', 'old']))

      if not self.version:
        self.version = click.prompt(click.style("Version Number", fg="white"), type=str)

    if self.version:
      major, minor, patch = self.util.parse_version_number(self.version)

      version_data['major'] = major
      version_data['minor'] = minor
      version_data['patch'] = patch

    if not self.json:
      click.echo('Image Size: {}'.format(self.util.get_size(self.component_set_file_path, image=False)))
      click.echo("Uploading Component Set Version to Lumavate")

    version_data['ephemeralKey'] = self.util.upload_ephemeral(self.component_set_file_path, 'application/zip')

    if self.label:
      version_data['label'] = self.label

    if self.css_includes:
      if 'directCssIncludes' not in version_data.keys():
        version_data['directCssIncludes'] = [x for x in self.css_includes]
      else:
        version_data['directCssIncludes'].extend([x for x in self.css_includes])

    if self.direct_includes:
      if 'directIncludes' not in version_data.keys():
        version_data['directIncludes'] = [x for x in self.direct_includes]
      else:
        version_data['directIncludes'].extend([x for x in self.direct_includes])

    resp = self.util.cli_request('POST',
        self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions',
        {'component_set_id': component_set_id}), data=json.dumps(version_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    handlers = {
      'directIncludes': lambda x: str(len(x)),
      'directCssIncludes': lambda x: str(len(x))
    }

    self.util.print_table([resp['payload']['data']], self.format, handlers=handlers)

  def update(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')

    version = self.util.get_component_set_version(component_set_id, self.version)
    version_id = version.get('id')

    post_data = {
      'componentSetId': component_set_id,
      'id': version_id,
      'label': self.label
    }

    resp = self.util.cli_request('PUT',
      self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}',
      {'component_set_id': component_set_id, 'version_id': version_id}), data=json.dumps(post_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    handlers = {
      'directIncludes': lambda x: str(len(x)),
      'directCssIncludes': lambda x: str(len(x))
    }

    self.util.print_table([resp['payload']['data']], self.format, handlers=handlers)

  def delete(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')

    if not self.version:
      self.version = click.prompt(click.style("Version: ", fg="white"), type=str)

    if "*" in self.version:
      versions = self.util.get_versions_from_mask('component-set', component_set_id, self.version)
      if self.json:
        resp_list = {}
        resp_list['responses'] = []
        for v in versions:
          resp = self.util.cli_request('DELETE',
                self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}', {'component_set_id': component_set_id, 'version_id': v['id']}))
          resp_list['responses'].append(resp)

        click.echo(json.dumps(resp_list))
        return

      with click.progressbar(versions, label='Deleting Versions') as bar:
        for v in bar:
          resp = self.util.cli_request('DELETE',
              self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}', {'component_set_id': component_set_id, 'version_id': v['id']}))

      handlers = {
          'directIncludes': lambda x: str(len(x)),
          'directCssIncludes': lambda x: str(len(x))
      }

      self.util.print_table(versions, self.format, handlers=handlers)

    else:
      version = self.util.get_component_set_version(component_set_id, self.version)
      version_id = version.get('id')

      resp = self.util.cli_request('DELETE',
          self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}',
          {'component_set_id': component_set_id, 'version_id': version_id}))

      if self.json:
        click.echo(json.dumps(resp))
        return

      handlers = {
        'directIncludes': lambda x: str(len(x)),
        'directCssIncludes': lambda x: str(len(x))
      }

      self.util.print_table([resp['payload']['data']], self.format, handlers=handlers)
