from datetime import datetime
from pathlib import Path
import subprocess
import platform
import requests
import click
import pyke
import json
import os

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
else:
  verify_tls = None

class ContainerVersionBehavior:
  def __init__(self, **kwargs):
    self.util           = kwargs.get('profile')

    self.click_ctx      = click.get_current_context()
    parent_command      = self.click_ctx.parent.command.name
    self.container_type = parent_command.replace('-version', '')

    self.container           = kwargs.get('container')
    self.port                = kwargs.get('port')
    self.editor_port         = kwargs.get('editor_port')
    self.is_editable         = kwargs.get('is_editable')
    self.container_file_path = kwargs.get('container_file_path')
    self.docker_image        = kwargs.get('docker_image')
    self.from_version        = kwargs.get('from_version')
    self.version             = kwargs.get('version')
    self.version_bump        = kwargs.get('version_bump')
    self.env                 = kwargs.get('env', {})
    self.label               = kwargs.get('label')
    self.format              = kwargs.get('format')
    self.json                = kwargs.get('json')
    self.path                = kwargs.get('path')
    self.tail_number         = kwargs.get('tail_number')
    self.filter              = kwargs.get('filter')
    self.page                = kwargs.get('page')
    self.pagesize            = kwargs.get('pagesize')

  def echo(self, msg, color='white'):
    if self.json:
      return
    click.echo(click.style(str(msg), fg=color))

  def raise_exc(self, msg, color='red'):
    raise click.ClickException(click.style(msg, fg=color))

  def list(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')
    data = {'filter': self.filter, 'page': self.page, 'pagesize': self.pagesize}

    handlers = {
      'actualState': lambda x: click.style(x, fg='red') if x not in ['running'] else click.style(x, fg='green')
    }

    resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions?page={page}&pagesize={pagesize}&{filter}',
      {'container_id': container_id, **data}))

    if self.json:
      click.echo(json.dumps(resp))
      return

    pyke.Menu().print_menu(resp['payload']['data'], self.format, handlers=handlers)
    self.util.print_record_count(resp)

  def start_stop(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    version_data = self.util.get_container_version(container_id, self.version)
    version_id = version_data.get('id')
    current_state = version_data.get('actualState')

    if current_state not in ['stopped', 'running', 'error']:
      self.raise_exec(f"To start or stop a version it must have a 'stopped', 'running' or 'error' state. The current state of this version is {current_state}. \
        A version goes through several states after being uploaded to Lumavate. It must finish this process before this command can be run. \
        To check its current state, run 'luma container-version ls'.", color='yellow')

    action = self.click_ctx.command.name
    if action == 'stop' and current_state != 'running':
      self.raise_exc("This version is not running", color='yellow')
    if action == 'start' and current_state == 'running':
      self.raise_exc("This version is already running", color='yellow')

    titles = {
        'id': 'id',
        'actualState': 'Current State',
        'versionNumber': 'Version #',
        'createdAt': 'Created At',
        'createdBy': 'Created By'
      }

    data = {
        "action": action,
        "containerId": container_id,
        "id": version_id
      }

    resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/{action}',\
      {'container_id': container_id, 'version_id': version_id, 'action': action}), data=data)

    if self.json:
      click.echo(json.dumps(resp))
      return

    status_id = resp.get('payload', {}).get('data', {}).get('results', {}).get('statusId', {})
    if not status_id:
      return resp

    if action == 'start':
      action_label = 'Starting'
    else:
      action_label = 'Stopping'

    status_resp = self.util.show_progress(status_id, label=f'{action_label} Container')

    error_msg = status_resp.get('payload', {}).get('data', {}).get('errorMessage')
    if error_msg is not None:
      self.raise_exc(f'{action_label} failed: {error_msg}')

    click.echo(' ')
    ver_resp = self.util.cli_request('GET',
      self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}', {'container_id': container_id, 'version_id': version_id}))

    handlers = {
      'actualState': lambda x: click.style(x, fg='red') if x not in ['running'] else click.style(x, fg='green')
    }

    self.util.print_table([ver_resp['payload']['data']], self.format, handlers=handlers, titles=titles)

  def run(self, command):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')
    version_data = self.util.get_container_version(container_id, self.version)
    version_id = version_data.get('id')

    resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/exec',\
      {'container_id': container_id, 'version_id': version_id}), json={"command": command})

    if self.json:
      click.echo(json.dumps(resp))
      return

    status_id = resp.get('payload', {}).get('data', {}).get('statusId', {})
    if not status_id:
      return resp

    status_resp = self.util.show_progress(status_id, label=f'Executing "{command}""')

    error_msg = status_resp.get('payload', {}).get('data', {}).get('errorMessage')
    if error_msg is not None:
      self.raise_exc(f'Command failed: {error_msg}')

    click.echo(' ')
    click.echo('Command Output: ')
    click.echo(' ')
    output = status_resp.get('payload', {}).get('data', {}).get('summary', {}).get('output', {})
    if output:
      for x in output:
        click.echo(x)
    else:
      click.echo(status_resp.get('payload', {}).get('data', {}))

  def update(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')
    version_data = self.util.get_container_version(container_id, self.version)
    version_id = version_data.get('id')

    post_data = {
      'containerId': container_id,
      'id': version_id,
      'label': self.label
      }

    resp = self.util.cli_request('PUT',\
      self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}',
      {'container_id': container_id, 'version_id': version_id}), json=post_data)

    if self.json:
      click.echo(json.dumps(resp))
      return

    self.util.print_table([resp['payload']['data']], self.format)

  def delete(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    if not self.version:
      self.version = click.prompt(click.style("Version: ", fg="white"), type=str)

    if "*" in self.version:
      versions = self.util.get_versions_from_mask('container', container_id, self.version)
      if self.json:
        resp_list = {}
        resp_list['responses'] = []
        for v in versions:
          resp = self.util.cli_request('DELETE',
              self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}', {'container_id': container_id, 'version_id': v['id']}))
          resp_list['responses'].append(resp)

        click.echo(json.dumps(resp_list))
        return

      with click.progressbar(versions, label='Deleting Versions') as bar:
        for v in bar:
          resp = self.util.cli_request('DELETE',
              self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}', {'container_id': container_id, 'version_id': v['id']}))

      self.util.print_table(versions, self.format)
    else:
      version = self.util.get_container_version(container_id, self.version)
      version_id = version.get('id')

      resp = self.util.cli_request('DELETE',
          self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}',
          {'container_id': container_id, 'version_id': version_id}))

      if self.json:
        click.echo(json.dumps(resp))
        return

      self.util.print_table([resp['payload']['data']], self.format)

  def docker_image_path(self, image_name):
    self.echo("Getting docker image:")
    cu = pyke.ContainerUtil()

    return cu.save_image(image_name)

  def resolve_env(self, version):
    if self.env:
      env = {var.split("=", 1)[0]: var.split("=", 1)[1] for var in self.env}
      return env

    return {}

  def create_version_data(self, container_id):
    if not self.from_version:
      version = {}

      # Set label
      if not self.label:
        if self.is_editable:
          label = 'dev'
        else:
          label = input("Label: ")
          if label is None or label == '':
            self.raise_exc("If you don't create from an old version then you must provide a --label")

        version['label'] = label
      else:
        version['label'] = self.label

      # Set version number
      if self.version:
        major, minor, patch = self.util.parse_version_number(self.version)

        version['major'] = major
        version['minor'] = minor
        version['patch'] = patch

      else:
        version_number = input("Version Number: ")

        if not version:
          self.raise_exc("If you don't create from an old version then you must provide a --version-number in the format\
              '<major: int>.<minor: int>.<patch: int>'")

        major, minor, patch = self.util.parse_version_number(version_number)

        version['major'] = major
        version['minor'] = minor
        version['patch'] = patch

      # Set port
      if not self.port:
        port = int(input("Port: "))
        if not port:
          self.raise_exc("If you don't create from an old version then you must provide a --port for your new version")
        version['port'] = port
      else:
        version['port'] = self.port

      return version

    else:
      version = self.util.get_container_version(container_id, self.from_version)
      from_version_id = version.get('id')

      if self.version:
        major, minor, patch = self.util.parse_version_number(self.version)

        version['major'] = major
        version['minor'] = minor
        version['patch'] = patch

        return version

      else:
        if self.version_bump == 'patch':
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions?major={major}&minor={minor}&sort=patch+desc',\
            { 'container_id': version['containerId'], 'major': version['major'], 'minor': version['minor'] }))['payload']['data']
        elif self.version_bump == 'minor':
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions?major={major}&sort=minor+desc',\
            { 'container_id': version['containerId'], 'major': version['major'] }))['payload']['data']
        else:
          versions = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions?sort=major+desc',\
            { 'container_id': version['containerId'] }))['payload']['data']

        if versions is not None and len(versions) > 0:
          latest_version = versions[0]

        version[self.version_bump] = latest_version[self.version_bump] + 1
        if self.version_bump in ['major', 'minor']:
          version['patch'] = 0
        if self.version_bump == 'major':
          version['minor'] = 0

        return version

  def create(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    if self.docker_image:
      container_file_path = self.docker_image_path(self.docker_image)
    else:
      container_file_path = self.container_file_path

    if not container_file_path and not self.from_version:
      image_name = input("Name of Docker Image: ")
      if not image_name:
        self.raise_exc("If you don't create from an old version then you must provide --container-file-path or --docker-image")

      container_file_path = self.docker_image_path(image_name)

    version = self.create_version_data(container_id)
    # Get version data

    if container_file_path:
      self.echo("Uploading image to Lumavate: ")
      self.echo('Image Size: {}'.format(self.util.get_size(container_file_path)))

      version['ephemeralKey'] = self.util.upload_ephemeral(container_file_path, 'application/gz')

    version['platformVersion'] = 'v2'
    if 'env' not in version.keys():
      version['env'] = {}

    version['env'] = {**version['env'], **self.resolve_env(version)}

    if self.label:
      version['label'] = self.label

    if self.port:
      version['port'] = self.port

    if self.is_editable:
      version['isEditable'] = True
      version['label'] = 'dev'
      version['editorPort'] = 5001

    if self.editor_port:
      version['editorPort'] = self.editor_port

    version['instanceCount'] = 1

    resp = self.upload_version_json(version, container_id)

    if self.json:
      if self.docker_image:
        try:
          os.remove(container_file_path)
        except:
          self.echo('Failed to delete zipped docker image...')

      click.echo(resp)
      return

    handlers = {
      'actualState': lambda x: click.style(x, fg='red') if x not in ['running'] else click.style(x, fg='green')
      }

    self.util.print_table([resp['payload']['data']], self.format, handlers=handlers)

    if self.docker_image:
      try:
        os.remove(container_file_path)
      except:
        self.echo('Failed to delete zipped docker image...')

  def upload_version_json(self, version_data, container_id):
    resp = self.util.cli_request('POST', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions',\
        {'container_id': container_id}), data=json.dumps(version_data))

    if self.json:
      return json.dumps(resp)

    # TO DO: Add progress bar after create for loading/validating container
    status_id = resp.get('payload', {}).get('data', {}).get('results', {}).get('statusId', {})
    if not status_id:
      return resp

    status_resp = self.util.show_progress(status_id, label='Uploading Container')

    error_msg = status_resp.get('payload', {}).get('data', {}).get('errorMessage')
    if error_msg is not None:
      self.raise_exc('Upload failed. {}'.format(error_msg))

    return resp

  def force_update(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    version = self.util.get_container_version(container_id, self.version)
    version_id = version.get('id')

    req_data = {'force': True}
    resp = self.util.cli_request('PUT',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}',
        {'container_id': container_id, 'version_id': version_id}), json=req_data)

    click.echo(resp)

  def download_app_zip(self):
    home = str(Path.home())
    if self.path is None:
      path = home
    else:
      path = f'{home}/{self.path}'

    for char in str(path):
      if char.isspace():
        raise click.ClickException(click.style(f"Your path cannont have a space in it - {path}", fg='red'))

    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    try:
      container = self.util.cli_request('GET',
          self.util.build_url('{experienceCloudUri}/iot/v1/containers?id={id}', {'id': container_id} ))['payload']['data']
    except:
      raise click.ClickException('Container not found')

    url_ref = container[0].get('urlRef')
    version = self.util.get_container_version(container_id, self.version)
    version_id = version.get('id')

    resp = self.util.cli_request('POST',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/token',
          {'container_id': container_id, 'version_id': version_id}), json={'type': 'editor'})

    token = resp.get('payload', {}).get('data', {}).get('token')
    service_url = self.util.ctx.get('experienceCloudUri')

    # TODO: Dynamically get integration cloud
    editor_url = f'{service_url}/ic/{url_ref}/luma-editor/download/application.zip'

    time = datetime.now().microsecond

    if platform.system() == 'Windows':
      zip_path = f'{path}\\application.{time}.zip'
    else:
      zip_path = f'{path}/application.{time}.zip'

    command_list = f"curl -L -f --create-dirs --output {zip_path} {editor_url} -H ".split()
    command_list.append(f'Authorization: Bearer {token}')
    if verify_tls is False:
      command_list.extend(['--insecure', '--proxy-insecure'])

    subprocess.run(command_list)
    click.echo(f'File Location: {zip_path}')


  def editor_info(self):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    version = self.util.get_container_version(container_id, self.version)
    version_id = version.get('id')
    url_ref = container.get('urlRef')
    editorPort = version.get('editorPort')

    if not editorPort:
      return self.old_logs(container_id, version_id, self.tail_number)

    resp = self.util.cli_request('POST',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/token',
          {'container_id': container_id, 'version_id': version_id}), json={'type': 'editor'})

    token = resp.get('payload', {}).get('data', {}).get('token')
    service_url = self.util.ctx.get('experienceCloudUri')

    headers = {'Authorization': f'Bearer {token}'}
    editor_url = f'{service_url}/ic/{url_ref}/luma-editor/version'

    req = requests.get(editor_url, headers=headers)
    click.echo(req.text)

  def tail_logs(self, editor):
    container = self.util.get_container(self.container, self.container_type)
    container_id = container.get('id')

    version = self.util.get_container_version(container_id, self.version)
    version_id = version.get('id')
    url_ref = container.get('urlRef')
    editorPort = version.get('editorPort')

    if not editorPort:
      return self.old_logs(container_id, version_id, self.tail_number)

    resp = self.util.cli_request('POST',
        self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/token',
          {'container_id': container_id, 'version_id': version_id}), json={'type': 'editor'})

    token = resp.get('payload', {}).get('data', {}).get('token')
    service_url = self.util.ctx.get('experienceCloudUri')

    if not self.tail_number:
      self.tail_number = 100

    # TODO: Dynamically get integration cloud
    editor_url = f'{service_url}/ic/{url_ref}/luma-editor/logs?tail={self.tail_number}'

    if editor:
      editor_url = f'{service_url}/ic/{url_ref}/luma-editor/logs?tail={self.tail_number}&editor=True'

    command_list = f'curl {editor_url} -H '.split()
    command_list.append(f'Authorization: Bearer {token}')
    if verify_tls is False:
      command_list.extend(['--insecure', '--proxy-insecure'])

    subprocess.run(command_list)

  def old_logs(self, container_id, version_id, tail_number):
    resp = self.util.cli_request('GET', self.util.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}/logs',\
      {'container_id': container_id, 'version_id': version_id}))

    logs = resp['payload']['data']
    if tail_number:
      tail = int(f'-{tail_number}')
      for x in logs[tail:]:
        click.echo(x)
    else:
      for x in logs:
        click.echo(x)
