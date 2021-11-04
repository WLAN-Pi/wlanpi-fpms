"""
    The Util class is comprised of common code that is used throughout the CLI.
    Refreshing tokens, making calls to the platform, building urls, and looking up
    various lumavate objects are few things implamented here.

    TO DO: This needs to be broken up further. Refreshing tokens and all other things
    auth should be broken out into the auth class. Request handling and the various validation
    of objects sprinkled in this code and the behavior files are two other major chunks of code
    that need a new home.
"""

from pyparsing import Literal, Word, nums, Combine, Optional,\
  delimitedList, oneOf, alphas, Suppress
from pathlib import Path
from time import sleep
import dateutil.parser
import functools
import requests
import platform
import urllib3
import urllib
import click
import pyke
import copy
import json
import sys
import re
import os


ESC = Literal('\x1b')
integer = Word(nums)
escapeSeq = Combine(ESC + '[' + Optional(delimitedList(integer,';')) +
                oneOf(list(alphas)))

uncolor = lambda s : Suppress(escapeSeq).transformString(s)

verify_tls = os.environ.get('LUMA_CLI_VERIFY_TLS', None)
if verify_tls == 'false' or verify_tls == 'False':
  verify_tls = False
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
else:
  verify_tls = None

def list_options(f):
  options = [
          click.option('--filter', default=''),
          click.option('--page', default=1),
          click.option('--pagesize', default=100),
          click.option('--json/--table', default=False, help='Return raw json from the platform.')
      ]
  return functools.reduce(lambda x, opt: opt(x), options, f)

