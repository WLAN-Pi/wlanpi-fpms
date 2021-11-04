"""
    This behavior file contains the logic for a subset of commands. Logic specific to
    commands should be implamented in corresponding behavior files.
"""

import requests
import urllib3
import click
import pyke
import json
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
else:
  verify_tls = None

class ExperienceBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')
    self.json           = kwargs.get('json', False)
    self.name           = kwargs.get('name')
    self.format         = kwargs.get('format')
    self.filter         = kwargs.get('filter')
    self.page           = kwargs.get('page')
    self.pagesize       = kwargs.get('pagesize')
    self.device_type    = kwargs.get('device_type')
    self.collection     = kwargs.get('collection')

    self.import_file = None
    # Expand the filename and get the absolute path. Relative paths won't resolve if entered via prompt
    filename = kwargs.get('import_file')
    if filename:
      try:
        self.import_file = os.path.abspath(os.path.expanduser(filename))
      except:
        raise pyke.CliException('Invalid value for --import-file')

    self.export_file = None
    filename = kwargs.get('export_file')
    if filename:
      try:
        self.export_file = os.path.abspath(os.path.expanduser(filename))
      except:
        raise pyke.CliException('Invalid value for --export-file')

    self.type = kwargs.get('type')
    self.redirect_url = kwargs.get('redirect_url')
    self.description = kwargs.get('description')
    self.label = kwargs.get('label')
    self.activation_code = kwargs.get('activation_code')
    self.is_template = kwargs.get('template', False)

    if self.type is None:
      self.type = 'template' if self.is_template else 'standard'

  def list(self):
    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize}

    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/experiences?page={page}&pagesize={pagesize}&{filter}', {**data} ))

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table(resp.get('payload', {}).get('data', {}), self.format)
    self.util.print_record_count(resp)

  def export(self):
    if not self.json and not self.export_file:
      try:
        self.export_file = input('Export file: ')
        if self.export_file is None or self.export_file == '':
          raise pyke.CliException('Must provide --export-file')

        self.export_file = os.path.abspath(os.path.expanduser(self.export_file))
      except:
        raise pyke.CliException('Invalid value for --export-file')


    if self.name and self.label:
      raise pyke.CliException('Must provide either --label or --name; not both')

    # Determine if we have to lookup the namespace
    if not self.name:
      if not self.label:
        self.label = input('Label: ')
        if self.label is None or self.label == '':
          raise pyke.CliException('Must provide --name or --label of the experience to export')

      experience_resp = self.util.cli_request('GET',
        self.util.build_url('{experienceCloudUri}/iot/v1/experiences?{filter}', {'filter': 'label={}'.format(self.label)} ))

      experience_data = experience_resp.get('payload', {}).get('data')
      if len(experience_data) == 0:
        raise pyke.CliException('Experience label "{}" not found'.format(self.label))

      if len(experience_data) > 1:
        raise pyke.CliException('More than one experience was found with the label "{}"'.format(self.label))

      self.name = experience_data[0].get('name')

    export_resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/experiences/{name}/export', {'name': self.name}))
    if self.json:
      click.echo(json.dumps(export_resp))
      return

    status_id = export_resp.get('payload', {}).get('data', {}).get('statusId', {})
    status_resp = self.util.show_progress(status_id, label='Exporting experience')

    error_msg = status_resp.get('payload', {}).get('data', {}).get('errorMessage')
    if error_msg is not None:
      raise pyke.CliException('Export failed. {}'.format(error_msg))

    click.echo(' ')

    file_url = status_resp.get('payload', {}).get('data', {}).get('summary', {}).get('fileInfo', {}).get('signedUrl')
    file_resp = requests.get(file_url, verify=verify_tls)
    with open(self.export_file, 'wb') as f:
      f.write(file_resp.content)

    click.echo('Saved to {}'.format(self.export_file))

  def import_(self):
    if not self.util.ctx.get('instanceType'):
      raise click.ClickException(click.style("This profile looks old. Run 'luma profile refresh-token' to migrate this profile to the new format.", fg='red'))
    if self.util.ctx.get('instanceType') == 'cc':
      raise click.ClickException(click.style("This command must be run with a studio profile", fg='red'))

    if self.collection:
      collection = self.util.get_collection(self.collection)
    else:
      titles =  titles={'name': 'Name', 'id': 'Collection ID'}
      collection = pyke.Menu().get_user_select(self.util.get_all_collections(),'{name} {id}', titles=titles)

    collection_id = collection.get('id')

    if not self.json:
      click.echo('Uploading file...')

    # Request ephemeral token
    token_resp = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/files/ephemeral?contentType=application/json'))
    token_data = token_resp.get('payload', {}).get('data', {})
    token_fields = token_data.get('fields')

    aws_access_key_id = token_fields.get('AWSAccessKeyId')
    ephemeral_key = token_fields.get('key').replace('${filename}', 'import.json')
    policy = token_fields.get('policy')
    signature = token_fields.get('signature')
    url = token_data.get('url')

    # Post to ephemral URL
    data = {
      'AWSAccessKeyId': aws_access_key_id,
      'key': ephemeral_key,
      'policy': policy,
      'signature': signature,
      'Content-Type': 'application/json'
    }

    aws_resp = None
    with open(self.import_file, 'rb') as f:
      aws_resp = requests.post(url, data=data, files={'file': f}, verify=verify_tls)

    if not self.json:
      click.echo('File uploaded.')
      click.echo('')

    # Post to import
    import_json = {
      'name':'',
      'description': self.description,
      'type': self.type,
      'experienceCollectionId': collection_id,
      'label': self.label,
      'redirectUrl': self.redirect_url,
      'code': self.activation_code,
      'ephemeralKey': ephemeral_key,
      'device': self.device_type
    }

    import_resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/experiences/import'), json=import_json)
    if self.json:
      click.echo(json.dumps(import_resp))
      return

    status_id = import_resp.get('payload', {}).get('data', {}).get('statusId', {})
    status_resp = self.util.show_progress(status_id, label='Importing experience')

    error_msg = status_resp.get('payload', {}).get('data', {}).get('errorMessage')
    if error_msg is not None:
      raise pyke.CliException('Import failed. {}'.format(error_msg))

    click.echo('Successfully imported experience.')

  def create(self):
    if not self.util.ctx.get('instanceType'):
      raise click.ClickException(click.style("This profile looks old. Run 'luma profile refresh-token' to migrate this profile to the new format.", fg='red'))
    if self.util.ctx.get('instanceType') == 'cc':
      raise click.ClickException(click.style("This command must be run with a studio profile", fg='red'))

    xp_data = {}
    xp_data['label'] = self.name
    xp_data['code'] = self.activation_code
    xp_data['description'] = self.description
    xp_data['device'] = self.device_type
    xp_data['type'] = self.type
    if self.redirect_url:
      xp_data['redirectUrl'] = self.redirect_url

    if self.collection:
      collection = self.util.get_collection(self.collection)
      xp_data['experienceCollectionId'] = collection.get('id')
    else:
      titles =  titles={'name': 'Name', 'id': 'Collection ID'}
      collection = pyke.Menu().get_user_select(self.util.get_all_collections(),'{name} {id}', titles=titles)
      xp_data['experienceCollectionId'] = collection.get('id')

    resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/experiences'), json=xp_data)
    if self.json:
      click.echo(resp)
      return

    titles =  titles={'label': 'Label', 'name': 'Namespace', 'code': 'Code', 'device': 'Device'}
    pyke.Menu().print_menu([resp['payload']['data']], '{label} {name} {code} {device}', titles=titles)
