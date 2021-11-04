from datetime import datetime
from pathlib import Path
import subprocess
import platform
import click
import pyke
import json
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
else:
  verify_tls = None

class ContainerBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')

    click_ctx           = click.get_current_context()
    parent_command      = click_ctx.parent.command.name
    self.container_type = parent_command

    self.format         = kwargs.get('format')
    self.json           = kwargs.get('json')
    self.container      = kwargs.get('container')
    self.name           = kwargs.get('name')
    self.url_ref        = kwargs.get('url_ref')
    self.icon_file      = kwargs.get('icon_file')
    self.add            = kwargs.get('add')
    self.rm             = kwargs.get('rm')
    self.absolute       = kwargs.get('absolute')
    self.current        = kwargs.get('current')
    self.filter         = kwargs.get('filter')
    self.page           = kwargs.get('page')
    self.pagesize       = kwargs.get('pagesize')
    self.asset_type     = kwargs.get('asset_type')

  def list(self):
    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize, 'container_type': self.container_type}

    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/containers?type={container_type}&page={page}&pagesize={pagesize}&{filter}', {**data} ))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table(resp['payload']['data'], self.format)
    self.util.print_record_count(resp)

  def create(self):
    # Replace with os.walk()
    if not self.icon_file:
      self.icon_file = self.util.resolve_default_icon_path()

    post_data = {
      'name': self.name,
      'urlRef': self.url_ref,
      'type': self.container_type,
      'ephemeralKey': self.util.upload_ephemeral(self.icon_file, 'image/svg+xml'),
      'publisherName': self.util.ctx['orgName'],
      'assetType': None
    }

    if self.container_type == 'asset':
      post_data['assetType'] = self.asset_type

    resp = self.util.cli_request('POST',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers'), data=json.dumps(post_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    pyke.Menu().print_menu([resp['payload']['data']], self.format)

  def delete(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    versions = self.util.get_all_container_versions(container_id)
    if versions:
      raise click.ClickException(click.style("You cannont delete a container with versions", fg='red'))

    resp = self.util.cli_request('DELETE',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}', {'container_id': container_id}))

    if self.json:
      click.echo(json.dumps(resp))
      return

    pyke.Menu().print_menu([resp['payload']['data']], self.format)

  def update(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')
    post_data = {}

    if not self.name and not self.icon_file:
      click.echo(click.style("You must provide either a new name or new icon to update the container", fg='yellow'))
      return

    if self.name:
      post_data['name'] = self.name

    if self.icon_file:
      post_data['ephemeralKey'] = self.util.upload_ephemeral(self.icon_file, 'image/svg+xml')

    resp = self.util.cli_request('PUT',
      self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}', {'container_id': container_id}),
      data=json.dumps(post_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table([resp['payload']['data']], self.format)

  def share(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    if self.current:
      if self.json:
        resp = self.util.cli_request('GET',
          self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/access', {'container_id': container_id}))

        click.echo(resp)
        return
      else:
        resp = self.util.cli_request('GET',
          self.util.build_url('{app}/auth/v1/company/child-companies'))['payload']['data']

        recs = self.util.get_current_access_records('container', container_id)
        org_names = [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]
        click.echo(org_names)
        return

    resp = self.util.cli_request('GET',
        self.util.build_url('{app}/auth/v1/company/child-companies'))['payload']['data']

    handlers = {
        'sharedWith': lambda x: x.get('granteeId') if x is not None else '',
        'unsharedWith': lambda x: x.get('granteeId') if x is not None else ''
      }

    if self.absolute:
      absolute_ids = [self.util.get_company_id(x, resp) for x in self.absolute]
      data = {
          "id": container_id,
          "granteeCompanyIds": [x for x in absolute_ids]
        }

      access_resp = self.util.cli_request('PUT', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/access',\
          {'container_id': container_id}), data=json.dumps(data))

      if self.json:
        click.echo(json.dumps(access_resp))
        return

      recs = self.util.get_current_access_records('container', container_id)
      access_resp['payload']['data']['resultingGrantees'] =\
          [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]

      self.util.print_table([access_resp['payload']['data']], self.format)
      return

    recs = self.util.get_current_access_records('container', container_id)
    sharees = [x.get('granteeCompanyId') for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]
    if self.add:
      add_ids = [self.util.get_company_id(x, resp) for x in self.add]
      sharees.extend(add_ids)

    if self.rm:
      rm_ids = [self.util.get_company_id(x, resp) for x in self.rm]
      sharees = [x for x in sharees if x not in rm_ids]

    data = {
      "id": container_id,
      "granteeCompanyIds": sharees
    }

    access_resp = self.util.cli_request('PUT',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/access', {'container_id': container_id}), data=json.dumps(data))

    if self.json:
      click.echo(json.dumps(access_resp))
      return

    recs = self.util.get_current_access_records('container', container_id)

    access_resp['payload']['data']['resultingGrantees'] =\
        [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]

    self.util.print_table([access_resp['payload']['data']], self.format)