class Util:
  def __init__(self, ctx=None, profile=None):
    if not ctx:
      self.ctx = self.get_ctx()
    else:
      self.ctx = ctx

    if not profile:
      self.profile = self.ctx.get('profileName')
    else:
      self.profile = profile

  def get_ctx(self):
    ctx = click.get_current_context()
    if not ctx:
      raise click.ClickException(click.style("Context has not yet been created for this command."))
    if ctx.obj:
      return ctx.obj
    return {}

  def login_token(self, renew=False):
    if renew:
      token = self.login()['access_token']
      self.ctx['accessToken'] = token
      self.get_ctx()['accessToken'] = token

      return token

    if self.ctx:
      return self.ctx.get('accessToken')

  def login_without_context(self, config_data=None):
    data = {
      'grant_type': 'client_credentials',
      'audience': self.ctx['audience'],
      'client_id': self.ctx['clientId'],
      'client_secret': self.ctx['clientSecret']
    }

    token_url = self.ctx.get('token')
    resp = self.cli_request('POST', f'https://{token_url}/oauth/token', json=data, external=True)

    if resp.status_code != 200:
      click.echo(json.dumps(self.ctx))
      click.echo(' ')

      raise click.ClickException(click.style("Env not configured correctly. Make sure your Client ID and Client Secret are correct.", fg='red'))

    return resp.json()['access_token']

  def login(self):
    data = {
      'grant_type': 'client_credentials',
      'audience': self.ctx['audience'].replace(" ", ""),
      'client_id': self.ctx['clientId'].replace(" ", ""),
      'client_secret': self.ctx['clientSecret'].replace(" ", "")
    }

    res = self.cli_request('POST', 'https://{}/oauth/token'.format(self.ctx['token']), json=data, external=True)
    if res.status_code != 200:
      raise click.ClickException(click.style("Env not configured correctly. Make sure your Client ID and Client Secret are correct.", fg='red'))

    resp = res.json()

    if self.ctx.get('orgId') is not None:
      url = '{}/auth/v1/session'.format(self.ctx.get('app'))
      data = {'companyId': self.ctx.get('orgId')}
      r = requests.post(url, json=data, headers={'Authorization': 'Bearer ' + resp['access_token']}, verify=verify_tls)
      if r.status_code != 200:
        raise click.BadParameter(click.style("Not authorized for company id {}".format(self.ctx.get('orgId')), fg='red'))
      access_token = resp.get('access_token')

      self.ctx['access_token'] = access_token
      pyke.auth.set_profile_token(self.ctx.get('profileName'), access_token)

      return resp

  def print_record_count(self, data):
    d = data['payload']
    if d['totalItems'] > d['currentItemCount']:
      d['startItem'] = (d['page'] - 1) * d['pageSize'] + 1
      d['endItem'] = d['startItem'] - 1 + d['currentItemCount']
      count_str = 'showing {startItem} - {endItem} of {totalItems} total items (page {page} / {totalPages})'
      click.echo(click.style(count_str.format(**d), fg='yellow'))

  def load_users(self):
    resp = self.cli_request('GET', self.build_url('{authUri}/auth/v1/users'))

    users = {}
    for u in resp['payload']['data']:
      users[u['id']] = u['emailAddress']

    return users

  def print_table(self, data, format, titles={}, handlers={}):
    headers = {}
    stats = {}
    users = {}

    if 'createdBy' in format or 'lastModifiedBy' in format:
      users = self.load_users()

    for c in data:
      child_records = {}
      for k in c:
        if isinstance(c[k], dict):
          for sk in c[k]:
            child_records[k + '__' + sk] = c[k][sk]

      c.update(child_records)

    if len(data) > 0:
      for k in data[0]:
        headers[k] = titles.get(k, k)
    else:
      click.echo('No Records Found')
      return

    for k in headers:
      stats[k] = len(uncolor(headers[k]))

    # TO DO: Cache users and reload when we can't find one
    for c in data:
      for k in c:
        if k in ['createdAt', 'lastModifiedAt']:
          cd = dateutil.parser.parse(c[k])
          c[k] = cd.strftime('%x %X')
        if k in ['createdBy', 'lastModifiedBy']:
          c[k] = users.get(c[k], 'Not Found ({})'.format(c[k]))
        if stats.get(k, 0) < len(str(uncolor(handlers[k](c[k])) if k in handlers else c[k])):
          stats[k] = len(str(uncolor(handlers[k](c[k])) if k in handlers else c[k]))

    for k in headers:
      headers[k] = titles.get(k, k).ljust(stats[k])

    for c in data:
      for k in c:
        c[k] = str(handlers[k](c[k]) if k in handlers else c[k])
        c[k] = c[k] + ' ' * (stats[k] - len(uncolor(c[k])))

    try:
      click.echo(click.style(format.format(**headers), fg='white'))
    except KeyError as ke:
      raise click.ClickException(click.style(f'You passed in a header that did not exsist in the response: {ke}', fg='red'))

    for c in data:
      click.echo(format.format(**c))

  def check_response(self, resp):
    if resp.status_code == 500:
      raise click.ClickException(str(click.style('Unhandled Exception: ', fg='red')) + str(resp.text))
    elif resp.status_code == 404:
      raise click.ClickException(click.style('Not Found', fg='red'))
    elif resp.status_code == 400:
      raise click.ClickException(click.style(resp.text, fg='red'))

    return resp

  def get_headers(self):
    return {
        'Authorization': 'Bearer ' + self.login_token(),
        'Content-Type': 'application/json'
      }

  def build_url(self, format, extra_data = {}):
    data = pyke.auth.sanatize_data(self.ctx)
    env = copy.deepcopy(data)
    env.update(self.ctx)
    env.update(extra_data)
    return format.format(**env).replace(" ", "+")

  def cli_request(self, method, url, data=None, json=None, headers=None, params=None, external=False):
    req_args = self.build_req_args(data, json, headers, params, external)
    req = self.get_request_func(method)
    url = url.replace(" ", "")
    if data is not None:
      resp = self.check_response(req(url, data=data, **req_args, verify=verify_tls))
    else:
      resp = self.check_response(req(url, **req_args, verify=verify_tls))

    bad_codes = [200, 500]
    if resp.status_code not in bad_codes and external is False:
      self.login_token(renew=True)
      req_args = self.build_req_args(data, json, headers, params, external)
      resp = self.check_response(req(url, **req_args, verify=verify_tls))
      print(f'RESP: {resp.__dict__}',flush=True)
      if resp.status_code != 200:
        raise click.BadParameter(click.style('Invalid Credentials', fg='red'))

    if not external:
      return resp.json()
    else:
      return resp

  def build_req_args(self, data, json_data, headers, params, external=False):
    if external is False:
      req_headers = self.get_headers()
      if headers is not None:
        req_headers.update(headers)
    elif headers is not None:
      req_headers = headers
    else:
      req_headers = None

    req_args = {}
    if json_data is not None:
      req_args['json'] = json_data
    if req_headers is not None:
      req_args['headers'] = req_headers
    if params is not None:
      req_args['params'] = params

    return req_args

  def get_request_func(self, method):
    method = method.lower()
    methods = {
      'get': requests.get,
      'head': requests.head,
      'post': requests.post,
      'put': requests.put,
      'patch': requests.patch,
      'delete': requests.delete
    }

    return methods[method]

  def get_companies(self):
    handlers = {
        'instanceType': lambda x: 'dev' if x == 'cc' else x,
    }

    headers = {
      'Authorization': 'Bearer ' + self.login_without_context(),
      'Content-Type': 'application/json'
    }

    app_url = self.ctx.get('app')
    res = requests.get(f'{app_url}/auth/v1/me/companies?sort=name', headers=headers, verify=verify_tls)
    resp = res.json()['payload']['data']

    return resp

  def get_company_id_from_resp(self, id, resp):
    try:
      company_id = next(int(rec.get('id')) for rec in resp if rec.get('name').lower() == id.lower())
      return company_id
    except:
      raise click.ClickException(click.style("Company not found. You can only share/unshare with companies you have provisioned.", fg='red'))

  def get_company_id(self, name_or_id, resp):
    try:
      company_id = int(name_or_id)
      return company_id
    except:
      return self.get_company_id_from_resp(name_or_id, resp)

  def get_company_name(self, id, resp):
    return next(rec.get('name') for rec in resp if int(rec.get('id')) == id)

  def upload_ephemeral(self, filename, content_type):
    resp = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/files/ephemeral?contentType=' + urllib.parse.quote(content_type)))
    if '/' in filename:
      file_name = filename.rsplit('/', 1)[-1]
    else:
      file_name = filename

    ephemeral_url = resp['payload']['data']['url']
    ephemeral_data = resp['payload']['data']['fields']
    ephemeral_data['key'] = ephemeral_data['key'].replace('${filename}', file_name)
    ephemeral_data['Content-Type'] = content_type

    requests.post(
      ephemeral_url,
      data=ephemeral_data,
      files={'file': open(filename, 'rb')},
      verify=verify_tls )

    return ephemeral_data['key']

  def get_current_access_records(self, object, object_id):
    path = '{}s/{}/access'.format(object, object_id)
    resp = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/' + path))
    return resp['payload']['data']

  def lookup_object_id(self, object_type, id, abort_if_null=True):
    if object_type == 'component-set':
      try:
        object_filter = int(id)
        filter_type = 'id'
      except:
        object_filter = id
        filter_type = 'urlRef'

      resp = self.cli_request('GET',
          self.build_url('{experienceCloudUri}/iot/v1/component-sets?{filter_type}={object_filter}',
          extra_data={'filter_type': filter_type, 'object_filter': object_filter}))

      if len(resp.get('payload').get('data', [])) > 0:
        return resp['payload']['data'][0]['id']

      if abort_if_null:
        click.echo(click.style('{} not found'.format(object_type), fg='red'))
        sys.exit()

    else:
      try:
        object_filter = int(id)
        filter_type = 'id'
      except:
        object_filter = id
        filter_type = 'urlRef'

      resp = self.cli_request('GET',
          self.build_url('{experienceCloudUri}/iot/v1/containers?{filter_type}={object_filter}',
          extra_data={'filter_type': filter_type, 'object_filter': object_filter}))

      if len(resp.get('payload').get('data', [])) > 0:
        return resp['payload']['data'][0]['id']

      if abort_if_null:
        click.echo(click.style('{} not found'.format(object_type), fg='red'))
        sys.exit()

  def save_config(self, data):
    with open(self.get_config_file(), 'w+') as outfile:
      json.dump(data, outfile, indent=4, sort_keys=True)

  def get_size(self, path, image=True):
    stats = os.stat(path)
    byte_size = stats.st_size
    if byte_size < 1048576:
      return '{} KB'.format(round(byte_size / 1024, 2))
    elif byte_size < 1073741824:
      return '{} MB'.format(round(byte_size / 1048576, 2))
    else:
      if image is True:
        click.echo('Hey! Thanks for being an awesome Lumavate customer.')
        click.echo('While you are waiting for this image to upload to the platform you should check this out!')
        click.echo('https://hackernoon.com/tips-to-reduce-docker-image-sizes-876095da3b34')
        return '{} GB'.format(round(byte_size / 1073741824, 2))

  def parse_version_number(self, version_number):
    try:
      major, minor, patch = version_number.split('.')
      for x in [major, minor, patch]:
        if x is None:
          raise click.ClickException(click.style("Version numbers must be in the format '<major: int>.<minor: int>.<patch: int>' ", fg='red'))
        if x != '*':
          if int(x) < 0:
            raise click.ClickException(click.style("Version numbers must be in the format '<major: int>.<minor: int>.<patch: int>' ", fg='red'))

      return major, minor, patch
    except:
      raise click.ClickException(click.style("Version numbers must be in the format '<major: int>.<minor: int>.<patch: int>' ", fg='red'))

  def get_config_file(self):
    config_path = str(Path.home()) + '/.luma_cli_config'
    if not os.path.exists(config_path):
      with open(config_path, 'w') as config:
        json.dump({ "envs": {}, "profiles": {} }, config)

    return config_path

  def get_version_id(self, object_type, parent_id, version):
    try:
      version_id = int(version)
    except:
      _version = self.get_version_from_version_number(object_type, parent_id, version)
      if _version is not None:
        version_id = _version.get('id')

    return version_id

  # TO DO:Create logic here to better target smaller page to find version
  def get_versions_from_mask(self, object_type, parent_id, version):
    if object_type == 'component-set':
      versions = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets/{parent_id}/versions?pagesize=500',\
          {'parent_id': parent_id}))['payload']['data']
    else:
      versions = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers/{parent_id}/versions?pagesize=500',\
          {'parent_id': parent_id}))['payload']['data']

    major, minor, patch = self.parse_version_number(version)

    return sorted([x for x in versions if
        (str(x['major']) == major or major == '*') and
        (str(x['minor']) == minor or minor == '*') and
        (str(x['patch']) == patch or patch == '*')], key=lambda x: (x['major'], x['minor'], x['patch']), reverse=True)

  def get_version_from_version_number(self, object_type, parent_id, version_number):
    if '*' in version_number:
      version = self.get_versions_from_mask(object_type, parent_id, version_number)

    else:
      major, minor, patch = self.parse_version_number(version_number)

      if object_type == 'component-set':
        version = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets/{parent_id}/versions?major={major}&minor={minor}&patch={patch}',\
            { 'parent_id': parent_id, 'major': major, 'minor': minor, 'patch': patch }))['payload']['data']
      else:
        version = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers/{parent_id}/versions?major={major}&minor={minor}&patch={patch}',\
            { 'parent_id': parent_id, 'major': major, 'minor': minor, 'patch': patch }))['payload']['data']

    if version is not None and len(version) > 0:
      return version[0]

    else:
      raise click.ClickException(click.style('Version Not Found', fg='red'))

  def get_component_set(self, component_set):
    try:
      component_set_id = int(component_set)
      return self.get_component_set_by_id(component_set_id)
    except:
      return self.get_component_set_by_url_ref(component_set)

  def get_component_set_by_id(self, component_set_id):
    component_set = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}',\
        {'component_set_id': component_set_id}))['payload']['data']

    if not component_set:
      raise click.ClickException(click.style('Component Set Not Found', fg='red'))
    return component_set

  def get_component_set_by_url_ref(self, url_ref):
    component_set_res = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets?urlRef={urlRef}', {'urlRef': url_ref}))
    component_set_list = component_set_res.get('payload', {}).get('data', {})

    if not component_set_list or len(component_set_list) < 1:
      raise click.ClickException(click.style('Component Set Not Found', fg='red'))

    return component_set_list[0]

  def get_component_set_version(self, component_set_id, version):
    try:
      version_id = int(version)
      return self.get_component_set_version_by_id(component_set_id, version_id)
    except:
      return self.get_version_from_version_number('component-set', component_set_id, version)

  def get_component_set_version_by_id(self, component_set_id, version_id):
    version = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions/{version_id}',\
        { 'component_set_id': component_set_id, 'version_id': version_id}))['payload']['data']

    return version

  def get_all_component_set_versions(self, component_set_id):
    versions = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/component-sets/{component_set_id}/versions',\
        {'component_set_id': component_set_id}))['payload']['data']

    return versions

  def get_all_collections(self):
    resp = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/experience-collections'))
    return resp['payload']['data']

  def get_collection(self, collection):
    try:
      collection_id = int(collection)
      resp = self.cli_request('GET',
          self.build_url('{experienceCloudUri}/iot/v1/experience-collections?id={id}', {'id': collection_id})).get('payload', {}).get('data')

      if not resp:
        raise click.ClickException(click.style('Collection Not Found', fg='red'))
      return resp[0]
    except:
      resp = self.cli_request('GET',
          self.build_url('{experienceCloudUri}/iot/v1/experience-collections?name={name}', {'name': collection})).get('payload', {}).get('data')

      if not resp:
        raise click.ClickException(click.style('Collection Not Found', fg='red'))
      return resp[0]

  def get_container(self, container, container_type):
    try:
      container_id = int(container)
      return self.get_container_by_id(container_id, container_type)
    except:
      return self.get_container_by_url_ref(container, container_type)

  def get_container_by_url_ref(self, url_ref, container_type):
    container_res = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers?urlRef={urlRef}&type={container_type}',\
        {'urlRef': url_ref, "container_type": container_type}))

    container_list = container_res.get('payload', {}).get('data', {})

    if not container_list or len(container_list) < 1:
      raise click.ClickException(click.style('Container Not Found', fg='red'))

    return container_list[0]

  def get_all_container_versions(self, container_id):
    versions = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions',\
        { 'container_id': container_id}))['payload']['data']

    return versions

  def get_container_version(self, container_id, version):
    try:
      version_id = int(version)
      return self.get_container_version_by_id(container_id, version_id)
    except:
      return self.get_version_from_version_number('container', container_id, version)

  def get_container_by_id(self, container_id, container_type):
    version = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}?type={container_type}',\
        { 'container_id': container_id, 'container_type': container_type}))['payload']['data']

    if version:
      if version.get('type') != container_type:
        raise click.ClickException(click.style('Container Not Found', fg='red'))

    return version

  def get_container_version_by_id(self, container_id, version_id):
    version = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/containers/{container_id}/versions/{version_id}',\
        { 'container_id': container_id, 'version_id': version_id}))['payload']['data']

    return version

  def get_version(self, object_type, parent_id, version):
    versions = self.get_versions_from_mask(object_type, parent_id, version)
    if versions:
      return versions[0]

    return None

  def resolve_default_icon_path(self):
    pwd = os.path.dirname(os.path.realpath(__file__))
    if platform.system() == 'Windows':
      return f'{sys.exec_prefix}\\images\\default-icon.svg'
    else:
      icon_path = pwd.rsplit('/', 1)[0]
      return f'{icon_path}/images/default-icon.svg'

  def show_progress(self, status_id, label=None):
    progress = 0
    error = None
    status_resp = None

    last_progress = 0
    with click.progressbar(length=100, label=label) as bar:
      while progress < 100 and error is None:
        sleep(3)
        status_resp = self.cli_request('GET', self.build_url('{experienceCloudUri}/iot/v1/statuses/{status_id}', {'status_id': status_id}))
        status_data = status_resp.get('payload', {}).get('data', {})
        progress = status_data.get('overallPercent')
        error = status_data.get('errorMessage')
        bar.update(progress - last_progress)
        last_progress = progress

    return status_resp
