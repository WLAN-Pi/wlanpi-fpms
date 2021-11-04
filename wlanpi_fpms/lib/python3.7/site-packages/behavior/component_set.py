"""
    This behavior file contains the logic for a subset of commands. Logic specific to
    commands should be implamented in corresponding behavior files.
"""

from pathlib import Path
import click
import time
import pyke
import json
import sys
import os

class ComponentSetBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')
    self.json           = kwargs.get('json')
    self.component_set  = kwargs.get('component_set')
    self.format         = kwargs.get('format')
    self.filter         = kwargs.get('filter')
    self.page           = kwargs.get('page')
    self.pagesize       = kwargs.get('pagesize')
    self.add            = kwargs.get('add')
    self.rm             = kwargs.get('rm')
    self.absolute       = kwargs.get('absolute')
    self.current        = kwargs.get('current')
    self.name           = kwargs.get('name')
    self.icon_file      = kwargs.get('icon_file')
    self.url_ref        = kwargs.get('url_ref')

  def list(self):
    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize}

    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/component-sets?page={page}&pagesize={pagesize}&{filter}', {**data} ))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table(resp['payload']['data'], self.format)
    self.util.print_record_count(resp)

  def delete(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')
    versions = self.util.get_all_component_set_versions(component_set_id)
    if versions:
      raise click.ClickException(click.style("You cannont delete a component set with versions", fg='red'))

    resp = self.util.cli_request('DELETE',
        self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}', {'component_set_id': component_set_id}))

    if self.json:
      click.echo(json.dumps(resp))
      return

    pyke.Menu().print_menu([resp['payload']['data']], self.format)

  def create(self):
    if not self.icon_file:
      self.icon_file = self.util.resolve_default_icon_path()

    post_data = {
      'name': self.name,
      'urlRef': self.url_ref,
      'ephemeralKey': self.util.upload_ephemeral(self.icon_file, 'image/svg+xml')
    }

    resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/component-sets'), data=json.dumps(post_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table([resp['payload']['data']], self.format)

  def update(self):
    component_set = self.util.get_component_set(self.component_set)
    component_set_id = component_set.get('id')
    post_data = {}

    if not self.name and not self.icon_file:
      click.echo(click.style("You must provide either a new name or new icon to update the component set", fg='yellow'))
      return

    if self.name:
      post_data['name'] = self.name

    if self.icon_file:
      post_data['ephemeralKey'] = self.util.upload_ephemeral(self.icon_file, 'image/svg+xml')

    resp = self.util.cli_request('PUT',
      self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}', {'component_set_id': component_set_id}),
      data=json.dumps(post_data))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table([resp['payload']['data']], self.format)

  def share(self):
      component_set = self.util.get_component_set(self.component_set)
      component_set_id = component_set.get('id')

      if self.current:
        if self.json:
          resp = self.util.cli_request('GET',
            self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/access', {'component_set_id': component_set_id}))

          click.echo(resp)
          return
        else:
          resp = self.util.cli_request('GET',
            self.util.build_url('{authUri}/auth/v1/company/child-companies'))['payload']['data']

          recs = self.util.get_current_access_records('component-set', component_set_id)
          org_names = [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]
          click.echo(org_names)
          return

      resp = self.util.cli_request('GET',
          self.util.build_url('{authUri}/auth/v1/company/child-companies'))['payload']['data']

      handlers = {
          'sharedWith': lambda x: x.get('granteeId') if x is not None else '',
          'unsharedWith': lambda x: x.get('granteeId') if x is not None else ''
        }

      if self.absolute:
        absolute_ids = [self.util.get_company_id(x, resp) for x in self.absolute]
        data = {
            "id": component_set_id,
            "granteeCompanyIds": [x for x in absolute_ids]
          }

        access_resp = self.util.cli_request('PUT', self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/access',\
            {'component_set_id': component_set_id}), data=json.dumps(data))

        if self.json:
          click.echo(json.dumps(access_resp))
          return

        recs = self.util.get_current_access_records('component-set', component_set_id)
        access_resp['payload']['data']['resultingGrantees'] =\
            [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]

        self.util.print_table([access_resp['payload']['data']], self.format)
        return

      recs = self.util.get_current_access_records('component-set', component_set_id)
      sharees = [x.get('granteeCompanyId') for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]
      if self.add:
        add_ids = [self.util.get_company_id(x, resp) for x in self.add]
        sharees.extend(add_ids)

      if self.rm:
        rm_ids = [self.util.get_company_id(x, resp) for x in self.rm]
        sharees = [x for x in sharees if x not in rm_ids]

      data = {
        "id": component_set_id,
        "granteeCompanyIds": sharees
      }

      access_resp = self.util.cli_request('PUT',
          self.util.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/access', {'component_set_id': component_set_id}), data=json.dumps(data))

      if self.json:
        click.echo(json.dumps(access_resp))
        return

      recs = self.util.get_current_access_records('component-set', component_set_id)

      access_resp['payload']['data']['resultingGrantees'] =\
          [self.util.get_company_name(x.get('granteeCompanyId'), resp) for x in recs if x.get('granteeCompanyId') != int(self.util.ctx.get('orgId'))]

      self.util.print_table([access_resp['payload']['data']], self.format)
